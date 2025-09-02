from abc import ABC, abstractmethod
from typing import List
from ..domain.models import ClipboardItem


class SearchPort(ABC):
    @abstractmethod
    def search(self, items: List[ClipboardItem], query: str) -> List[ClipboardItem]:
        """Search through items using the provided query."""

    @abstractmethod
    def is_match(self, item: ClipboardItem, query: str) -> bool:
        """Check if a single item matches the search query."""
