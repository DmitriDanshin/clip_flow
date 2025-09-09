from dataclasses import dataclass
from typing import Dict

from .setting_definition import SettingDefinition


@dataclass
class SettingsGroup:
    name: str
    display_name: str
    description: str
    settings: Dict[str, SettingDefinition]