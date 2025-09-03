from src.infrastructure.logger import setup_logger
from src.application.clipboard_service import ClipboardService
from src.adapters.pyperclip_adapter import PyperclipAdapter
from src.adapters.sqlite_storage_adapter import SqliteStorageAdapter
from src.adapters.tkinter_ui_adapter import TkinterUIAdapter
from src.adapters.fuzzy_search_adapter import FuzzySearchAdapter
from loguru import logger


def main():
    setup_logger()
    logger.info("Preparing to launch Clip Flow.")

    clipboard_adapter = PyperclipAdapter()
    storage_adapter = SqliteStorageAdapter()
    ui_adapter = TkinterUIAdapter()
    search_adapter = FuzzySearchAdapter(max_l_dist=1, case_sensitive=False)

    clipboard_service = ClipboardService(
        clipboard_port=clipboard_adapter,
        storage_port=storage_adapter,
        ui_port=ui_adapter,
        search_port=search_adapter,
    )

    clipboard_service.start()


if __name__ == "__main__":
    main()
