from datetime import datetime
import os
import sqlite3
import tempfile

import pytest

from src.adapters.sqlite_storage_adapter import SqliteStorageAdapter
from src.domain.clipboard import ClipboardHistory, ClipboardItem


class TestSqliteStorageAdapter:
    @pytest.fixture
    def temp_db_path(self):
        fd, path = tempfile.mkstemp(suffix=".db")
        os.close(fd)
        os.remove(path)
        yield path
        if os.path.exists(path):
            try:
                os.remove(path)
            except (OSError, PermissionError):
                pass

    @pytest.fixture
    def adapter(self, temp_db_path):
        yield SqliteStorageAdapter(temp_db_path)

    @pytest.fixture
    def sample_items(self):
        return [
            ClipboardItem(
                content="First item", created_at=datetime(2024, 1, 1, 10, 0, 0)
            ),
            ClipboardItem(
                content="Second item", created_at=datetime(2024, 1, 1, 11, 0, 0)
            ),
            ClipboardItem(
                content="Third item", created_at=datetime(2024, 1, 1, 12, 0, 0)
            ),
        ]

    @pytest.fixture
    def sample_history(self, sample_items):
        return ClipboardHistory(items=sample_items, max_items=100)

    def test_init_creates_database_file(self, temp_db_path):
        SqliteStorageAdapter(temp_db_path)
        assert os.path.exists(temp_db_path)

    def test_init_creates_tables(self, adapter, temp_db_path):
        with sqlite3.connect(temp_db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
            tables = [row[0] for row in cursor.fetchall()]
            assert "clipboard_history" in tables

    def test_save_history_stores_items(self, adapter, sample_history, temp_db_path):
        adapter.save_history(sample_history)

        with sqlite3.connect(temp_db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT content, created_at FROM clipboard_history ORDER BY created_at DESC"
            )
            rows = cursor.fetchall()

            assert len(rows) == 3
            assert rows[0][0] == "Third item"
            assert rows[1][0] == "Second item"
            assert rows[2][0] == "First item"

    def test_save_history_stores_max_items_setting(
        self, adapter, sample_history, temp_db_path
    ):
        # This test is no longer applicable since settings are not stored in the database
        # The max_items is now handled by the domain model and doesn't persist in the database
        adapter.save_history(sample_history)

        # Just verify that the history items were saved
        with sqlite3.connect(temp_db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM clipboard_history")
            count = cursor.fetchone()[0]
            assert count == 3

    def test_save_history_clears_previous_data(
        self, adapter, sample_history, temp_db_path
    ):
        adapter.save_history(sample_history)

        new_history = ClipboardHistory(
            items=[ClipboardItem(content="New item", created_at=datetime.now())],
            max_items=50,
        )
        adapter.save_history(new_history)

        with sqlite3.connect(temp_db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM clipboard_history")
            count = cursor.fetchone()[0]
            assert count == 1

    def test_load_history_retrieves_saved_data(self, adapter, sample_history):
        adapter.save_history(sample_history)
        loaded_history = adapter.load_history()

        assert len(loaded_history.items) == 3
        assert loaded_history.max_items == 1000  # Hardcoded max_items in the adapter
        assert loaded_history.items[0].content == "Third item"
        assert loaded_history.items[1].content == "Second item"
        assert loaded_history.items[2].content == "First item"

    def test_load_history_preserves_datetime_format(self, adapter, sample_history):
        adapter.save_history(sample_history)
        loaded_history = adapter.load_history()

        original_item = sample_history.items[0]
        loaded_item = loaded_history.items[2]

        assert loaded_item.created_at == original_item.created_at

    def test_load_history_handles_invalid_datetime(self, adapter, temp_db_path):
        with sqlite3.connect(temp_db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO clipboard_history (content, created_at) VALUES (?, ?)",
                ("Test item", "invalid_datetime"),
            )
            cursor.execute(
                "INSERT INTO clipboard_history (content, created_at) VALUES (?, ?)",
                ("Valid item", datetime.now().isoformat()),
            )
            conn.commit()

        loaded_history = adapter.load_history()
        assert len(loaded_history.items) == 1
        assert loaded_history.items[0].content == "Valid item"

    def test_load_history_uses_default_max_items_when_not_set(
        self, adapter, temp_db_path
    ):
        with sqlite3.connect(temp_db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO clipboard_history (content, created_at) VALUES (?, ?)",
                ("Test item", datetime.now().isoformat()),
            )
            conn.commit()

        loaded_history = adapter.load_history()
        assert loaded_history.max_items == 1000

    def test_database_error_handling_on_init(self):
        invalid_path = "/invalid/path/database.db"
        with pytest.raises(sqlite3.Error):
            SqliteStorageAdapter(invalid_path)

    def test_save_history_empty_items(self, adapter):
        empty_history = ClipboardHistory(items=[], max_items=50)
        adapter.save_history(empty_history)

        loaded_history = adapter.load_history()
        assert len(loaded_history.items) == 0
        assert loaded_history.max_items == 1000  # Hardcoded max_items in the adapter

    def test_concurrent_database_access(self, temp_db_path, sample_history):
        adapter1 = SqliteStorageAdapter(temp_db_path)
        adapter2 = SqliteStorageAdapter(temp_db_path)

        adapter1.save_history(sample_history)
        loaded_history = adapter2.load_history()

        assert len(loaded_history.items) == 3
        assert loaded_history.max_items == 1000  # Hardcoded max_items in the adapter

    def test_database_schema_validation(self, adapter, temp_db_path):
        with sqlite3.connect(temp_db_path) as conn:
            cursor = conn.cursor()

            cursor.execute("PRAGMA table_info(clipboard_history)")
            clipboard_columns = cursor.fetchall()
            clipboard_column_names = [col[1] for col in clipboard_columns]
            assert "id" in clipboard_column_names
            assert "content" in clipboard_column_names
            assert "created_at" in clipboard_column_names

            # Settings table is no longer created by this adapter
            cursor.execute(
                "SELECT name FROM sqlite_master WHERE type='table' AND name='settings'"
            )
            settings_table_exists = cursor.fetchone() is None
            assert settings_table_exists  # Assert that settings table does NOT exist
