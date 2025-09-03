from src.infrastructure.logger import setup_logger
from src.application.clipboard_service import ClipboardService
from src.adapters.pyperclip_adapter import PyperclipAdapter
from src.adapters.sqlite_storage_adapter import SqliteStorageAdapter
from src.adapters.tkinter_ui_adapter import TkinterUIAdapter
from src.adapters.fuzzy_search_adapter import FuzzySearchAdapter
from src.adapters.system_tray_adapter import SystemTrayAdapter
from loguru import logger
import threading
import time


def main():
    setup_logger()
    logger.info("Preparing to launch Clip Flow.")

    clipboard_adapter = PyperclipAdapter()
    storage_adapter = SqliteStorageAdapter()
    ui_adapter = TkinterUIAdapter()
    search_adapter = FuzzySearchAdapter(max_l_dist=1, case_sensitive=False)
    tray_adapter = SystemTrayAdapter()

    clipboard_service = ClipboardService(
        clipboard_port=clipboard_adapter,
        storage_port=storage_adapter,
        ui_port=ui_adapter,
        search_port=search_adapter,
    )

    def show_window():
        """Callback для показа окна из системного трея"""
        ui_adapter.show_window()

    def quit_application():
        """Callback для выхода из приложения"""
        logger.info("Shutting down application")
        tray_adapter.stop()
        ui_adapter.shutdown()

    def hide_to_tray():
        """Callback для скрытия окна в системный трей"""
        logger.info("Application hidden to system tray")

    # Настройка callback'ов для системного трея
    tray_adapter.register_show_callback(show_window)
    tray_adapter.register_quit_callback(quit_application)
    
    # Настройка callback'а для UI адаптера
    ui_adapter.register_hide_callback(hide_to_tray)

    # Запуск системного трея
    tray_adapter.start()
    
    # Скрытие окна при запуске (приложение запускается в трее)
    ui_adapter.hide_window()
    
    # Запуск сервиса буфера обмена в отдельном потоке
    clipboard_thread = threading.Thread(target=clipboard_service.start_monitoring, daemon=True)
    clipboard_thread.start()
    
    # Ожидание небольшой задержки для корректной инициализации
    time.sleep(0.5)
    
    # Запуск основного цикла UI
    ui_adapter.run()


if __name__ == "__main__":
    main()
