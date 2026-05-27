"""Утилиты для NoteMaster."""

import logging
import re
from pathlib import Path
from typing import List

logger = logging.getLogger(__name__)


class FileValidator:
    """Валидатор файлов."""

    # Поддерживаемые расширения
    ALLOWED_EXTENSIONS = {
        # Документы
        '.pdf', '.doc', '.docx', '.txt', '.rtf',
        # Таблицы
        '.xlsx', '.xls', '.csv',
        # Презентации
        '.ppt', '.pptx',
        # Изображения
        '.png', '.jpg', '.jpeg', '.gif', '.svg', '.bmp', '.webp',
        # Видео
        '.mp4', '.avi', '.mov', '.mkv', '.wmv', '.flv',
        # Аудио
        '.mp3', '.wav', '.aac', '.ogg',
        # Архивы
        '.zip', '.rar', '.7z', '.tar', '.gz',
        # Код
        '.py', '.js', '.html', '.css', '.json', '.md', '.txt',
    }

    @classmethod
    def validate_path(cls, path: str, must_exist: bool = True) -> tuple:
        """
        Валидация пути к файлу.

        Args:
            path: Путь к файлу
            must_exist: Проверять ли существование файла

        Returns:
            (is_valid, error_message)
        """
        path = path.strip()

        if not path:
            return False, "Путь не может быть пустым"

        # Проверка расширения
        ext = Path(path).suffix.lower()
        if ext not in cls.ALLOWED_EXTENSIONS:
            return False, f"Неподдерживаемый формат файла: {ext}"

        # Проверка существования
        if must_exist:
            file_path = Path(path)
            if not file_path.exists():
                return False, f"Файл не существует: {path}"

            if not file_path.is_file():
                return False, f"Путь не является файлом: {path}"

        return True, None

    @classmethod
    def validate_attachment_list(cls, attachments: List[str], must_exist: bool = True) -> tuple:
        """
        Валидация списка вложений.

        Args:
            attachments: Список путей к файлам
            must_exist: Проверять ли существование файлов

        Returns:
            (valid_attachments, invalid_attachments, error_messages)
        """
        valid = []
        invalid = []
        errors = []

        for path in attachments:
            is_valid, error_msg = cls.validate_path(path, must_exist)
            if is_valid:
                valid.append(path)
            else:
                invalid.append(path)
                errors.append(f"'{path}': {error_msg}")

        return valid, invalid, errors

    @classmethod
    def get_file_icon(cls, filename: str) -> str:
        """Получить иконку для типа файла."""
        ext = Path(filename).suffix.lower()

        icons = {
            # Документы
            '.pdf': '📄', '.doc': '📝', '.docx': '📝', '.txt': '📝', '.rtf': '📝',
            # Таблицы
            '.xlsx': '📊', '.xls': '📊', '.csv': '📊',
            # Презентации
            '.ppt': '📽️', '.pptx': '📽️',
            # Изображения
            '.png': '🖼️', '.jpg': '🖼️', '.jpeg': '🖼️', '.gif': '🖼️', '.svg': '🖼️', '.bmp': '🖼️', '.webp': '🖼️',
            # Видео
            '.mp4': '🎬', '.avi': '🎬', '.mov': '🎬', '.mkv': '🎬', '.wmv': '🎬', '.flv': '🎬',
            # Аудио
            '.mp3': '🎵', '.wav': '🎵', '.aac': '🎵', '.ogg': '🎵',
            # Архивы
            '.zip': '📦', '.rar': '📦', '.7z': '📦', '.tar': '📦', '.gz': '📦',
        }

        return icons.get(ext, '📎')


class PathResolver:
    """Резолвер путей для файлов."""

    def __init__(self, base_dir: str = "uploads"):
        """
        Инициализация резолвера.

        Args:
            base_dir: Базовая директория для файлов
        """
        self.base_dir = Path(base_dir)
        self.base_dir.mkdir(parents=True, exist_ok=True)

    def resolve(self, filename: str) -> Path:
        """
        Разрешение полного пути к файлу.

        Args:
            filename: Имя файла

        Returns:
            Полный путь к файлу
        """
        return self.base_dir / filename

    def exists(self, filename: str) -> bool:
        """Проверка существования файла."""
        return self.resolve(filename).exists()

    def get_url(self, filename: str, base_url: str = "/uploads/") -> str:
        """Получить URL для файла."""
        return f"{base_url}{filename}"

    def delete(self, filename: str) -> bool:
        """
        Удаление файла.

        Args:
            filename: Имя файла

        Returns:
            True если удалено успешно
        """
        file_path = self.resolve(filename)
        if file_path.exists():
            try:
                file_path.unlink()
                return True
            except Exception as e:
                logger.error(f"Ошибка удаления файла {filename}: {e}")
                return False
        return False


def sanitize_filename(filename: str) -> str:
    """
    Очистка имени файла от опасных символов.

    Args:
        filename: Оригинальное имя файла

    Returns:
        Безопасное имя файла
    """
    # Удаляем пути и только оставляем имя файла
    path = Path(filename)
    name = path.name

    # Удаляем опасные символы
    name = re.sub(r'[<>:"/\\|?*]', '_', name)

    # Ограничиваем длину
    if len(name) > 200:
        stem = path.stem[:180]
        ext = path.suffix
        name = f"{stem}{ext}"

    return name if name else "unnamed_file"


def format_size(size_bytes: int) -> str:
    """Форматирование размера файла."""
    for unit in ['B', 'KB', 'MB', 'GB']:
        if size_bytes < 1024:
            return f"{size_bytes:.1f} {unit}"
        size_bytes /= 1024
    return f"{size_bytes:.1f} TB"


def parse_attachment_string(attachments_str: str) -> List[str]:
    """
    Парсинг строки вложений.

    Args:
        attachments_str: Строка с путями через запятую

    Returns:
        Список путей
    """
    if not attachments_str or not attachments_str.strip():
        return []

    return [path.strip() for path in attachments_str.split(',') if path.strip()]
