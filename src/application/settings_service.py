from typing import Any, Dict

from loguru import logger

from src.domain.settings import Settings
from src.ports.settings_port import SettingsRepositoryPort, SettingsServicePort


class SettingsService(SettingsServicePort):
    def __init__(self, repository: SettingsRepositoryPort, settings: Settings):
        self._repository = repository
        self._settings = settings
        self._load_from_repository()

    def _load_from_repository(self) -> None:
        if self._repository.exists():
            data = self._repository.load()
            if data:
                self._settings.deserialize(data)
                logger.debug("Settings loaded from repository")
            else:
                logger.warning(
                    "Failed to load settings from repository, using defaults"
                )
        else:
            logger.debug("Settings file does not exist, using default values")

    def get_settings(self) -> Settings:
        return self._settings

    def update_setting(self, key: str, value: Any) -> bool:
        success = self._settings.set_value(key, value)
        if success:
            logger.debug(f"Setting '{key}' updated to '{value}'")
        else:
            logger.warning(f"Failed to update setting '{key}' to '{value}'")
        return success

    def update_settings(self, values: Dict[str, Any]) -> Dict[str, bool]:
        results = self._settings.update_values(values)
        successful_updates = sum(1 for success in results.values() if success)
        logger.debug(f"Updated {successful_updates}/{len(values)} settings")
        return results

    def save_settings(self) -> bool:
        serialized_data = self._settings.serialize()
        success = self._repository.save(serialized_data)
        if success:
            logger.debug("Settings saved to repository")
        else:
            logger.error("Failed to save settings to repository")
        return success

    def reload_settings(self) -> bool:
        try:
            self._load_from_repository()
            logger.debug("Settings reloaded from repository")
            return True
        except Exception as e:
            logger.error(f"Failed to reload settings: {e}")
            return False
