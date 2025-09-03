import json
import sys
from pathlib import Path
from typing import Dict, List, Any, Optional
from loguru import logger
from src.ports.settings_schema_port import SettingsSchemaPort


class JsonSettingsSchemaAdapter(SettingsSchemaPort):
    def __init__(self, schema_path: str = "settings_schema.json"):
        self.schema_path = Path(schema_path)
        self._schema = None
        self._load_schema()

    def _resolve_runtime_path(self) -> Path:
        if getattr(sys, "frozen", False) and hasattr(sys, "_MEIPASS"):
            base_dir = Path(sys._MEIPASS)
        else:
            base_dir = Path.cwd()

        if self.schema_path.is_absolute():
            return self.schema_path
        return base_dir / self.schema_path

    def _load_schema(self):
        path = self._resolve_runtime_path()
        try:
            with open(path, "r", encoding="utf-8") as f:
                self._schema = json.load(f)
            logger.debug(f"Settings schema loaded from {path}")
        except FileNotFoundError:
            logger.error(f"Settings schema file not found: {path}")
            self._schema = {"categories": []}
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON in settings schema: {e}")
            self._schema = {"categories": []}

    def get_categories(self) -> List[Dict[str, Any]]:
        return self._schema.get("categories", [])

    def get_category(self, key: str) -> Optional[Dict[str, Any]]:
        for category in self.get_categories():
            if category.get("key") == key:
                return category
        return None

    def get_setting_definition(self, setting_key: str) -> Optional[Dict[str, Any]]:
        for category in self.get_categories():
            for setting in category.get("settings", []):
                if setting.get("key") == setting_key:
                    return setting
        return None

    def get_default_value(self, setting_key: str) -> Any:
        definition = self.get_setting_definition(setting_key)
        if definition:
            return definition.get("default")
        return None

    def get_all_defaults(self) -> Dict[str, Any]:
        defaults = {}
        categories = self.get_categories()
        logger.debug(f"Processing {len(categories)} categories for defaults")

        for category in categories:
            category_key = category.get("key", "unknown")
            settings = category.get("settings", [])
            logger.debug(f"Category '{category_key}' has {len(settings)} settings")

            for setting in settings:
                key = setting.get("key")
                if key and "default" in setting:
                    defaults[key] = setting["default"]
                    logger.debug(f"Added default for '{key}': {setting['default']}")

        logger.debug(f"Total defaults collected: {defaults}")
        return defaults

    def validate_setting_value(self, setting_key: str, value: Any) -> bool:
        definition = self.get_setting_definition(setting_key)
        if not definition:
            return False

        setting_type = definition.get("type")

        if setting_type == "checkbox":
            return isinstance(value, bool)
        elif setting_type in ["slider", "spinbox"]:
            if not isinstance(value, (int, float)):
                return False
            min_val = definition.get("min")
            max_val = definition.get("max")
            if min_val is not None and value < min_val:
                return False
            if max_val is not None and value > max_val:
                return False
            return True
        elif setting_type == "select":
            options = definition.get("options", [])
            return value in options
        elif setting_type == "text":
            return isinstance(value, str)

        return True
