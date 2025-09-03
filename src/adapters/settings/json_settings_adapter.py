import json
import os
from typing import Dict, Any
from loguru import logger
from src.ports.settings_port import SettingsPort
from src.ports.settings_schema_port import SettingsSchemaPort
from src.infrastructure.system_paths import get_config_dir


class JsonSettingsAdapter(SettingsPort):
    def __init__(
        self,
        config_file_name: str = "settings.json",
        schema_adapter: SettingsSchemaPort = None,
    ):
        self.config_file = os.path.join(get_config_dir(), config_file_name)
        self._settings: Dict[str, Any] = {}
        self._schema_adapter = schema_adapter
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
            with open(self.config_file, "w", encoding="utf-8") as f:
                json.dump(self._settings, f, indent=2)
            logger.info(f"Settings saved to {self.config_file}")
        except Exception as e:
            logger.error(f"Failed to save settings: {e}")
            raise

    def load_settings(self) -> None:
        default_settings = {}
        if self._schema_adapter:
            default_settings = self._schema_adapter.get_all_defaults()
            logger.debug(f"Default settings from schema: {default_settings}")

        try:
            if os.path.exists(self.config_file):
                with open(self.config_file, "r", encoding="utf-8") as f:
                    loaded_settings = json.load(f)
                logger.info(f"Loaded {len(loaded_settings)} settings from file: {self.config_file}")
                
                self._settings = default_settings.copy()
                self._settings.update(loaded_settings)
                
                for key, value in loaded_settings.items():
                    logger.info(f"Setting '{key}' loaded with value: {value}")
                    
                logger.info(f"Total settings available: {len(self._settings)}")
            else:
                self._settings = default_settings.copy()
                logger.info(f"No settings file found. Using {len(default_settings)} default settings from schema")
                
                for key, value in default_settings.items():
                    logger.info(f"Default setting '{key}': {value}")
                    
        except Exception as exception:
            logger.error(f"Failed to load settings: {exception}")
            self._settings = default_settings.copy()
            logger.info(f"Fallback to {len(default_settings)} default settings from schema")
