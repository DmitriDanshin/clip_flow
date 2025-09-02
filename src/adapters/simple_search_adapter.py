from typing import List
from loguru import logger
from ..ports.search_port import SearchPort
from ..domain.models import ClipboardItem


class SimpleSearchAdapter(SearchPort):
    def __init__(self, case_sensitive: bool = False):
        self.case_sensitive = case_sensitive
        logger.debug(
            f"SimpleSearchAdapter initialized with case_sensitive={case_sensitive}"
        )

    def search(self, items: List[ClipboardItem], query: str) -> List[ClipboardItem]:
        if not query:
            return items.copy()

        results = [item for item in items if self.is_match(item, query)]
        logger.debug(
            f"Search query '{query}' returned {len(results)} results from {len(items)} items."
        )
        return results

    def is_match(self, item: ClipboardItem, query: str) -> bool:
        if not query:
            return True

        content = item.content if self.case_sensitive else item.content.lower()
        search_query = query if self.case_sensitive else query.lower()

        return search_query in content
