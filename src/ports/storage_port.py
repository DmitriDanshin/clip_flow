from abc import ABC, abstractmethod
from src.domain.clipboard import ClipboardHistory


class StoragePort(ABC):
    """Port for storage operations."""

    @abstractmethod
    def save_history(self, history: ClipboardHistory) -> None:
        """Save clipboard history to storage."""

    @abstractmethod
    def load_history(self) -> ClipboardHistory:
        """Load clipboard history from storage."""

    @abstractmethod
    def clear_storage(self) -> None:
        """Clear all stored data."""
