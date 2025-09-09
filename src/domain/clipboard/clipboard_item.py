from dataclasses import dataclass
from datetime import datetime


@dataclass
class ClipboardItem:
    content: str
    created_at: datetime

    def __post_init__(self):
        if not self.content:
            raise ValueError("Clipboard item content cannot be empty")

    def preview(self, max_length: int = 50) -> str:
        preview = self.content.replace("\n", " ").replace("\r", " ")
        if len(preview) > max_length:
            return preview[: max_length - 3] + "..."
        return preview