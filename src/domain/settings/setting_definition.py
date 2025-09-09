from abc import ABC, abstractmethod
from typing import Any

from .setting_metadata import SettingMetadata


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
