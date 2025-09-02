from abc import ABC, abstractmethod
from typing import Callable


class ClipboardPort(ABC):
    @abstractmethod
    def get_content(self) -> str:
        """Get current clipboard content."""

    @abstractmethod
    def set_content(self, content: str) -> None:
        """Set clipboard content."""

    @abstractmethod
    def start_monitoring(self, callback: Callable[[str], None]) -> None:
        """Start monitoring clipboard changes."""

    @abstractmethod
    def stop_monitoring(self) -> None:
        """Stop monitoring clipboard changes."""
