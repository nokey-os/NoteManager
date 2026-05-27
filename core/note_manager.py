"""Модуль управления заметками."""

import logging
from pathlib import Path
from typing import List, Optional

from models import Note
from driver.file_driver import JSONFileDriver, FileDriverError

from .errors import (
    NoteManagerError,
    NoteNotFoundError,
    ValidationError,
    EmptyTitleError,
    EmptyListError
)
from .json_recovery import JSONRecoveryManager
from .utils import FileValidator, PathResolver

logger = logging.getLogger(__name__)


class NoteManager:
    """Менеджер для управления заметками."""

    def __init__(self, storage_path: str = "data/notes.json") -> None:
        """
        Инициализация NoteManager.

        Args:
            storage_path: Путь к файлу хранения заметок
        """
        self._driver = JSONFileDriver(storage_path)
        self._notes: List[Note] = []
        self._storage_path = storage_path

        # Инициализация валидатора и резолвера
        self._file_validator = FileValidator()
        self._path_resolver = PathResolver()

        # Проверка и восстановление JSON
        self._check_and_recovery()
        self._load_notes()

    def _check_and_recovery(self) -> None:
        """Проверка и автоматическое восстановление JSON файла."""
        recovery_manager = JSONRecoveryManager(self._storage_path)
        status = recovery_manager.check_and_recovery()

        if status['status'] == 'error':
            logger.warning(f"Ошибка восстановления: {status['message']}")
        elif status['recovery_needed']:
            logger.info(f"Восстановление выполнено: {status['message']}")

    def _load_notes(self) -> None:
        """Загрузка заметок из хранилища."""
        try:
            data = self._driver.load()
            self._notes = [Note.from_dict(item) for item in data]
            logger.info(f"Загружено {len(self._notes)} заметок")
        except FileDriverError as e:
            logger.error(f"Ошибка загрузки заметок: {e}")
            self._notes = []

    def _save_notes(self) -> None:
        """Сохранение заметок в хранилище."""
        try:
            data = [note.to_dict() for note in self._notes]
            self._driver.save(data)
        except FileDriverError as e:
            logger.error(f"Ошибка сохранения заметок: {e}")
            raise NoteManagerError(f"Не удалось сохранить заметки: {e}")

    def create_note(
        self, title: str, content: str = "",
        attachments: Optional[List[str]] = None
    ) -> Note:
        """
        Создание новой заметки.

        Args:
            title: Заголовок заметки (обязательное)
            content: Содержание заметки
            attachments: Список путей к вложениям

        Returns:
            Созданная заметка

        Raises:
            ValidationError: Если заголовок пустой
        """
        # Валидация заголовка
        if not title or not title.strip():
            error = EmptyTitleError()
            logger.error(error.message)
            raise error

        # Валидация вложений (без проверки существования - файлы могут быть добавлены позже)
        valid_attachments = []
        if attachments:
            for att in attachments:
                is_valid, error_msg = self._file_validator.validate_path(att, must_exist=False)
                if is_valid:
                    valid_attachments.append(att)
                else:
                    logger.warning(f"Пропущено вложение '{att}': {error_msg}")

        note = Note(
            title=title.strip(),
            content=content,
            attachments=valid_attachments
        )

        self._notes.append(note)
        self._save_notes()

        logger.info(f"Создана заметка: id={note.id}, title='{note.title}'")
        return note

    def get_all_notes(self) -> List[Note]:
        """
        Получение всех заметок.

        Returns:
            Список всех заметок
        """
        logger.debug(f"Получено {len(self._notes)} заметок")
        return self._notes.copy()

    def get_note_by_id(self, note_id: str) -> Note:
        """
        Получение заметки по ID.

        Args:
            note_id: Уникальный идентификатор заметки

        Returns:
            Найденная заметка

        Raises:
            NoteNotFoundError: Если заметка не найдена
        """
        for note in self._notes:
            if note.id == note_id:
                logger.debug(f"Найдена заметка: id={note_id}")
                return note

        error_msg = f"Заметка с id={note_id} не найдена"
        logger.error(error_msg)
        raise NoteNotFoundError(error_msg)

    def update_note(self, note_id: str, **kwargs) -> Note:
        """
        Частичное обновление заметки.

        Args:
            note_id: Уникальный идентификатор заметки
            **kwargs: Поля для обновления (title, content, attachments)

        Returns:
            Обновлённая заметка

        Raises:
            NoteNotFoundError: Если заметка не найдена
            ValidationError: Если данные невалидны
        """
        if not self._notes:
            error = EmptyListError("обновление")
            logger.warning(error.message)
            raise NoteManagerError(error.message)

        note = self.get_note_by_id(note_id)

        # Валидация полей перед обновлением
        if "title" in kwargs:
            if not kwargs["title"] or not kwargs["title"].strip():
                error = EmptyTitleError()
                logger.error(error.message)
                raise EmptyTitleError()
            kwargs["title"] = kwargs["title"].strip()

        if "attachments" in kwargs:
            if not isinstance(kwargs["attachments"], list):
                error_msg = "Attachments должен быть списком"
                logger.error(error_msg)
                raise ValidationError("attachments", error_msg, "Убедитесь что вложения — список строк")
            if not all(isinstance(att, str) for att in kwargs["attachments"]):
                error_msg = "Все элементы attachments должны быть строками"
                logger.error(error_msg)
                raise ValidationError("attachments", error_msg, "Проверьте формат вложений")

        # Обновление полей
        for key, value in kwargs.items():
            if hasattr(note, key):
                setattr(note, key, value)

        self._save_notes()
        logger.info(f"Обновлена заметка: id={note_id}")
        return note

    def delete_note(self, note_id: str) -> bool:
        """
        Удаление заметки по ID.

        Args:
            note_id: Уникальный идентификатор заметки

        Returns:
            True если заметка удалена

        Raises:
            NoteNotFoundError: Если заметка не найдена
        """
        if not self._notes:
            error = EmptyListError("удаление")
            logger.warning(error.message)
            raise NoteManagerError(error.message)

        note = self.get_note_by_id(note_id)
        self._notes.remove(note)
        self._save_notes()

        logger.info(f"Удалена заметка: id={note_id}")
        return True

    def clear_all(self) -> int:
        """
        Удаление всех заметок.

        Returns:
            Количество удалённых заметок
        """
        count = len(self._notes)
        self._notes = []
        self._save_notes()
        logger.info(f"Удалено {count} заметок")
        return count

    def validate_attachments(self, attachments: List[str]) -> tuple:
        """
        Валидация списка вложений.

        Args:
            attachments: Список путей к файлам

        Returns:
            (valid_attachments, invalid_attachments, errors)
        """
        return self._file_validator.validate_attachment_list(attachments, must_exist=True)

    def check_attachment_exists(self, filename: str) -> bool:
        """
        Проверка существования файла вложения.

        Args:
            filename: Имя файла

        Returns:
            True если файл существует
        """
        return self._path_resolver.exists(filename)

    def get_attachment_path(self, filename: str) -> Optional[Path]:
        """
        Получение пути к файлу вложения.

        Args:
            filename: Имя файла

        Returns:
            Путь к файлу или None если не существует
        """
        if self.check_attachment_exists(filename):
            return self._path_resolver.resolve(filename)
        return None
