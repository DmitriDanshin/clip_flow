from __future__ import annotations

from typing import TYPE_CHECKING, Dict, Any


if TYPE_CHECKING:
    from src.adapters.ui.pywebview_ui_adapter import PyWebViewUIAdapter


class JavaScriptAPI:
    def __init__(self, ui: PyWebViewUIAdapter):
        self._ui = ui

    def on_search(self, query: str) -> None:
        self._ui.handle_js_search(query)

    def on_copy(self, index: int) -> None:
        self._ui.handle_js_copy(int(index))

    def on_clear(self) -> None:
        self._ui.handle_js_clear()

    def on_delete(self, index: int) -> None:
        self._ui.handle_js_delete(int(index))

    def on_ready(self) -> None:
        self._ui.handle_js_ready()

    def get_settings_metadata(self) -> Dict[str, Any]:
        return self._ui.handle_js_get_settings_metadata()

    def get_settings_values(self) -> Dict[str, Any]:
        return self._ui.handle_js_get_settings_values()

    def update_setting(self, key: str, value: Any) -> bool:
        return self._ui.handle_js_update_setting(key, value)

    def save_settings(self) -> bool:
        return self._ui.handle_js_save_settings()

