from typing import Any

from .setting_definition import SettingDefinition
from .setting_metadata import SettingMetadata


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