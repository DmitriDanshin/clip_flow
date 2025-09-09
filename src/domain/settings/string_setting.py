from typing import Any

from .setting_definition import SettingDefinition


class StringSetting(SettingDefinition):
    def validate_value(self, value: Any) -> bool:
        return isinstance(value, str)

    def serialize_value(self, value: Any) -> str:
        return str(value)

    def deserialize_value(self, serialized_value: Any) -> str:
        return str(serialized_value)
