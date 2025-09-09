from abc import ABC, abstractmethod
from typing import List, Callable


class UIPort(ABC):
    @abstractmethod
    def show_history(self, items: List[str]) -> None:
        """Display history items in the UI."""

    @abstractmethod
    def show_message(self, message: str, message_type: str = "info") -> None:
        """Show a message to the user."""

    @abstractmethod
    def run(self) -> None:
        """Start the UI main loop."""

    @abstractmethod
    def register_copy_callback(self, callback: Callable[[int], None]) -> None:
        """Register callback for when user wants to copy an item."""

    @abstractmethod
    def register_search_callback(self, callback: Callable[[str], None]) -> None:
        """Register callback for search input changes."""

    @abstractmethod
    def register_clear_callback(self, callback: Callable[[], None]) -> None:
        """Register callback for clear history action."""

    @abstractmethod
    def register_delete_callback(self, callback: Callable[[int], None]) -> None:
        """Register callback for delete item action."""

    @abstractmethod
    def shutdown(self) -> None:
        """Shutdown the UI."""

    @abstractmethod
    def show_window(self) -> None:
        """Show the application window."""

    @abstractmethod
    def hide_window(self) -> None:
        """Hide the application window."""

    @abstractmethod
    def register_hide_callback(self, callback: Callable[[], None]) -> None:
        """Register callback for when window is hidden."""
