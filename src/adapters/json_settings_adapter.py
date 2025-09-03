import json
import os
from typing import Dict, Any
from loguru import logger
from src.ports.settings_port import SettingsPort
from src.infrastructure.system_paths import get_config_dir


class JsonSettingsAdapter(SettingsPort):
    def __init__(self, config_file_name: str = "settings.json"):
        self.config_file = os.path.join(get_config_dir(), config_file_name)
        self._settings: Dict[str, Any] = {}
        self._default_settings = {
            "theme": "arc"
        }
        self.load_settings()

    def get_setting(self, key: str, default: Any = None) -> Any:
        return self._settings.get(key, default)

    def set_setting(self, key: str, value: Any) -> None:
        self._settings[key] = value

    def get_all_settings(self) -> Dict[str, Any]:
        return self._settings.copy()

    def save_settings(self) -> None:
        try:
            os.makedirs(os.path.dirname(self.config_file), exist_ok=True)
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(self._settings, f, indent=2)
            logger.info(f"Settings saved to {self.config_file}")
        except Exception as e:
            logger.error(f"Failed to save settings: {e}")
            raise

    def load_settings(self) -> None:
        try:
            if os.path.exists(self.config_file):
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    self._settings = json.load(f)
                logger.debug(f"Settings loaded from {self.config_file}")
            else:
                self._settings = self._default_settings.copy()
                logger.debug("Using default settings")
        except Exception as e:
            logger.error(f"Failed to load settings: {e}")
            self._settings = self._default_settings.copy()
            logger.debug("Fallback to default settings")