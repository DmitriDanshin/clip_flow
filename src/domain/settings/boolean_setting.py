from typing import Any

from .setting_definition import SettingDefinition


class BooleanSetting(SettingDefinition):
    def validate_value(self, value: Any) -> bool:
        return isinstance(value, bool)

    def serialize_value(self, value: Any) -> bool:
        return bool(value)

    def deserialize_value(self, serialized_value: Any) -> bool:
        return bool(serialized_value)
