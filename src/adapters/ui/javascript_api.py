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

    def on_delete(self, index: int) -> None:
        self._ui.handle_js_delete(int(index))

    def on_ready(self) -> None:
        self._ui.handle_js_ready()

