import json

import webview
from loguru import logger

from src.adapters.ui.javascript_api import JavaScriptAPI
from src.ports.settings_port import SettingsPort


class PyWebViewSettings:
    def __init__(self, settings_port: SettingsPort, js_api: JavaScriptAPI):
        self.settings_port = settings_port
        self.settings_window:webview.Window | None = None
        self._api = js_api

    def show_settings_window(self) -> None:
        if self.settings_window:
            self.settings_window.show()
            return

        logger.info("Creating Settings window")
        self.settings_window = webview.create_window(
            title="Clip Flow - Settings",
            html=self._build_settings_html(),
            width=600,
            height=500,
            resizable=True,
            js_api=self._api,
        )

        def _on_settings_closing():
            logger.debug("Settings window closing, resetting reference")
            self.settings_window = None
            return True

        self.settings_window.events.closing += _on_settings_closing

    def get_settings_schema(self) -> str:
        schema = self.settings_port.get_schema()
        logger.debug(f"Loaded settings schema: {schema}")
        result = json.dumps(schema)
        logger.debug(f"Returning schema JSON: {result[:200]}...")
        return result

    def get_current_settings(self) -> str:
        schema = self.settings_port.get_schema()
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
        settings = json.loads(settings_json)
        for key, value in settings.items():
            self.settings_port.set_setting(key, value)
        logger.info(f"Settings saved: {list(settings.keys())}")


    def destroy_window(self):
        if self.settings_window:
            self.settings_window.destroy()

    @staticmethod
    def _build_settings_html() -> str:
        return """
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>Clip Flow - Settings</title>
  <style>
    html, body { margin: 0; padding: 0; height: 100%; font-family: -apple-system, Segoe UI, Roboto, Arial, sans-serif; }
    .container { padding: 20px; max-width: 600px; margin: 0 auto; height: calc(100% - 40px); display: flex; flex-direction: column; }
    h1 { margin: 0 0 20px 0; font-size: 24px; color: #333; }
    
    .categories { flex: 1; overflow-y: auto; }
    .category { margin-bottom: 30px; }
    .category-title { font-size: 18px; font-weight: 600; color: #333; margin-bottom: 15px; border-bottom: 2px solid #007bff; padding-bottom: 5px; }
    
    .setting-group { margin-bottom: 20px; }
    .setting-label { display: block; margin-bottom: 8px; font-weight: 500; color: #555; }
    .setting-description { font-size: 12px; color: #777; margin-top: 4px; }
    
    input, select, textarea { padding: 8px 12px; border: 1px solid #ddd; border-radius: 4px; font-size: 14px; width: 100%; box-sizing: border-box; }
    input[type="checkbox"] { width: auto; margin-right: 8px; }
    input[type="range"] { width: 100%; }
    
    .range-container { display: flex; align-items: center; gap: 10px; }
    .range-value { min-width: 40px; text-align: center; font-weight: 500; }
    
    .buttons { margin-top: 20px; display: flex; gap: 10px; justify-content: flex-end; border-top: 1px solid #ddd; padding-top: 20px; }
    button { padding: 8px 16px; border: none; border-radius: 4px; font-size: 14px; cursor: pointer; }
    .btn-primary { background: #007bff; color: white; }
    .btn-secondary { background: #6c757d; color: white; }
    .btn-primary:hover { background: #0056b3; }
    .btn-secondary:hover { background: #545b62; }
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
    
    function createSettingElement(setting, currentValue) {
      const group = document.createElement('div');
      group.className = 'setting-group';
      
      const label = document.createElement('label');
      label.className = 'setting-label';
      label.textContent = setting.title;
      label.setAttribute('for', setting.key);
      group.appendChild(label);
      
      let input;
      
      if (setting.type === 'select') {
        input = document.createElement('select');
        input.id = setting.key;
        input.name = setting.key;
        
        setting.options.forEach(option => {
          const opt = document.createElement('option');
          opt.value = option;
          opt.textContent = option.charAt(0).toUpperCase() + option.slice(1);
          if (option === currentValue) opt.selected = true;
          input.appendChild(opt);
        });
      } else if (setting.type === 'checkbox') {
        input = document.createElement('input');
        input.type = 'checkbox';
        input.id = setting.key;
        input.name = setting.key;
        input.checked = currentValue;
      } else if (setting.type === 'slider') {
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
        
        input.addEventListener('input', () => {
          valueDisplay.textContent = input.value;
        });
        
        container.appendChild(input);
        container.appendChild(valueDisplay);
        group.appendChild(container);
      } else if (setting.type === 'spinbox') {
        input = document.createElement('input');
        input.type = 'number';
        input.id = setting.key;
        input.name = setting.key;
        input.min = setting.min || 0;
        input.max = setting.max || 1000;
        input.step = setting.step || 1;
        input.value = currentValue;
      } else {
        // text type
        input = document.createElement('input');
        input.type = 'text';
        input.id = setting.key;
        input.name = setting.key;
        input.value = currentValue || '';
      }
      
      if (input && setting.type !== 'slider') {
        group.appendChild(input);
      }
      
      if (setting.description) {
        const desc = document.createElement('div');
        desc.className = 'setting-description';
        desc.textContent = setting.description;
        group.appendChild(desc);
      }
      
      return group;
    }
    
    function renderSettings(schema, settings) {
      const container = document.getElementById('settings-container');
      container.innerHTML = '';
      
      schema.categories.forEach(category => {
        const categoryDiv = document.createElement('div');
        categoryDiv.className = 'category';
        
        const categoryTitle = document.createElement('div');
        categoryTitle.className = 'category-title';
        categoryTitle.textContent = category.title;
        categoryDiv.appendChild(categoryTitle);
        
        category.settings.forEach(setting => {
          const currentValue = settings[setting.key] !== undefined ? settings[setting.key] : setting.default;
          const settingElement = createSettingElement(setting, currentValue);
          categoryDiv.appendChild(settingElement);
        });
        
        container.appendChild(categoryDiv);
      });
    }
    
    function collectSettings() {
      const formData = new FormData();
      const settings = {};
      
      settingsSchema.categories.forEach(category => {
        category.settings.forEach(setting => {
          const element = document.getElementById(setting.key);
          if (element) {
            if (setting.type === 'checkbox') {
              settings[setting.key] = element.checked;
            } else if (setting.type === 'slider' || setting.type === 'spinbox') {
              settings[setting.key] = parseInt(element.value);
            } else {
              settings[setting.key] = element.value;
            }
          }
        });
      });
      
      return settings;
    }
    
    async function loadSettings() {
      try {
        console.log('Starting to load settings...');
        if (window.pywebview && pywebview.api) {
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
        } else {
          console.error('pywebview.api is not available');
        }
      } catch (error) {
        console.error('Failed to load settings:', error);
        // Show error message in the UI
        const container = document.getElementById('settings-container');
        container.innerHTML = '<div style="color: red; padding: 20px;">Failed to load settings: ' + error.message + '</div>';
      }
    }
    
    window.addEventListener('DOMContentLoaded', () => {
      document.getElementById('cancel-btn').addEventListener('click', () => {
        window.close();
      });
      
      document.getElementById('save-btn').addEventListener('click', async () => {
        try {
          const settings = collectSettings();
          if (window.pywebview && pywebview.api) {
            await pywebview.api.save_settings(JSON.stringify(settings));
            alert('Settings saved successfully!');
            window.close();
          }
        } catch (error) {
          console.error('Failed to save settings:', error);
          alert('Failed to save settings. Please try again.');
        }
      });
      
      // Load settings when page is ready - but wait for API
      function tryLoadSettings() {
        if (window.pywebview && pywebview.api) {
          loadSettings();
        } else {
          console.log('API not ready, retrying in 100ms...');
          setTimeout(() => {
            if (window.pywebview && pywebview.api) {
              loadSettings();
            } else {
              console.log('API still not ready, retrying in 500ms...');
              setTimeout(tryLoadSettings, 500);
            }
          }, 100);
        }
      }
      
      tryLoadSettings();
    });
  </script>
</body>
</html>
"""
