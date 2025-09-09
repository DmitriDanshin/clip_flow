from dataclasses import dataclass
from typing import List
from datetime import datetime

from src.domain.clipboard.clipboard_item import ClipboardItem


@dataclass
class ClipboardHistory:
    items: List[ClipboardItem]
    max_items: int = 1000

    def __post_init__(self):
        if self.max_items <= 0:
            raise ValueError("Max items must be positive")
        self._enforce_limit()

    def add_item(self, content: str) -> None:
        if not content:
            return

        self.items = [item for item in self.items if item.content != content]

        new_item = ClipboardItem(content=content, created_at=datetime.now())
        self.items.insert(0, new_item)

        self._enforce_limit()

    def clear(self) -> None:
        self.items.clear()

    def remove_item_by_index(self, index: int) -> bool:
        if 0 <= index < len(self.items):
            self.items.pop(index)
            return True
        return False

    def get_content_list(self) -> List[str]:
        return [item.content for item in self.items]

    def _enforce_limit(self) -> None:
        if len(self.items) > self.max_items:
            self.items = self.items[: self.max_items]