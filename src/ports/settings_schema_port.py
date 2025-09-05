from abc import ABC, abstractmethod
from typing import Dict, List, Any, Optional


class SettingsSchemaPort(ABC):
    @abstractmethod
    def get_categories(self) -> List[Dict[str, Any]]:
        pass

    @abstractmethod
    def get_category(self, key: str) -> Optional[Dict[str, Any]]:
        pass

    @abstractmethod
    def get_setting_definition(self, setting_key: str) -> Optional[Dict[str, Any]]:
        pass

    @abstractmethod
    def get_default_value(self, setting_key: str) -> Any:
        pass

    @abstractmethod
    def get_all_defaults(self) -> Dict[str, Any]:
        pass

    @abstractmethod
    def validate_setting_value(self, setting_key: str, value: Any) -> bool:
        pass

    @abstractmethod
    def get_schema(self) -> Dict[str, Any]:
        """Get the full settings schema."""