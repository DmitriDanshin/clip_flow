from __future__ import annotations

import json
from typing import Callable, List, Optional

from loguru import logger

try:
    import webview  # type: ignore
except Exception as e:  # pragma: no cover - optional dependency at dev time
    webview = None  # defer import error until runtime

from src.ports.ui_port import UIPort
from src.ports.settings_port import SettingsPort


class _JsApi:
    def __init__(self, ui: "PyWebViewUIAdapter"):
        self._ui = ui

    # JS -> Python bridge
    def log(self, message: str) -> None:
        logger.debug(f"[WebView JS] {message}")

    def on_search(self, query: str) -> None:
        if self._ui._search_callback:
            self._ui._search_callback(query)

    def on_copy(self, index: int) -> None:
        if self._ui._copy_callback:
            self._ui._copy_callback(int(index))
        # mimic Tk behavior: hide after copy
        self._ui.hide_window()
        if self._ui._hide_callback:
            self._ui._hide_callback()

    def on_clear(self) -> None:
        if self._ui._clear_callback:
            self._ui._clear_callback()

    def on_ready(self) -> None:
        # Mark JS context ready and flush any pending UI state
        self._ui._mark_js_ready()

    def show_settings(self) -> None:
        self._ui.show_settings_window()

    def get_settings_schema(self) -> str:
        """Get settings schema as JSON string"""
        return self._ui.get_settings_schema()

    def get_current_settings(self) -> str:
        """Get current settings values as JSON string"""
        return self._ui.get_current_settings()

    def save_settings(self, settings_json: str) -> None:
        """Save settings from JSON string"""
        self._ui.save_settings_from_json(settings_json)


class PyWebViewUIAdapter(UIPort):
    def __init__(self, settings_port: SettingsPort):
        if webview is None:
            raise RuntimeError(
                "pywebview is not installed. Please `pip install pywebview`."
            )

        self.settings_port = settings_port

        self.window: Optional["webview.Window"] = None
        self.settings_window: Optional["webview.Window"] = None
        self._api = _JsApi(self)

        self._copy_callback: Optional[Callable[[int], None]] = None
        self._search_callback: Optional[Callable[[str], None]] = None
        self._clear_callback: Optional[Callable[[], None]] = None
        self._hide_callback: Optional[Callable[[], None]] = None

        self._current_items: List[str] = []
        self._is_hidden = False
        self._js_ready = False
        self._pending_history: Optional[List[str]] = None
        self._request_focus = False

        logger.debug("PyWebViewUIAdapter initialized.")

    # UIPort methods
    def show_history(self, items: List[str]) -> None:
        logger.debug(f"show_history called with {len(items)} items")
        logger.debug(f"JS ready state: {self._js_ready}")
        self._current_items = items.copy()
        if self._js_ready:
            logger.debug("JS is ready, pushing history to webview")
            self._push_history_to_webview()
        else:
            logger.debug("JS not ready, storing in pending history")
            self._pending_history = self._current_items.copy()

    def show_message(self, message: str, message_type: str = "info") -> None:
        if not self.window:
            logger.debug("show_message called before window is ready; skipping")
            return
        payload = json.dumps({"message": message, "type": message_type})
        # try window-scoped first
        ok = self._evaluate_js("typeof window.showMessage === 'function' ? 'ok' : 'missing'")
        if ok == 'ok':
            self._evaluate_js(f"window.showMessage({payload});")
        else:
            self._evaluate_js(f"showMessage({payload});")

    def run(self) -> None:
        logger.info("Starting PyWebView UI.")
        self.window = webview.create_window(
            title="Clip Flow",
            html=self._build_html(),
            width=400,
            height=600,
            resizable=True,
            easy_drag=False,
            js_api=self._api,
        )

        # Hook window events for close -> hide behavior
        try:
            def _on_closing():
                logger.info("Window close event detected. Hiding to system tray.")
                self.hide_window()
                if self._hide_callback:
                    self._hide_callback()
                # Prevent default close where supported
                try:
                    return True  # on some GUIs truthy return cancels close
                except Exception:
                    return None

            self.window.events.closing += _on_closing  # type: ignore[attr-defined]
            
        except Exception:
            # Events API not available on older pywebview backends
            pass

        webview.start(self._after_start, debug=False)

    def register_copy_callback(self, callback: Callable[[int], None]) -> None:
        self._copy_callback = callback

    def register_search_callback(self, callback: Callable[[str], None]) -> None:
        self._search_callback = callback

    def register_clear_callback(self, callback: Callable[[], None]) -> None:
        self._clear_callback = callback

    def register_hide_callback(self, callback: Callable[[], None]) -> None:
        self._hide_callback = callback

    def show_window(self) -> None:
        if not self.window:
            return
        try:
            # Prefer restore if available
            if hasattr(self.window, "restore"):
                self.window.restore()  # type: ignore[attr-defined]
            elif hasattr(self.window, "show"):
                self.window.show()  # type: ignore[attr-defined]
        except Exception as e:
            logger.debug(f"show_window fallback failed: {e}")
        if self._js_ready:
            self._evaluate_js("window.focusSearch();")
        else:
            self._request_focus = True
        self._is_hidden = False
        logger.debug("Window shown")

    def hide_window(self) -> None:
        # persist desired state even if window isn't created yet
        self._is_hidden = True
        if not self.window:
            return
        try:
            if hasattr(self.window, "hide"):
                self.window.hide()  # type: ignore[attr-defined]
            elif hasattr(self.window, "minimize"):
                self.window.minimize()  # type: ignore[attr-defined]
        except Exception as e:
            logger.debug(f"hide_window fallback failed: {e}")
        logger.debug("Window hidden to system tray")

    def shutdown(self) -> None:
        try:
            if self.window:
                self.window.destroy()
            if self.settings_window:
                self.settings_window.destroy()
        except Exception:
            pass

    def show_settings_window(self) -> None:
        """Show settings window"""
        if self.settings_window:
            # Focus existing window
            try:
                if hasattr(self.settings_window, "show"):
                    self.settings_window.show()  # type: ignore[attr-defined]
                elif hasattr(self.settings_window, "restore"):
                    self.settings_window.restore()  # type: ignore[attr-defined]
            except Exception:
                pass
            return

        # Create new settings window
        logger.info("Creating Settings window")
        self.settings_window = webview.create_window(
            title="Clip Flow - Settings",
            html=self._build_settings_html(),
            width=600,
            height=500,
            resizable=True,
            js_api=self._api,
        )
        
        # Hook window events to reset reference when closed
        try:
            def _on_settings_closing():
                logger.debug("Settings window closing, resetting reference")
                self.settings_window = None
                return True
            
            self.settings_window.events.closing += _on_settings_closing  # type: ignore[attr-defined]
        except Exception:
            # Events API not available on older pywebview backends
            pass

    def get_settings_schema(self) -> str:
        """Get settings schema as JSON string"""
        try:
            schema = self.settings_port._schema_adapter._schema
            logger.debug(f"Loaded settings schema: {schema}")
            result = json.dumps(schema)
            logger.debug(f"Returning schema JSON: {result[:200]}...")
            return result
        except Exception as e:
            logger.error(f"Error getting settings schema: {e}")
            raise

    def get_current_settings(self) -> str:
        """Get current settings values as JSON string"""
        schema = self.settings_port._schema_adapter._schema
        current_settings = {}
        for category in schema.get("categories", []):
            for setting in category.get("settings", []):
                key = setting["key"]
                default = setting.get("default")
                current_value = self.settings_port.get_setting(key, default)
                current_settings[key] = current_value
                logger.debug(f"Getting setting '{key}': {current_value} (default: {default})")
        
        logger.debug(f"All current settings: {current_settings}")
        return json.dumps(current_settings)

    def save_settings_from_json(self, settings_json: str) -> None:
        """Save settings from JSON string"""
        try:
            settings = json.loads(settings_json)
            for key, value in settings.items():
                self.settings_port.set_setting(key, value)
            logger.info(f"Settings saved: {list(settings.keys())}")
        except Exception as e:
            logger.error(f"Failed to save settings: {e}")

    # internals
    def _push_history_to_webview(self) -> None:
        if not self.window:
            return
        data = json.dumps(self._current_items)
        logger.debug(f"Pushing {len(self._current_items)} items to WebView")
        exists = self._evaluate_js("typeof updateHistory === 'function' ? 'ok' : 'missing'")
        if exists != 'ok':
            exists_win = self._evaluate_js("typeof window.updateHistory === 'function' ? 'ok' : 'missing'")
            logger.debug(f"updateHistory availability: global={exists}, window={exists_win}")
            if exists_win == 'ok':
                self._evaluate_js(f"window.updateHistory({data});")
                return
        self._evaluate_js(f"updateHistory({data});")

    def _evaluate_js(self, script: str):
        try:
            if self.window:
                short = script if len(script) < 120 else script[:117] + "..."
                logger.debug(f"Evaluating JS: {short}")
                return self.window.evaluate_js(script)
        except Exception as e:
            logger.debug(f"evaluate_js failed: {e}")
        return None

    def _after_start(self) -> None:
        # Called on GUI thread after window is ready
        if self._is_hidden:
            self.hide_window()
        else:
            if self._js_ready:
                self._evaluate_js("window.focusSearch();")
            else:
                self._request_focus = True

    def _mark_js_ready(self) -> None:
        if self._js_ready:
            return
        self._js_ready = True
        logger.debug("JS context is ready")
        logger.debug(f"Pending history items: {len(self._pending_history) if self._pending_history else 0}")
        if self._pending_history is not None:
            logger.debug(f"Processing pending history with {len(self._pending_history)} items")
            self._current_items = self._pending_history
            self._pending_history = None
            self._push_history_to_webview()
        else:
            logger.debug("No pending history to process")
        if self._request_focus:
            self._request_focus = False
            self._evaluate_js("window.focusSearch();")

    def _build_html(self) -> str:
        # Simple self-contained UI
        return f"""
<!doctype html>
<html lang=\"en\">
<head>
  <meta charset=\"utf-8\" />
  <meta name=\"viewport\" content=\"width=device-width, initial-scale=1\" />
  <title>Clip Flow</title>
  <style>
    html, body {{ margin: 0; padding: 0; height: 100%; font-family: -apple-system, Segoe UI, Roboto, Arial, sans-serif; }}
    .wrap {{ display: flex; flex-direction: column; height: 100%; box-sizing: border-box; }}
    .top {{ padding: 10px; border-bottom: 1px solid #e5e5e5; display: flex; gap: 8px; align-items: center; }}
    .top input {{ flex: 1; padding: 6px 8px; font-size: 14px; }}
    .content {{ flex: 1; overflow: auto; padding: 8px; }}
    table {{ width: 100%; border-collapse: collapse; }}
    th, td {{ text-align: left; padding: 6px 8px; font-size: 13px; }}
    tr:hover {{ background: #f7f7f7; }}
    tr.selected {{ background: #e8f0fe; }}
    .buttons {{ padding: 8px; border-top: 1px solid #e5e5e5; display: flex; gap: 8px; justify-content: space-between; }}
    button {{ padding: 6px 10px; font-size: 13px; cursor: pointer; }}
    .right {{ display: flex; gap: 8px; }}
    /* modal */
    .modal {{ position: fixed; inset: 0; background: rgba(0,0,0,0.35); display: none; align-items: center; justify-content: center; }}
    .modal .card {{ width: 90%; max-width: 600px; background: #fff; border-radius: 6px; box-shadow: 0 8px 24px rgba(0,0,0,0.2); display: flex; flex-direction: column; max-height: 80vh; }}
    .modal .head {{ padding: 10px; border-bottom: 1px solid #e5e5e5; font-weight: 600; }}
    .modal .body {{ padding: 10px; overflow: auto; white-space: pre-wrap; font-family: Consolas, Menlo, monospace; font-size: 12px; }}
    .modal .foot {{ padding: 8px; border-top: 1px solid #e5e5e5; display: flex; justify-content: flex-end; gap: 8px; }}
  </style>
  <script>
    let state = {{ items: [], selected: -1 }};
    function updateHistory(items) {{
      state.items = items || [];
      const tbody = document.getElementById('tbody');
      tbody.innerHTML = '';
      state.items.forEach((item, i) => {{
        const tr = document.createElement('tr');
        tr.dataset.index = i;
        if (i === state.selected) tr.classList.add('selected');
        const num = document.createElement('td'); num.textContent = (i + 1).toString(); num.style.width = '36px';
        const txt = document.createElement('td');
        const preview = item.replace(/\\n|\\r/g, ' ');
        txt.textContent = preview.length > 50 ? (preview.slice(0,47) + '...') : preview;
        tr.appendChild(num); tr.appendChild(txt);
        tr.addEventListener('click', () => selectRow(i));
        tr.addEventListener('dblclick', () => onCopy());
        tbody.appendChild(tr);
      }});
      // auto-select first if nothing selected and there are items
      if (state.items.length && state.selected === -1) {{
        selectRow(0);
      }}
    }}

    function selectRow(i) {{
      state.selected = i;
      const rows = [...document.querySelectorAll('#tbody tr')];
      rows.forEach(r => r.classList.remove('selected'));
      const row = rows[i]; if (row) row.classList.add('selected');
    }}

    function onSearch(e) {{
      const val = typeof e === 'string' ? e : e.target.value;
      if (window.pywebview && pywebview.api) pywebview.api.on_search(val);
    }}

    function onCopy() {{
      if (state.selected < 0) {{ showMessage({{message: 'Please select an item to copy.', type: 'warning'}}); return; }}
      if (window.pywebview && pywebview.api) pywebview.api.on_copy(state.selected);
    }}

    function onView() {{
      if (state.selected < 0) {{ showMessage({{message: 'Please select an item to view.', type: 'warning'}}); return; }}
      const text = state.items[state.selected] || '';
      document.getElementById('modal-text').textContent = text;
      document.getElementById('modal').style.display = 'flex';
    }}

    function onClear() {{
      if (!confirm('Are you sure you want to clear all clipboard history?')) return;
      if (window.pywebview && pywebview.api) pywebview.api.on_clear();
    }}

    function onCloseModal() {{ document.getElementById('modal').style.display = 'none'; }}

    function copyFromModal() {{
      if (window.pywebview && pywebview.api) pywebview.api.on_copy(state.selected);
      onCloseModal();
    }}

    function showMessage(payload) {{
      const msg = (payload && payload.message) ? payload.message : '';
      alert(msg);
    }}

    function focusSearch() {{
      const el = document.getElementById('search'); if (el) el.focus();
    }}

    function checkPyWebViewAPI() {{
      if (window.pywebview && pywebview.api && pywebview.api.on_ready) {{
        pywebview.api.on_ready();
        return true;
      }}
      return false;
    }}

    window.addEventListener('DOMContentLoaded', () => {{
      document.getElementById('search').addEventListener('input', onSearch);
      document.getElementById('copy').addEventListener('click', onCopy);
      document.getElementById('view').addEventListener('click', onView);
      document.getElementById('clear').addEventListener('click', onClear);
      document.getElementById('settings').addEventListener('click', () => {{ if (window.pywebview && pywebview.api) pywebview.api.show_settings(); }});
      document.getElementById('close-modal').addEventListener('click', onCloseModal);
      document.getElementById('copy-modal').addEventListener('click', copyFromModal);
      
      focusSearch();
      
      // Try to call API immediately
      if (!checkPyWebViewAPI()) {{
        // If API not available, retry after a short delay
        setTimeout(() => {{
          if (!checkPyWebViewAPI()) {{
            setTimeout(checkPyWebViewAPI, 500);
          }}
        }}, 100);
      }}
    }});
  </script>
  </head>
  <body>
    <div class="wrap">
      <div class="top">
        <div>🔍</div>
        <input id="search" type="text" placeholder="Search..." />
      </div>
      <div class="content">
        <table>
          <thead><tr><th>#</th><th>Content</th></tr></thead>
          <tbody id="tbody"></tbody>
        </table>
      </div>
      <div class="buttons">
        <div class="left">
          <button id="copy">Copy Selected</button>
          <button id="view">View Full Text</button>
        </div>
        <div class="right">
          <button id="settings">⚙️ Settings</button>
          <button id="clear">Clear History</button>
        </div>
      </div>
    </div>

    <div id="modal" class="modal">
      <div class="card">
        <div class="head">Full Text</div>
        <div id="modal-text" class="body"></div>
        <div class="foot">
          <button id="close-modal">Close</button>
          <button id="copy-modal">Copy to Clipboard</button>
        </div>
      </div>
    </div>
  </body>
</html>
"""

    def _build_settings_html(self) -> str:
        """Build HTML for settings window with dynamic schema parsing"""
        return f"""
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>Clip Flow - Settings</title>
  <style>
    html, body {{ margin: 0; padding: 0; height: 100%; font-family: -apple-system, Segoe UI, Roboto, Arial, sans-serif; }}
    .container {{ padding: 20px; max-width: 600px; margin: 0 auto; height: calc(100% - 40px); display: flex; flex-direction: column; }}
    h1 {{ margin: 0 0 20px 0; font-size: 24px; color: #333; }}
    
    .categories {{ flex: 1; overflow-y: auto; }}
    .category {{ margin-bottom: 30px; }}
    .category-title {{ font-size: 18px; font-weight: 600; color: #333; margin-bottom: 15px; border-bottom: 2px solid #007bff; padding-bottom: 5px; }}
    
    .setting-group {{ margin-bottom: 20px; }}
    .setting-label {{ display: block; margin-bottom: 8px; font-weight: 500; color: #555; }}
    .setting-description {{ font-size: 12px; color: #777; margin-top: 4px; }}
    
    input, select, textarea {{ padding: 8px 12px; border: 1px solid #ddd; border-radius: 4px; font-size: 14px; width: 100%; box-sizing: border-box; }}
    input[type="checkbox"] {{ width: auto; margin-right: 8px; }}
    input[type="range"] {{ width: 100%; }}
    
    .range-container {{ display: flex; align-items: center; gap: 10px; }}
    .range-value {{ min-width: 40px; text-align: center; font-weight: 500; }}
    
    .buttons {{ margin-top: 20px; display: flex; gap: 10px; justify-content: flex-end; border-top: 1px solid #ddd; padding-top: 20px; }}
    button {{ padding: 8px 16px; border: none; border-radius: 4px; font-size: 14px; cursor: pointer; }}
    .btn-primary {{ background: #007bff; color: white; }}
    .btn-secondary {{ background: #6c757d; color: white; }}
    .btn-primary:hover {{ background: #0056b3; }}
    .btn-secondary:hover {{ background: #545b62; }}
  </style>
</head>
<body>
  <div class="container">
    <h1>⚙️ Settings</h1>
    
    <div class="categories" id="settings-container">
      <!-- Settings will be dynamically generated here -->
    </div>
    
    <div class="buttons">
      <button type="button" class="btn-secondary" id="cancel-btn">Cancel</button>
      <button type="button" class="btn-primary" id="save-btn">Save</button>
    </div>
  </div>
  
  <script>
    let settingsSchema = null;
    let currentSettings = null;
    
    function createSettingElement(setting, currentValue) {{
      const group = document.createElement('div');
      group.className = 'setting-group';
      
      const label = document.createElement('label');
      label.className = 'setting-label';
      label.textContent = setting.title;
      label.setAttribute('for', setting.key);
      group.appendChild(label);
      
      let input;
      
      if (setting.type === 'select') {{
        input = document.createElement('select');
        input.id = setting.key;
        input.name = setting.key;
        
        setting.options.forEach(option => {{
          const opt = document.createElement('option');
          opt.value = option;
          opt.textContent = option.charAt(0).toUpperCase() + option.slice(1);
          if (option === currentValue) opt.selected = true;
          input.appendChild(opt);
        }});
      }} else if (setting.type === 'checkbox') {{
        input = document.createElement('input');
        input.type = 'checkbox';
        input.id = setting.key;
        input.name = setting.key;
        input.checked = currentValue;
      }} else if (setting.type === 'slider') {{
        const container = document.createElement('div');
        container.className = 'range-container';
        
        input = document.createElement('input');
        input.type = 'range';
        input.id = setting.key;
        input.name = setting.key;
        input.min = setting.min || 0;
        input.max = setting.max || 100;
        input.value = currentValue;
        
        const valueDisplay = document.createElement('span');
        valueDisplay.className = 'range-value';
        valueDisplay.textContent = currentValue;
        
        input.addEventListener('input', () => {{
          valueDisplay.textContent = input.value;
        }});
        
        container.appendChild(input);
        container.appendChild(valueDisplay);
        group.appendChild(container);
      }} else if (setting.type === 'spinbox') {{
        input = document.createElement('input');
        input.type = 'number';
        input.id = setting.key;
        input.name = setting.key;
        input.min = setting.min || 0;
        input.max = setting.max || 1000;
        input.step = setting.step || 1;
        input.value = currentValue;
      }} else {{
        // text type
        input = document.createElement('input');
        input.type = 'text';
        input.id = setting.key;
        input.name = setting.key;
        input.value = currentValue || '';
      }}
      
      if (input && setting.type !== 'slider') {{
        group.appendChild(input);
      }}
      
      if (setting.description) {{
        const desc = document.createElement('div');
        desc.className = 'setting-description';
        desc.textContent = setting.description;
        group.appendChild(desc);
      }}
      
      return group;
    }}
    
    function renderSettings(schema, settings) {{
      const container = document.getElementById('settings-container');
      container.innerHTML = '';
      
      schema.categories.forEach(category => {{
        const categoryDiv = document.createElement('div');
        categoryDiv.className = 'category';
        
        const categoryTitle = document.createElement('div');
        categoryTitle.className = 'category-title';
        categoryTitle.textContent = category.title;
        categoryDiv.appendChild(categoryTitle);
        
        category.settings.forEach(setting => {{
          const currentValue = settings[setting.key] !== undefined ? settings[setting.key] : setting.default;
          const settingElement = createSettingElement(setting, currentValue);
          categoryDiv.appendChild(settingElement);
        }});
        
        container.appendChild(categoryDiv);
      }});
    }}
    
    function collectSettings() {{
      const formData = new FormData();
      const settings = {{}};
      
      settingsSchema.categories.forEach(category => {{
        category.settings.forEach(setting => {{
          const element = document.getElementById(setting.key);
          if (element) {{
            if (setting.type === 'checkbox') {{
              settings[setting.key] = element.checked;
            }} else if (setting.type === 'slider' || setting.type === 'spinbox') {{
              settings[setting.key] = parseInt(element.value);
            }} else {{
              settings[setting.key] = element.value;
            }}
          }}
        }});
      }});
      
      return settings;
    }}
    
    async function loadSettings() {{
      try {{
        console.log('Starting to load settings...');
        if (window.pywebview && pywebview.api) {{
          console.log('pywebview.api is available');
          
          const schemaJson = await pywebview.api.get_settings_schema();
          console.log('Schema loaded:', schemaJson);
          
          const settingsJson = await pywebview.api.get_current_settings();
          console.log('Settings loaded:', settingsJson);
          
          settingsSchema = JSON.parse(schemaJson);
          currentSettings = JSON.parse(settingsJson);
          
          console.log('Parsed schema:', settingsSchema);
          console.log('Parsed settings:', currentSettings);
          
          renderSettings(settingsSchema, currentSettings);
          console.log('Settings rendered');
        }} else {{
          console.error('pywebview.api is not available');
        }}
      }} catch (error) {{
        console.error('Failed to load settings:', error);
        // Show error message in the UI
        const container = document.getElementById('settings-container');
        container.innerHTML = '<div style="color: red; padding: 20px;">Failed to load settings: ' + error.message + '</div>';
      }}
    }}
    
    window.addEventListener('DOMContentLoaded', () => {{
      document.getElementById('cancel-btn').addEventListener('click', () => {{
        window.close();
      }});
      
      document.getElementById('save-btn').addEventListener('click', async () => {{
        try {{
          const settings = collectSettings();
          if (window.pywebview && pywebview.api) {{
            await pywebview.api.save_settings(JSON.stringify(settings));
            alert('Settings saved successfully!');
            window.close();
          }}
        }} catch (error) {{
          console.error('Failed to save settings:', error);
          alert('Failed to save settings. Please try again.');
        }}
      }});
      
      // Load settings when page is ready - but wait for API
      function tryLoadSettings() {{
        if (window.pywebview && pywebview.api) {{
          loadSettings();
        }} else {{
          console.log('API not ready, retrying in 100ms...');
          setTimeout(() => {{
            if (window.pywebview && pywebview.api) {{
              loadSettings();
            }} else {{
              console.log('API still not ready, retrying in 500ms...');
              setTimeout(tryLoadSettings, 500);
            }}
          }}, 100);
        }}
      }}
      
      tryLoadSettings();
    }});
  </script>
</body>
</html>
"""
