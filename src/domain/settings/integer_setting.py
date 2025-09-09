from typing import Any

from .setting_definition import SettingDefinition


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