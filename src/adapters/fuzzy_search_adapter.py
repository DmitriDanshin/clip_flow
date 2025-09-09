import fuzzysearch
from loguru import logger
from src.ports.search_port import SearchPort
from src.domain.models import ClipboardItem


class FuzzySearchAdapter(SearchPort):
    def __init__(
        self,
        max_substitutions: int = None,
        max_insertions: int = None,
        max_deletions: int = None,
        max_l_dist: int = 1,
        case_sensitive: bool = False,
    ):
        self.max_substitutions = max_substitutions
        self.max_insertions = max_insertions
        self.max_deletions = max_deletions
        self.max_l_dist = max_l_dist
        self.case_sensitive = case_sensitive
        logger.debug(
            f"FuzzySearchAdapter initialized with max_substitutions={max_substitutions}, "
            f"max_insertions={max_insertions}, max_deletions={max_deletions}, "
            f"max_l_dist={max_l_dist}, case_sensitive={case_sensitive}"
        )

    def search(self, items: list[ClipboardItem], query: str) -> list[ClipboardItem]:
        if not query:
            return items.copy()

        results = [item for item in items if self.is_match(item, query)]
        logger.debug(
            f"Fuzzy search query '{query}' returned {len(results)} results from {len(items)} items."
        )
        return results

    def is_match(self, item: ClipboardItem, query: str) -> bool:
        if not query:
            return True

        content = item.content if self.case_sensitive else item.content.lower()
        search_query = query if self.case_sensitive else query.lower()

        if len(search_query) <= 2:
            return search_query in content

        fuzzy_content = item.content if self.case_sensitive else content
        fuzzy_query = query if self.case_sensitive else search_query

        return bool(
            fuzzysearch.find_near_matches(
                fuzzy_query,
                fuzzy_content,
                max_substitutions=self.max_substitutions,
                max_insertions=self.max_insertions,
                max_deletions=self.max_deletions,
                max_l_dist=self.max_l_dist,
            )
        )
