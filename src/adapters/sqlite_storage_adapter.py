import sqlite3
import os
from datetime import datetime
from loguru import logger
from src.ports.storage_port import StoragePort
from src.domain.models import ClipboardHistory, ClipboardItem


class SqliteStorageAdapter(StoragePort):
    def __init__(self, db_path: str = "clipboard_history.db"):
        self.db_path = db_path
        self._init_database()
        logger.debug(f"SqliteStorageAdapter initialized with database: {db_path}")

    def _init_database(self) -> None:
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS clipboard_history (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        content TEXT NOT NULL,
                        created_at TEXT NOT NULL
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS settings (
                        key TEXT PRIMARY KEY,
                        value TEXT NOT NULL
                    )
                ''')
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
                cursor.execute("DELETE FROM settings WHERE key = 'max_items'")
                
                cursor.execute(
                    "INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?)",
                    ("max_items", str(history.max_items))
                )
                
                for item in history.items:
                    cursor.execute(
                        "INSERT INTO clipboard_history (content, created_at) VALUES (?, ?)",
                        (item.content, item.created_at.isoformat())
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
                
                cursor.execute("SELECT value FROM settings WHERE key = 'max_items'")
                max_items_result = cursor.fetchone()
                max_items = int(max_items_result[0]) if max_items_result else 1000
                
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