import json
import os
from datetime import datetime
from loguru import logger
from src.ports.storage_port import StoragePort
from src.domain.models import ClipboardHistory, ClipboardItem


class JsonStorageAdapter(StoragePort):
    def __init__(self, file_path: str = "clipboard_history.json"):
        self.file_path = file_path
        logger.debug(f"JsonStorageAdapter initialized with file: {file_path}")

    def save_history(self, history: ClipboardHistory) -> None:
        try:
            data = []
            for item in history.items:
                data.append(
                    {"content": item.content, "created_at": item.created_at.isoformat()}
                )

            with open(self.file_path, "w", encoding="utf-8") as f:
                json.dump(
                    {"max_items": history.max_items, "items": data},
                    f,
                    ensure_ascii=False,
                    indent=2,
                )

            logger.trace(f"Saved {len(history.items)} items to {self.file_path}")
        except IOError as e:
            logger.error(f"Error saving history to file: {e}")

    def load_history(self) -> ClipboardHistory:
        try:
            if not os.path.exists(self.file_path):
                logger.info(
                    "No existing history file found, starting with empty history."
                )
                return ClipboardHistory(items=[])

            with open(self.file_path, "r", encoding="utf-8") as f:
                data = json.load(f)

            if not isinstance(data, dict):
                logger.warning(
                    "Invalid history file format, starting with empty history."
                )
                return ClipboardHistory(items=[])

            max_items = data.get("max_items", 1000)
            items_data = data.get("items", [])

            items = []
            for item_data in items_data:
                try:
                    created_at = datetime.fromisoformat(
                        item_data.get("created_at", datetime.now().isoformat())
                    )
                    item = ClipboardItem(
                        content=item_data["content"], created_at=created_at
                    )
                    items.append(item)
                except (KeyError, ValueError) as e:
                    logger.warning(f"Skipping invalid history item: {e}")
                    continue

            history = ClipboardHistory(items=items, max_items=max_items)
            logger.info(f"Loaded {len(items)} items from history file.")
            return history

        except (json.JSONDecodeError, IOError) as e:
            logger.error(f"Error loading history from file: {e}")
            logger.info("Starting with empty history.")
            return ClipboardHistory(items=[])

    def clear_storage(self) -> None:
        try:
            if os.path.exists(self.file_path):
                os.remove(self.file_path)
                logger.info(f"Storage file {self.file_path} deleted.")
        except IOError as e:
            logger.error(f"Error deleting storage file: {e}")
