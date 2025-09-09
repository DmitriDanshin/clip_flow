from dataclasses import dataclass
from typing import Any, Optional

from .setting_type import SettingType


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