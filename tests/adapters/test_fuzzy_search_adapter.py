import pytest
from datetime import datetime
from unittest.mock import Mock
from src.adapters.fuzzy_search_adapter import FuzzySearchAdapter
from src.domain.clipboard import ClipboardItem
from src.domain.settings.app_settings import create_app_settings
from src.application.settings_service import SettingsService


class TestFuzzySearchAdapter:
    @pytest.fixture
    def mock_settings_service(self):
        settings = create_app_settings()
        mock_repository = Mock()
        mock_repository.exists.return_value = False
        return SettingsService(repository=mock_repository, settings=settings)
    
    @pytest.fixture
    def adapter(self, mock_settings_service):
        return FuzzySearchAdapter(settings_service=mock_settings_service)

    @pytest.fixture
    def sample_items(self):
        return [
            ClipboardItem(content="Hello World", created_at=datetime.now()),
            ClipboardItem(content="Python Programming", created_at=datetime.now()),
            ClipboardItem(content="Testing Code", created_at=datetime.now()),
            ClipboardItem(content="FuzzySearch Example", created_at=datetime.now()),
            ClipboardItem(content="Quick Brown Fox", created_at=datetime.now()),
        ]

    def test_empty_query_returns_all_items(self, adapter, sample_items):
        results = adapter.search(sample_items, "")
        assert len(results) == len(sample_items)
        assert results == sample_items

    def test_single_character_search(self, adapter, sample_items):
        results = adapter.search(sample_items, "P")
        assert len(results) == 2
        assert any("Python Programming" in item.content for item in results)
        assert any("FuzzySearch Example" in item.content for item in results)

    def test_two_character_search(self, adapter, sample_items):
        results = adapter.search(sample_items, "Qu")
        assert len(results) == 1
        assert results[0].content == "Quick Brown Fox"

    def test_exact_match_long_query(self, adapter, sample_items):
        results = adapter.search(sample_items, "Hello")
        assert len(results) == 1
        assert results[0].content == "Hello World"

    def test_fuzzy_match_with_typo(self, adapter, sample_items):
        results = adapter.search(sample_items, "Helo")  # Missing 'l'
        assert len(results) == 1
        assert results[0].content == "Hello World"

    def test_fuzzy_match_substitution(self, adapter, sample_items):
        results = adapter.search(sample_items, "Pythom")  # 'n' -> 'm'
        assert len(results) == 1
        assert results[0].content == "Python Programming"

    def test_no_matches_found(self, adapter, sample_items):
        results = adapter.search(sample_items, "XYZ123")
        assert len(results) == 0

    def test_case_insensitive_search(self, adapter, sample_items):
        results = adapter.search(sample_items, "hello")
        assert len(results) == 1
        assert results[0].content == "Hello World"

    def test_is_match_empty_query(self, adapter):
        item = ClipboardItem(content="Test", created_at=datetime.now())
        assert adapter.is_match(item, "") is True

    def test_is_match_short_query(self, adapter):
        item = ClipboardItem(content="Hello World", created_at=datetime.now())
        assert adapter.is_match(item, "H") is True
        assert adapter.is_match(item, "He") is True
        assert adapter.is_match(item, "XY") is False

    def test_is_match_long_query_exact(self, adapter):
        item = ClipboardItem(content="Hello World", created_at=datetime.now())
        assert adapter.is_match(item, "Hello") is True
        assert adapter.is_match(item, "World") is True

    def test_is_match_long_query_fuzzy(self, adapter):
        item = ClipboardItem(content="Hello World", created_at=datetime.now())
        assert adapter.is_match(item, "Helo") is True  # Missing 'l'
        assert adapter.is_match(item, "Wrld") is True  # Missing 'o'
        assert adapter.is_match(item, "Hxllo") is True  # 'e' -> 'x'

    def test_is_match_too_many_errors(self, adapter):
        item = ClipboardItem(content="Hello", created_at=datetime.now())

        assert adapter.is_match(item, "Hexo") is False

    def test_initialization_parameters(self, mock_settings_service):
        # Update the settings
        mock_settings_service.update_setting("fuzzy_search.max_l_dist", 2)
        mock_settings_service.update_setting("fuzzy_search.case_sensitive", True)
        
        adapter = FuzzySearchAdapter(settings_service=mock_settings_service)
        assert adapter.max_l_dist == 2
        assert adapter.case_sensitive is True

    def test_default_parameters(self, mock_settings_service):
        adapter = FuzzySearchAdapter(settings_service=mock_settings_service)
        assert adapter.max_l_dist == 1  # default from app_settings.py
        assert adapter.case_sensitive is False  # default from app_settings.py
