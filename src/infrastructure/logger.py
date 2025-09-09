import sys

from loguru import logger

from src.infrastructure.system_paths import ensure_directories_exist, get_log_file_path


def setup_logger():
    ensure_directories_exist()

    logger.remove()

    if sys.stderr is not None:
        logger.add(
            sys.stderr,
            format="<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
            level="DEBUG",
        )

    log_file_path = get_log_file_path()
    logger.add(
        str(log_file_path),
        format="{time:YYYY-MM-DD HH:mm:ss.SSS} | {level: <8} | {name}:{function}:{line} - {message}",
        level="DEBUG",
        rotation="10 MB",
        retention="7 days",
    )

    logger.info(f"Logger configured successfully. Log file: {log_file_path}")
