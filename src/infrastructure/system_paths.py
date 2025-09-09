from pathlib import Path

from loguru import logger
from platformdirs import user_config_dir, user_data_dir, user_log_dir


def ensure_directories_exist() -> None:
    directories = [
        Path(user_data_dir("clip_flow", appauthor=False)),
        Path(user_log_dir("clip_flow", appauthor=False)),
        Path(user_config_dir("clip_flow", appauthor=False)),
    ]

    for directory in directories:
        try:
            directory.mkdir(parents=True, exist_ok=True)
            logger.trace(f"Ensured directory exists: {directory}")
        except OSError as exception:
            logger.error(f"Failed to create directory {directory}: {exception}")
            raise


def get_log_file_path() -> Path:
    return Path(user_log_dir("clip_flow", appauthor=False)) / "clip_flow.log"


def get_database_file_path() -> Path:
    return Path(user_data_dir("clip_flow", appauthor=False)) / "clipboard_history.db"


def get_config_dir() -> Path:
    return Path(user_config_dir("clip_flow", appauthor=False))
