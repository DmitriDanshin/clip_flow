from datetime import datetime
import os
import sqlite3

from loguru import logger

from src.domain.clipboard import ClipboardHistory, ClipboardItem
from src.infrastructure.system_paths import (
    ensure_directories_exist,
    get_database_file_path,
)
from src.ports.storage_port import StoragePort


class SqliteStorageAdapter(StoragePort):
    def __init__(self, db_path: str = None):
        if db_path is None:
            ensure_directories_exist()
            self.db_path = str(get_database_file_path())
        else:
            self.db_path = db_path
        self._init_database()
        logger.info(f"Database configured successfully. Database file: {self.db_path}")

    def _init_database(self) -> None:
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS clipboard_history (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        content TEXT NOT NULL,
                        created_at TEXT NOT NULL
                    )
                """)
                conn.commit()
                logger.trace("Database initialized successfully")
        except sqlite3.Error as e:
            logger.error(f"Error initializing database: {e}")
            raise

    def save_history(self, history: ClipboardHistory) -> None:
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()

                cursor.execute("DELETE FROM clipboard_history")

                for item in history.items:
                    cursor.execute(
                        "INSERT INTO clipboard_history (content, created_at) VALUES (?, ?)",
                        (item.content, item.created_at.isoformat()),
                    )

                conn.commit()
                logger.trace(f"Saved {len(history.items)} items to database")
        except sqlite3.Error as e:
            # TODO: Add tests
            logger.error(f"Error saving history to database: {e}")

    def load_history(self) -> ClipboardHistory:
        try:
            # TODO: Add tests
            if not os.path.exists(self.db_path):
                logger.info("No existing database found, starting with empty history.")
                return ClipboardHistory(items=[])

            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()

                max_items = 1000  # Hardcoded max items

                cursor.execute(
                    "SELECT content, created_at FROM clipboard_history ORDER BY created_at DESC"
                )
                rows = cursor.fetchall()

                items = []
                for content, created_at_str in rows:
                    try:
                        created_at = datetime.fromisoformat(created_at_str)
                        item = ClipboardItem(content=content, created_at=created_at)
                        items.append(item)
                    except (ValueError, TypeError) as e:
                        logger.warning(f"Skipping invalid history item: {e}")
                        continue

                history = ClipboardHistory(items=items, max_items=max_items)
                logger.info(f"Loaded {len(items)} items from database.")
                return history

        except sqlite3.Error as e:
            # TODO: Add tests
            logger.error(f"Error loading history from database: {e}")
            logger.info("Starting with empty history.")
            return ClipboardHistory(items=[])

    def clear_storage(self) -> None:
        # TODO: Add tests
        try:
            if os.path.exists(self.db_path):
                os.remove(self.db_path)
                logger.info(f"Database file {self.db_path} deleted.")
        except (OSError, sqlite3.Error) as e:
            logger.error(f"Error deleting database file: {e}")
