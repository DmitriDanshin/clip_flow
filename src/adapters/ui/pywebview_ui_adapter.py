from __future__ import annotations

import json
from typing import Callable

from loguru import logger

import webview
from src.ports.ui_port import UIPort
from src.ports.settings_port import SettingsPort
from src.adapters.ui.pywebview_settings import PyWebViewSettings
from src.adapters.ui.javascript_api import JavaScriptAPI


class PyWebViewUIAdapter(UIPort):
    def __init__(self, settings_port: SettingsPort):
        if webview is None:
            raise RuntimeError(
                "pywebview is not installed. Please `pip install pywebview`."
            )

        self.settings_port = settings_port

        self.window: webview.Window | None = None
        self._api = JavaScriptAPI(self)
        self.settings_manager = PyWebViewSettings(settings_port, self._api)

        self._copy_callback: Callable[[int], None] | None = None
        self._search_callback: Callable[[int | str], None] | None = None
        self._clear_callback: Callable[[int], None] | None = None
        self._hide_callback: Callable[[int], None] | None = None

        self._current_items: list[str] = []
        self._is_hidden = False
        self._js_ready = False
        self._pending_history: list[str] | None = None
        self._request_focus = False

        logger.debug("PyWebViewUIAdapter initialized.")

    def show_history(self, items: list[str]) -> None:
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

        self._evaluate_js(f"window.showMessage({payload});")

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

        webview.start(self._after_start, debug=False)

    def register_copy_callback(self, callback: Callable[[int], None]) -> None:
        self._copy_callback = callback

    def register_search_callback(self, callback: Callable[[str], None]) -> None:
        self._search_callback = callback

    def register_clear_callback(self, callback: Callable[[], None]) -> None:
        self._clear_callback = callback

    def register_hide_callback(self, callback: Callable[[], None]) -> None:
        self._hide_callback = callback

    def handle_js_search(self, query: str) -> None:
        if self._search_callback:
            self._search_callback(query)

    def handle_js_copy(self, index: int) -> None:
        if self._copy_callback:
            self._copy_callback(index)
        self.hide_window()
        if self._hide_callback:
            self._hide_callback()

    def handle_js_clear(self) -> None:
        if self._clear_callback:
            self._clear_callback()

    def handle_js_ready(self) -> None:
        self._mark_js_ready()

    def show_window(self) -> None:
        if not self.window:
            return

        self.window.restore()

        if self._js_ready:
            self._evaluate_js("window.focusSearch();")
        else:
            self._request_focus = True

        self._is_hidden = False
        logger.debug("Window shown")

    def hide_window(self) -> None:
        self._is_hidden = True
        if not self.window:
            return

        self.window.hide()

        logger.debug("Window hidden to system tray")

    def shutdown(self) -> None:
        if self.window:
            self.window.destroy()

        if self.settings_manager:
            self.settings_manager.destroy_window()

    def show_settings_window(self) -> None:
        self.settings_manager.show_settings_window()

    def get_settings_schema(self) -> str:
        return self.settings_manager.get_settings_schema()

    def get_current_settings(self) -> str:
        return self.settings_manager.get_current_settings()

    def save_settings_from_json(self, settings_json: str) -> None:
        self.settings_manager.save_settings_from_json(settings_json)

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
        except Exception as exception:
            logger.debug(f"evaluate_js failed: {exception}")
        return None

    def _after_start(self) -> None:
        if self._is_hidden:
            self.hide_window()
        elif self._js_ready:
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

    
