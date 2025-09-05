from __future__ import annotations

from typing import TYPE_CHECKING

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

    def on_ready(self) -> None:
        self._ui.handle_js_ready()

    def show_settings(self) -> None:
        self._ui.show_settings_window()

    def get_settings_schema(self) -> str:
        return self._ui.get_settings_schema()

    def get_current_settings(self) -> str:
        return self._ui.get_current_settings()

    def save_settings(self, settings_json: str) -> None:
        self._ui.save_settings_from_json(settings_json)
