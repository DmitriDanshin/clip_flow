from typing import List
from loguru import logger
from ..domain.models import ClipboardHistory
from ..ports.clipboard_port import ClipboardPort
from ..ports.storage_port import StoragePort
from ..ports.ui_port import UIPort
from ..ports.search_port import SearchPort


class ClipboardService:
    def __init__(
        self,
        clipboard_port: ClipboardPort,
        storage_port: StoragePort,
        ui_port: UIPort,
        search_port: SearchPort,
    ):
        self.clipboard_port = clipboard_port
        self.storage_port = storage_port
        self.ui_port = ui_port
        self.search_port = search_port
        self.history: ClipboardHistory = ClipboardHistory(items=[])

        self.ui_port.register_copy_callback(self._on_copy_item)
        self.ui_port.register_search_callback(self._on_search)
        self.ui_port.register_clear_callback(self._on_clear_history)

        self._current_filtered_items: List[str] = []

        logger.debug("ClipboardService initialized.")

    def start(self) -> None:
        self.history = self.storage_port.load_history()
        logger.info(f"Loaded {len(self.history.items)} items from storage.")

        self.clipboard_port.start_monitoring(self._on_clipboard_change)

        self._update_ui_display()

        self.ui_port.run()

        logger.info("ClipboardService started.")

    def stop(self) -> None:
        self.clipboard_port.stop_monitoring()
        self.ui_port.shutdown()
        logger.info("ClipboardService stopped.")

    def _on_clipboard_change(self, content: str) -> None:
        if content:
            logger.debug(f"Clipboard changed: '{content[:30]}...'")
            self.history.add_item(content)
            self.storage_port.save_history(self.history)
            self._update_ui_display()

    def _on_copy_item(self, index: int) -> None:
        if 0 <= index < len(self._current_filtered_items):
            content = self._current_filtered_items[index]
            self.clipboard_port.set_content(content)
            self.ui_port.show_message("Item copied to clipboard!")
            logger.info(f"Copied item at index {index} to clipboard.")
        else:
            logger.warning(f"Invalid copy index: {index}")

    def _on_search(self, query: str) -> None:
        filtered_items = self.search_port.search(self.history.items, query)
        self._current_filtered_items = [item.content for item in filtered_items]
        self.ui_port.show_history(self._current_filtered_items)
        logger.debug(f"Search query '{query}' returned {len(filtered_items)} results.")

    def _on_clear_history(self) -> None:
        self.history.clear()
        self.storage_port.clear_storage()
        self._update_ui_display()
        self.ui_port.show_message("Clipboard history cleared!")
        logger.info("Clipboard history cleared.")

    def _update_ui_display(self) -> None:
        content_list = self.history.get_content_list()
        self._current_filtered_items = content_list
        self.ui_port.show_history(content_list)
