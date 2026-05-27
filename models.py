"""Модели данных для системы управления заметками."""

from dataclasses import dataclass, field
from datetime import datetime
from typing import List
import uuid


@dataclass
class Note:
    """Модель заметки."""

    title: str
    content: str = ""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    attachments: List[str] = field(default_factory=list)

    def __post_init__(self) -> None:
        """Валидация полей после инициализации."""
        if not self.title or not self.title.strip():
            raise ValueError("Title cannot be empty")

        if not isinstance(self.attachments, list):
            raise TypeError("Attachments must be a list")

        if not all(isinstance(att, str) for att in self.attachments):
            raise TypeError("All attachments must be strings")

    def to_dict(self) -> dict:
        """Преобразование модели в словарь."""
        return {
            "id": self.id,
            "title": self.title,
            "content": self.content,
            "timestamp": self.timestamp,
            "attachments": self.attachments
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Note":
        """Создание модели из словаря."""
        return cls(
            id=data.get("id", str(uuid.uuid4())),
            title=data["title"],
            content=data.get("content", ""),
            timestamp=data.get("timestamp", datetime.now().isoformat()),
            attachments=data.get("attachments", [])
        )
