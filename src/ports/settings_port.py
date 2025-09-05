from abc import ABC, abstractmethod
from typing import Dict, Any


class SettingsPort(ABC):
    @abstractmethod
    def get_setting(self, key: str, default: Any = None) -> Any:
        """Get a specific setting value by key."""

    @abstractmethod
    def set_setting(self, key: str, value: Any) -> None:
        """Set a specific setting value."""

    @abstractmethod
    def get_all_settings(self) -> Dict[str, Any]:
        """Get all settings as a dictionary."""

    @abstractmethod
    def save_settings(self) -> None:
        """Persist settings to storage."""

    @abstractmethod
    def load_settings(self) -> None:
        """Load settings from storage."""

    @abstractmethod
    def get_schema(self) -> Dict[str, Any]:
        """Get the settings schema."""
