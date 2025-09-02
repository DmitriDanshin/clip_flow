import pyperclip
import time
import threading
from typing import Callable
from loguru import logger
from src.ports.clipboard_port import ClipboardPort


class PyperclipAdapter(ClipboardPort):
    def __init__(self):
        self._callback: Callable[[str], None] | None = None
        self._stop_event = threading.Event()
        self._monitor_thread: threading.Thread | None = None
        self._last_value = ""
        logger.debug("PyperclipAdapter initialized.")

    def get_content(self) -> str:
        try:
            return pyperclip.paste()
        except pyperclip.PyperclipException as e:
            logger.warning(f"Could not read clipboard content: {e}")
            return ""

    def set_content(self, content: str) -> None:
        try:
            pyperclip.copy(content)
            logger.debug(f"Copied to clipboard: '{content[:30]}...'")
        except pyperclip.PyperclipException as e:
            logger.error(f"Could not copy to clipboard: {e}")

    def start_monitoring(self, callback: Callable[[str], None]) -> None:
        self._callback = callback
        self._stop_event.clear()

        if self._monitor_thread and self._monitor_thread.is_alive():
            logger.warning("Clipboard monitoring already running.")
            return

        self._monitor_thread = threading.Thread(
            target=self._monitor_clipboard, daemon=True
        )
        self._monitor_thread.start()
        logger.info("Clipboard monitoring started.")

    def stop_monitoring(self) -> None:
        logger.info("Stopping clipboard monitoring.")
        self._stop_event.set()
        if self._monitor_thread and self._monitor_thread.is_alive():
            self._monitor_thread.join()
            logger.debug("Monitoring thread joined successfully.")

    def _monitor_clipboard(self) -> None:
        logger.info("Clipboard monitoring thread started.")

        try:
            self._last_value = self.get_content()
            if self._last_value and self._callback:
                logger.debug(
                    f"Initial clipboard content found: '{self._last_value[:30]}...'"
                )
                self._callback(self._last_value)
        except Exception as e:
            logger.warning(f"Could not read initial clipboard content: {e}")
            self._last_value = ""

        while not self._stop_event.is_set():
            try:
                current_value = self.get_content()
                if current_value != self._last_value:
                    logger.debug("New clipboard value detected.")
                    self._last_value = current_value
                    if self._callback:
                        self._callback(current_value)
            except Exception as e:
                logger.warning(f"Error monitoring clipboard: {e}")
                time.sleep(5)
                continue

            time.sleep(1)

        logger.info("Clipboard monitoring thread stopped.")
