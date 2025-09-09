from typing import Dict, Any, Optional

from .settings_group import SettingsGroup
from .setting_definition import SettingDefinition


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