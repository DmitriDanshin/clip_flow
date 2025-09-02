import pytest
from datetime import datetime
from src.adapters.fuzzy_search_adapter import FuzzySearchAdapter
from src.domain.models import ClipboardItem


class TestFuzzySearchAdapter:
    @pytest.fixture
    def adapter(self):
        return FuzzySearchAdapter(max_l_dist=1, case_sensitive=False)
    

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
    
    def test_initialization_parameters(self):
        adapter = FuzzySearchAdapter(max_l_dist=2, case_sensitive=True)
        assert adapter.max_l_dist == 2
        assert adapter.case_sensitive is True
    
    def test_default_parameters(self):
        adapter = FuzzySearchAdapter()
        assert adapter.max_l_dist == 1
        assert adapter.case_sensitive is False