
import json
from typing import Callable

from loguru import logger

import webview
from src.ports.ui_port import UIPort
from src.adapters.ui.javascript_api import JavaScriptAPI
from src.utils.assets import asset_uri as get_asset_uri


class PyWebViewUIAdapter(UIPort):
    def __init__(self):
        if webview is None:
            raise RuntimeError(
                "pywebview is not installed. Please `pip install pywebview`."
            )

        self.window: webview.Window | None = None
        self._api = JavaScriptAPI(self)

        self._copy_callback: Callable[[int], None] | None = None
        self._search_callback: Callable[[int | str], None] | None = None
        self._clear_callback: Callable[[int], None] | None = None
        self._delete_callback: Callable[[int], None] | None = None
        self._hide_callback: Callable[[int], None] | None = None

        self._current_items: list[str] = []
        self._is_hidden = False
        self._js_ready = False
        self._pending_history: list[str] | None = None
        self._request_focus = False

        logger.debug("PyWebViewUIAdapter initialized.")

    def show_history(self, items: list[str]) -> None:
        logger.debug(f"show_history called with {len(items)} items")
        logger.debug(f"JS ready state: {self._js_ready}")
        self._current_items = items.copy()

        if self._js_ready:
            logger.debug("JS is ready, pushing history to webview")
            self._push_history_to_webview()
        else:
            logger.debug("JS not ready, storing in pending history")
            self._pending_history = self._current_items.copy()

    def show_message(self, message: str, message_type: str = "info") -> None:
        if not self.window:
            logger.debug("show_message called before window is ready; skipping")
            return

        payload = json.dumps({"message": message, "type": message_type})

        self._evaluate_js(f"window.showMessage({payload});")

    def run(self) -> None:
        logger.info("Starting PyWebView UI.")

        uri = get_asset_uri('index.html')
        if not uri:
            raise RuntimeError("assets/index.html not found. Build frontend via 'python scripts/build_frontend.py'.")

        logger.debug(f"Loading UI from assets: {uri}")
        self.window = webview.create_window(
            title="Clip Flow",
            url=uri,
            width=400,
            height=600,
            resizable=True,
            easy_drag=False,
            js_api=self._api,
            on_top=False,
            minimized=False,
        )

        self.window.events.closing += self._on_window_closing
        
        webview.start(self._after_start, debug=False)

    def register_copy_callback(self, callback: Callable[[int], None]) -> None:
        self._copy_callback = callback

    def register_search_callback(self, callback: Callable[[str], None]) -> None:
        self._search_callback = callback

    def register_clear_callback(self, callback: Callable[[], None]) -> None:
        self._clear_callback = callback

    def register_delete_callback(self, callback: Callable[[int], None]) -> None:
        self._delete_callback = callback

    def register_hide_callback(self, callback: Callable[[], None]) -> None:
        self._hide_callback = callback

    def handle_js_search(self, query: str) -> None:
        if self._search_callback:
            self._search_callback(query)

    def handle_js_copy(self, index: int) -> None:
        if self._copy_callback:
            self._copy_callback(index)
        self.hide_window()
        if self._hide_callback:
            self._hide_callback()

    def handle_js_clear(self) -> None:
        if self._clear_callback:
            self._clear_callback()

    def handle_js_delete(self, index: int) -> None:
        if self._delete_callback:
            self._delete_callback(index)

    def handle_js_ready(self) -> None:
        self._mark_js_ready()

    def show_window(self) -> None:
        if not self.window:
            return

        # Сначала показываем окно, затем восстанавливаем и фокусируемся
        self.window.show()
        self.window.restore()
        self.window.on_top = True
        self.window.on_top = False  # Сбрасываем on_top для нормального поведения

        if self._js_ready:
            self._evaluate_js("window.focusSearch();")
        else:
            self._request_focus = True

        self._is_hidden = False
        logger.debug("Window shown and focused")

    def hide_window(self) -> None:
        self._is_hidden = True
        if not self.window:
            return

        self.window.hide()

        logger.debug("Window hidden to system tray")

    def shutdown(self) -> None:
        if self.window:
            self.window.destroy()


    def _push_history_to_webview(self) -> None:
        if not self.window:
            return

        data = json.dumps(self._current_items)
        logger.debug(f"Pushing {len(self._current_items)} items to WebView")
        exists = self._evaluate_js("typeof updateHistory === 'function' ? 'ok' : 'missing'")

        if exists != 'ok':
            exists_win = self._evaluate_js("typeof window.updateHistory === 'function' ? 'ok' : 'missing'")
            logger.debug(f"updateHistory availability: global={exists}, window={exists_win}")
            if exists_win == 'ok':
                self._evaluate_js(f"window.updateHistory({data});")
                return

        self._evaluate_js(f"updateHistory({data});")

    def _evaluate_js(self, script: str):
        try:
            if self.window:
                short = script if len(script) < 120 else script[:117] + "..."
                logger.debug(f"Evaluating JS: {short}")
                return self.window.evaluate_js(script)
        except Exception as exception:
            logger.debug(f"evaluate_js failed: {exception}")
        return None

    def _after_start(self) -> None:
        if self._is_hidden:
            self.hide_window()
        elif self._js_ready:
            self._evaluate_js("window.focusSearch();")
        else:
            self._request_focus = True

    def _mark_js_ready(self) -> None:
        if self._js_ready:
            return

        self._js_ready = True

        logger.debug("JS context is ready")
        logger.debug(f"Pending history items: {len(self._pending_history) if self._pending_history else 0}")

        if self._pending_history is not None:
            logger.debug(f"Processing pending history with {len(self._pending_history)} items")
            self._current_items = self._pending_history
            self._pending_history = None
            self._push_history_to_webview()
        else:
            logger.debug("No pending history to process")

        if self._request_focus:
            self._request_focus = False
            self._evaluate_js("window.focusSearch();")

    def _on_window_closing(self) -> None:
        logger.debug("Window closing event triggered - hiding to system tray")
        self.hide_window()
        if self._hide_callback:
            self._hide_callback()
        return False
