import time

from loguru import logger

from src.adapters.fuzzy_search_adapter import FuzzySearchAdapter
from src.adapters.pyperclip_adapter import PyperclipAdapter
from src.adapters.sqlite_storage_adapter import SqliteStorageAdapter
from src.adapters.system_tray_adapter import SystemTrayAdapter
from src.adapters.tkinter_ui_adapter import TkinterUIAdapter
from src.application.app_service import AppService


class Container:
    def __init__(self):
        self._app_service = None
        self._system_tray = None
    
    def get_app_service(self) -> AppService:
        if self._app_service is None:
            self._app_service = self._create_app_service()
        return self._app_service
    
    def get_system_tray(self) -> SystemTrayAdapter:
        if self._system_tray is None:
            self._system_tray = SystemTrayAdapter()
        return self._system_tray
    
    def _create_app_service(self) -> AppService:
        clipboard_adapter = PyperclipAdapter()
        storage_adapter = SqliteStorageAdapter()
        ui_adapter = TkinterUIAdapter()
        search_adapter = FuzzySearchAdapter(max_l_dist=3, case_sensitive=False)
        
        app_service = AppService(
            clipboard_port=clipboard_adapter,
            storage_port=storage_adapter,
            ui_port=ui_adapter,
            search_port=search_adapter
        )
        
        return app_service
    
    def setup_system_integration(self) -> None:
        app_service = self.get_app_service()
        system_tray = self.get_system_tray()
        ui_adapter = app_service.ui_port
        
        def show_window():
            ui_adapter.show_window()
        
        def quit_application():
            logger.info("Shutting down application")
            system_tray.stop()
            app_service.stop()
        
        def hide_to_tray():
            logger.debug("Application hidden to system tray")
        
        system_tray.register_show_callback(show_window)
        system_tray.register_quit_callback(quit_application)
        ui_adapter.register_hide_callback(hide_to_tray)
        
        system_tray.start()
        
        logger.info("System integration configured")
    
    def start_application(self) -> None:
        logger.info("Initializing application")
        
        self.setup_system_integration()
        
        time.sleep(0.5)
        
        app_service = self.get_app_service()
        app_service.start()