from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
from src.domain.settings import Settings


class SettingsRepositoryPort(ABC):
    @abstractmethod
    def load(self) -> Optional[Dict[str, Any]]:
        pass

    @abstractmethod
    def save(self, settings_data: Dict[str, Any]) -> bool:
        pass

    @abstractmethod
    def exists(self) -> bool:
        pass


class SettingsServicePort(ABC):
    @abstractmethod
    def get_settings(self) -> Settings:
        pass

    @abstractmethod
    def update_setting(self, key: str, value: Any) -> bool:
        pass

    @abstractmethod
    def update_settings(self, values: Dict[str, Any]) -> Dict[str, bool]:
        pass

    @abstractmethod
    def save_settings(self) -> bool:
        pass

    @abstractmethod
    def reload_settings(self) -> bool:
        pass