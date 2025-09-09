import json
from pathlib import Path
from typing import Dict, Any, Optional
from loguru import logger

from src.ports.settings_port import SettingsRepositoryPort
from src.infrastructure.system_paths import get_config_dir


class JsonSettingsAdapter(SettingsRepositoryPort):
    def __init__(self, filename: str = "settings.json"):
        self._settings_file = get_config_dir() / filename
        self._ensure_config_dir_exists()

    def _ensure_config_dir_exists(self) -> None:
        try:
            self._settings_file.parent.mkdir(parents=True, exist_ok=True)
        except OSError as e:
            logger.error(f"Failed to create config directory: {e}")
            raise

    def load(self) -> Optional[Dict[str, Any]]:
        if not self._settings_file.exists():
            logger.debug(f"Settings file {self._settings_file} does not exist")
            return None

        try:
            with open(self._settings_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            logger.debug(f"Settings loaded from {self._settings_file}")
            return data
        except (json.JSONDecodeError, OSError) as e:
            logger.error(f"Failed to load settings from {self._settings_file}: {e}")
            return None

    def save(self, settings_data: Dict[str, Any]) -> bool:
        try:
            with open(self._settings_file, 'w', encoding='utf-8') as f:
                json.dump(settings_data, f, indent=2, ensure_ascii=False)
            logger.debug(f"Settings saved to {self._settings_file}")
            return True
        except OSError as e:
            logger.error(f"Failed to save settings to {self._settings_file}: {e}")
            return False

    def exists(self) -> bool:
        return self._settings_file.exists()