import json

import webview
from loguru import logger

from src.ports.settings_port import SettingsPort
from src.adapters.ui.javascript_api import JavaScriptAPI
from src.utils.assets import asset_uri as get_asset_uri


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
        uri = get_asset_uri('settings.html')
        if not uri:
            raise RuntimeError("assets/settings.html not found. Build frontend via 'python scripts/build_frontend.py'.")

        self.settings_window = webview.create_window(
            title="Clip Flow - Settings",
            url=uri,
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
