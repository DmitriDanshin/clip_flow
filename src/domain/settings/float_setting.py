from typing import Any

from .setting_definition import SettingDefinition


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