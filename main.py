from src.infrastructure.logger import setup_logger
from src.application.clipboard_service import ClipboardService
from src.adapters.pyperclip_adapter import PyperclipAdapter
from src.adapters.json_storage_adapter import JsonStorageAdapter
from src.adapters.tkinter_ui_adapter import TkinterUIAdapter
from src.adapters.simple_search_adapter import SimpleSearchAdapter
from loguru import logger


def main():
    setup_logger()
    logger.info("Preparing to launch Clip Flow.")

    clipboard_adapter = PyperclipAdapter()
    storage_adapter = JsonStorageAdapter("clipboard_history.json")
    ui_adapter = TkinterUIAdapter()
    search_adapter = SimpleSearchAdapter(case_sensitive=False)

    clipboard_service = ClipboardService(
        clipboard_port=clipboard_adapter,
        storage_port=storage_adapter,
        ui_port=ui_adapter,
        search_port=search_adapter,
    )

    clipboard_service.start()


if __name__ == "__main__":
    main()
