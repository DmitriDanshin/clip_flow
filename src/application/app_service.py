from loguru import logger
from src.ports.clipboard_port import ClipboardPort
from src.ports.storage_port import StoragePort
from src.ports.ui_port import UIPort
from src.ports.search_port import SearchPort
from src.application.clipboard_service import ClipboardService


class AppService:
    def __init__(
        self,
        clipboard_port: ClipboardPort,
        storage_port: StoragePort,
        ui_port: UIPort,
        search_port: SearchPort,
    ):
        self.clipboard_service = ClipboardService(
            clipboard_port=clipboard_port,
            storage_port=storage_port,
            ui_port=ui_port,
            search_port=search_port,
        )
        self.ui_port = ui_port
        self._running = False
        logger.debug("AppService initialized.")

    def start(self) -> None:
        if self._running:
            return

        self._running = True
        logger.info("Starting application")

        self.clipboard_service.start_monitoring()

        self.ui_port.hide_window()

        self.ui_port.run()

    def stop(self) -> None:
        if not self._running:
            return

        logger.info("Stopping application")
        self._running = False
        self.clipboard_service.stop()
        self.ui_port.shutdown()
