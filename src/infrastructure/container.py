import time

from loguru import logger

from src.adapters.fuzzy_search_adapter import FuzzySearchAdapter
from src.adapters.pyperclip_adapter import PyperclipAdapter
from src.adapters.sqlite_storage_adapter import SqliteStorageAdapter
from src.adapters.system_tray_adapter import SystemTrayAdapter
from src.adapters.settings.json_settings_adapter import JsonSettingsAdapter
from src.adapters.settings.json_settings_schema_adapter import JsonSettingsSchemaAdapter
from src.adapters.ui.tkinter_ui_adapter import TkinterUIAdapter
from src.application.app_service import AppService


class Container:
    def __init__(self):
        self.settings_adapter = JsonSettingsAdapter()
        self.schema_adapter = JsonSettingsSchemaAdapter()
        
        self.clipboard_adapter = PyperclipAdapter()
        self.storage_adapter = SqliteStorageAdapter()
        self.ui_adapter = TkinterUIAdapter(self.settings_adapter)
        
        max_l_dist = self.settings_adapter.get_setting(
            "fuzzy_search_max_l_dist",
            self.schema_adapter.get_default_value("fuzzy_search_max_l_dist")
        )
        case_sensitive = self.settings_adapter.get_setting(
            "fuzzy_search_case_sensitive",
            self.schema_adapter.get_default_value("fuzzy_search_case_sensitive")
        )
        self.search_adapter = FuzzySearchAdapter(max_l_dist=max_l_dist, case_sensitive=case_sensitive)
        self.system_tray = SystemTrayAdapter()
        
        self.app_service = AppService(
            clipboard_port=self.clipboard_adapter,
            storage_port=self.storage_adapter,
            ui_port=self.ui_adapter,
            search_port=self.search_adapter
        )
    
    def setup_system_integration(self) -> None:
        def show_window():
            self.ui_adapter.show_window()
        
        def quit_application():
            logger.info("Shutting down application")
            self.system_tray.stop()
            self.app_service.stop()
        
        def hide_to_tray():
            logger.debug("Application hidden to system tray")
        
        self.system_tray.register_show_callback(show_window)
        self.system_tray.register_quit_callback(quit_application)
        self.ui_adapter.register_hide_callback(hide_to_tray)
        
        self.system_tray.start()
        
        logger.info("System integration configured")
    
    def start_application(self) -> None:
        logger.info("Initializing application")
        
        self.setup_system_integration()
        
        time.sleep(0.5)
        
        self.app_service.start()