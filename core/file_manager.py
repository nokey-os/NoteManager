"""Модуль управления файлами для NoteMaster."""

import logging
import os
import uuid
from pathlib import Path
from typing import List, Optional, Tuple
from datetime import datetime

from .utils import FileValidator, sanitize_filename

logger = logging.getLogger(__name__)


class FileManagerError(Exception):
    """Базовое исключение для ошибок файлового менеджера."""
    pass


class FileManager:
    """Менеджер для работы с файлами вложений."""

    def __init__(self, upload_folder: str, max_size_mb: int = 50):
        """
        Инициализация файлового менеджера.

        Args:
            upload_folder: Директория для загруженных файлов
            max_size_mb: Максимальный размер файла в MB
        """
        self.upload_folder = Path(upload_folder)
        self.upload_folder.mkdir(parents=True, exist_ok=True)
        self.max_size_bytes = max_size_mb * 1024 * 1024
        self.validator = FileValidator()

        logger.info(f"FileManager инициализирован: {self.upload_folder}")

    def save_file(
        self, file_content, original_filename: str,
        note_id: Optional[str] = None
    ) -> Tuple[bool, str, Optional[str]]:
        """
        Сохранение загруженного файла.

        Args:
            file_content: Содержимое файла или путь
            original_filename: Оригинальное имя файла
            note_id: ID заметки (для уникализации имени)

        Returns:
            (success, saved_filename, error_message)
        """
        try:
            # Санитизация имени
            safe_filename = sanitize_filename(original_filename)

            # Генерация уникального имени с UUID
            if note_id:
                unique_name = f"{note_id}_{uuid.uuid4().hex[:8]}_{safe_filename}"
            else:
                unique_name = f"{uuid.uuid4().hex}_{safe_filename}"

            file_path = self.upload_folder / unique_name

            # Проверка размера (если передан путь)
            if isinstance(file_content, str) and os.path.exists(file_content):
                file_size = os.path.getsize(file_content)
                if file_size > self.max_size_bytes:
                    return False, "", f"Файл слишком большой: {file_size} > {self.max_size_bytes}"

            # Сохранение файла
            if hasattr(file_content, 'read'):
                # Это файловый объект (например, из Flask request)
                file_content.save(str(file_path))
            else:
                # Это путь к файлу
                import shutil
                shutil.copy2(file_content, str(file_path))

            logger.info(f"Файл сохранён: {unique_name} ({file_path.stat().st_size} байт)")
            return True, unique_name, None

        except Exception as e:
            logger.error(f"Ошибка сохранения файла {original_filename}: {e}", exc_info=True)
            return False, "", str(e)

    def get_file_path(self, filename: str) -> Path:
        """Получить полный путь к файлу."""
        return self.upload_folder / filename

    def file_exists(self, filename: str) -> bool:
        """Проверить существование файла."""
        file_path = self.get_file_path(filename)
        return file_path.exists() and file_path.is_file()

    def get_file_url(self, filename: str, base_url: str = "/uploads/") -> str:
        """Получить URL для файла."""
        return f"{base_url}{filename}"

    def get_file_info(self, filename: str) -> Optional[dict]:
        """Получить информацию о файле."""
        file_path = self.get_file_path(filename)

        if not file_path.exists():
            return None

        try:
            stat = file_path.stat()
            return {
                "name": filename,
                "path": str(file_path),
                "size": stat.st_size,
                "size_formatted": self._format_size(stat.st_size),
                "modified": datetime.fromtimestamp(stat.st_mtime).isoformat(),
                "exists": True
            }
        except Exception as e:
            logger.error(f"Ошибка получения информации о файле {filename}: {e}")
            return None

    def delete_file(self, filename: str) -> Tuple[bool, Optional[str]]:
        """
        Удалить файл.

        Args:
            filename: Имя файла для удаления

        Returns:
            (success, error_message)
        """
        file_path = self.get_file_path(filename)

        if not file_path.exists():
            logger.warning(f"Файл не найден для удаления: {filename}")
            return True, None  # Уже удалён

        try:
            file_path.unlink()
            logger.info(f"Файл удалён: {filename}")
            return True, None
        except Exception as e:
            logger.error(f"Ошибка удаления файла {filename}: {e}")
            return False, str(e)

    def delete_files(self, filenames: List[str]) -> dict:
        """
        Удалить несколько файлов.

        Args:
            filenames: Список имён файлов

        Returns:
            {filename: (success, error_message)}
        """
        results = {}
        for filename in filenames:
            success, error = self.delete_file(filename)
            results[filename] = {"success": success, "error": error}
        return results

    def validate_file(self, filename: str, must_exist: bool = True) -> Tuple[bool, Optional[str]]:
        """
        Валидация файла.

        Args:
            filename: Имя файла
            must_exist: Проверять ли существование

        Returns:
            (is_valid, error_message)
        """
        if not filename:
            return False, "Имя файла не может быть пустым"

        # Проверка расширения
        is_valid, error = self.validator.validate_path(filename, must_exist=False)
        if not is_valid:
            return False, error

        # Проверка существования
        if must_exist and not self.file_exists(filename):
            return False, f"Файл не найден: {filename}"

        return True, None

    def validate_files(self, filenames: List[str], must_exist: bool = True) -> Tuple[List[str], List[str], List[str]]:
        """
        Валидация списка файлов.

        Args:
            filenames: Список имён файлов
            must_exist: Проверять ли существование

        Returns:
            (valid_files, invalid_files, error_messages)
        """
        valid = []
        invalid = []
        errors = []

        for filename in filenames:
            is_valid, error = self.validate_file(filename, must_exist)
            if is_valid:
                valid.append(filename)
            else:
                invalid.append(filename)
                errors.append(f"{filename}: {error}")

        return valid, invalid, errors

    def _format_size(self, size_bytes: int) -> str:
        """Форматирование размера файла."""
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size_bytes < 1024:
                return f"{size_bytes:.1f} {unit}"
            size_bytes /= 1024
        return f"{size_bytes:.1f} TB"

    def cleanup_orphaned_files(self, used_filenames: List[str]) -> List[str]:
        """
        Удаление неиспользуемых файлов.

        Args:
            used_filenames: Список используемых имён файлов

        Returns:
            Список удалённых файлов
        """
        deleted = []
        used_set = set(used_filenames)

        try:
            for file_path in self.upload_folder.iterdir():
                if file_path.is_file():
                    if file_path.name not in used_set:
                        file_path.unlink()
                        deleted.append(file_path.name)
                        logger.info(f"Удалён неиспользуемый файл: {file_path.name}")
        except Exception as e:
            logger.error(f"Ошибка очистки orphaned файлов: {e}")

        return deleted
