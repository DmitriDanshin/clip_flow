import pystray
from PIL import Image, ImageDraw
import keyboard
import threading
from typing import Callable, Optional
from loguru import logger


class SystemTrayAdapter:
    def __init__(self):
        self.icon: Optional[pystray.Icon] = None
        self._show_callback: Optional[Callable[[], None]] = None
        self._quit_callback: Optional[Callable[[], None]] = None
        self._hotkey_thread: Optional[threading.Thread] = None
        self._running = False
        logger.debug("SystemTrayAdapter initialized.")

    def register_show_callback(self, callback: Callable[[], None]) -> None:
        self._show_callback = callback

    def register_quit_callback(self, callback: Callable[[], None]) -> None:
        self._quit_callback = callback

    def create_icon(self) -> Image.Image:
        # TODO: Use icon
        image = Image.new('RGB', (64, 64), color=(73, 109, 137))
        dc = ImageDraw.Draw(image)
        
        dc.rectangle([16, 8, 48, 56], fill=(255, 255, 255), outline=(0, 0, 0))
        dc.rectangle([20, 16, 44, 24], fill=(0, 0, 0))
        dc.rectangle([20, 28, 44, 32], fill=(0, 0, 0))
        dc.rectangle([20, 36, 44, 40], fill=(0, 0, 0))
        dc.rectangle([20, 44, 36, 48], fill=(0, 0, 0))
        
        return image

    def setup_global_hotkey(self) -> None:
        def hotkey_handler():
            if self._show_callback:
                logger.debug("Global hotkey triggered")
                self._show_callback()

        def hotkey_listener():
            try:
                keyboard.add_hotkey('ctrl+shift+q', hotkey_handler, suppress=True)
                logger.info("Global hotkey registered: Ctrl+Shift+Q")
                keyboard.wait()
            except Exception as exception:
                logger.error(f"Error in hotkey listener: {exception}")

        self._hotkey_thread = threading.Thread(target=hotkey_listener, daemon=True)
        self._hotkey_thread.start()

    def show_window(self) -> None:
        if self._show_callback:
            self._show_callback()

    def quit_application(self) -> None:
        logger.info("Quitting application from system tray")
        self._running = False
        
        if self._quit_callback:
            self._quit_callback()
        
        if self.icon:
            self.icon.stop()

    def start(self) -> None:
        if self._running:
            return
            
        self._running = True
        
        self.setup_global_hotkey()
        
        menu = pystray.Menu(
            pystray.MenuItem("Show", self.show_window, default=True),
            pystray.MenuItem("Exit", self.quit_application)
        )
        
        icon_image = self.create_icon()
        self.icon = pystray.Icon("Clip Flow", icon_image, menu=menu)
        
        logger.info("Starting system tray")
        
        tray_thread = threading.Thread(target=self._run_tray, daemon=True)
        tray_thread.start()

    def _run_tray(self) -> None:
        try:
            if self.icon:
                self.icon.run()
        except Exception as exception:
            logger.error(f"Error running system tray: {exception}")

    def stop(self) -> None:
        logger.info("Stopping system tray")
        self._running = False
        
        try:
            keyboard.unhook_all()
        except Exception as exception:
            logger.error(f"Error unhooking keyboard: {exception}")
        
        if self.icon:
            self.icon.stop()