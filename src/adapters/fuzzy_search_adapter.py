import fuzzysearch
from loguru import logger
from src.ports.search_port import SearchPort
from src.ports.settings_port import SettingsServicePort
from src.domain.clipboard import ClipboardItem


class FuzzySearchAdapter(SearchPort):
    def __init__(self, settings_service: SettingsServicePort):
        self._settings_service = settings_service
        logger.debug("FuzzySearchAdapter initialized with settings service")

    @property
    def max_substitutions(self) -> int:
        return self._settings_service.get_settings().get_value("fuzzy_search.max_substitutions")

    @property
    def max_insertions(self) -> int:
        return self._settings_service.get_settings().get_value("fuzzy_search.max_insertions")

    @property
    def max_deletions(self) -> int:
        return self._settings_service.get_settings().get_value("fuzzy_search.max_deletions")

    @property
    def max_l_dist(self) -> int:
        return self._settings_service.get_settings().get_value("fuzzy_search.max_l_dist")

    @property
    def case_sensitive(self) -> bool:
        return self._settings_service.get_settings().get_value("fuzzy_search.case_sensitive")

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
