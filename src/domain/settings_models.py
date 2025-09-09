from abc import ABC, abstractmethod
from typing import Any, Optional, Dict, Type
from dataclasses import dataclass
from enum import Enum


class SettingType(Enum):
    INTEGER = "integer"
    FLOAT = "float" 
    BOOLEAN = "boolean"
    STRING = "string"
    SLIDER = "slider"


@dataclass
class SettingMetadata:
    key: str
    display_name: str
    description: str
    setting_type: SettingType
    default_value: Any
    min_value: Optional[float] = None
    max_value: Optional[float] = None
    step: Optional[float] = None


class SettingDefinition(ABC):
    def __init__(self, metadata: SettingMetadata):
        self.metadata = metadata

    @abstractmethod
    def validate_value(self, value: Any) -> bool:
        pass

    @abstractmethod
    def serialize_value(self, value: Any) -> Any:
        pass

    @abstractmethod
    def deserialize_value(self, serialized_value: Any) -> Any:
        pass


class IntegerSetting(SettingDefinition):
    def validate_value(self, value: Any) -> bool:
        if value is None:
            return True
        if not isinstance(value, int):
            return False
        
        if self.metadata.min_value is not None and value < self.metadata.min_value:
            return False
        
        if self.metadata.max_value is not None and value > self.metadata.max_value:
            return False
        
        return True

    def serialize_value(self, value: Any) -> Any:
        return value if value is None else int(value)

    def deserialize_value(self, serialized_value: Any) -> Any:
        return serialized_value if serialized_value is None else int(serialized_value)


class FloatSetting(SettingDefinition):
    def validate_value(self, value: Any) -> bool:
        if not isinstance(value, (int, float)):
            return False
        
        if self.metadata.min_value is not None and value < self.metadata.min_value:
            return False
        
        if self.metadata.max_value is not None and value > self.metadata.max_value:
            return False
        
        return True

    def serialize_value(self, value: Any) -> float:
        return float(value)

    def deserialize_value(self, serialized_value: Any) -> float:
        return float(serialized_value)


class BooleanSetting(SettingDefinition):
    def validate_value(self, value: Any) -> bool:
        return isinstance(value, bool)

    def serialize_value(self, value: Any) -> bool:
        return bool(value)

    def deserialize_value(self, serialized_value: Any) -> bool:
        return bool(serialized_value)


class StringSetting(SettingDefinition):
    def validate_value(self, value: Any) -> bool:
        return isinstance(value, str)

    def serialize_value(self, value: Any) -> str:
        return str(value)

    def deserialize_value(self, serialized_value: Any) -> str:
        return str(serialized_value)


class SliderSetting(SettingDefinition):
    def __init__(self, metadata: SettingMetadata):
        super().__init__(metadata)
        if metadata.min_value is None or metadata.max_value is None:
            raise ValueError("Slider setting requires min_value and max_value")

    def validate_value(self, value: Any) -> bool:
        if not isinstance(value, (int, float)):
            return False
        
        return self.metadata.min_value <= value <= self.metadata.max_value

    def serialize_value(self, value: Any) -> float:
        return float(value)

    def deserialize_value(self, serialized_value: Any) -> float:
        return float(serialized_value)


@dataclass
class SettingsGroup:
    name: str
    display_name: str
    description: str
    settings: Dict[str, SettingDefinition]


class Settings:
    def __init__(self, groups: Dict[str, SettingsGroup]):
        self._groups = groups
        self._values: Dict[str, Any] = {}
        self._load_defaults()

    def _load_defaults(self):
        for group in self._groups.values():
            for setting_key, setting_def in group.settings.items():
                self._values[setting_key] = setting_def.metadata.default_value

    def get_value(self, key: str) -> Any:
        return self._values.get(key)

    def set_value(self, key: str, value: Any) -> bool:
        setting_def = self._find_setting_definition(key)
        if not setting_def:
            return False
        
        if not setting_def.validate_value(value):
            return False
        
        self._values[key] = value
        return True

    def get_all_values(self) -> Dict[str, Any]:
        return self._values.copy()

    def update_values(self, values: Dict[str, Any]) -> Dict[str, bool]:
        results = {}
        for key, value in values.items():
            results[key] = self.set_value(key, value)
        return results

    def get_groups(self) -> Dict[str, SettingsGroup]:
        return self._groups

    def _find_setting_definition(self, key: str) -> Optional[SettingDefinition]:
        for group in self._groups.values():
            if key in group.settings:
                return group.settings[key]
        return None

    def serialize(self) -> Dict[str, Any]:
        serialized = {}
        for key, value in self._values.items():
            setting_def = self._find_setting_definition(key)
            if setting_def:
                serialized[key] = setting_def.serialize_value(value)
        return serialized

    def deserialize(self, data: Dict[str, Any]) -> None:
        for key, serialized_value in data.items():
            setting_def = self._find_setting_definition(key)
            if setting_def:
                try:
                    value = setting_def.deserialize_value(serialized_value)
                    if setting_def.validate_value(value):
                        self._values[key] = value
                except (ValueError, TypeError):
                    continue