"""Централизованная обработка ошибок и сообщений для NoteMaster."""

from enum import Enum
from typing import Optional, Dict, Any
from dataclasses import dataclass
import logging

logger = logging.getLogger(__name__)


class ErrorCategory(Enum):
    """Категории ошибок."""
    USER_INPUT = "user_input"           # Ошибки ввода пользователя
    FILE_SYSTEM = "file_system"         # Ошибки файловой системы
    DATA_VALIDATION = "data_validation"  # Ошибки валидации данных
    SYSTEM = "system"                   # Системные ошибки
    NETWORK = "network"                 # Ошибки сети


@dataclass
class UserMessage:
    """Сообщение для пользователя."""
    title: str
    message: str
    suggestion: Optional[str] = None
    category: ErrorCategory = ErrorCategory.SYSTEM

    def format_cli(self) -> str:
        """Форматирование для CLI."""
        prefix = self._get_prefix()
        result = f"{prefix}{self.title}: {self.message}"
        if self.suggestion:
            result += f"\n💡 {self.suggestion}"
        return result

    def format_web(self) -> Dict[str, str]:
        """Форматирование для Web (JSON)."""
        return {
            "type": self.category.value,
            "title": self.title,
            "message": self.message,
            "suggestion": self.suggestion or "",
            "icon": self._get_icon()
        }

    def _get_prefix(self) -> str:
        prefixes = {
            ErrorCategory.USER_INPUT: "❌",
            ErrorCategory.FILE_SYSTEM: "📁",
            ErrorCategory.DATA_VALIDATION: "⚠️",
            ErrorCategory.SYSTEM: "🔧",
            ErrorCategory.NETWORK: "🌐"
        }
        return prefixes.get(self.category, "⚠️")

    def _get_icon(self) -> str:
        return self._get_prefix()


class ErrorRegistry:
    """Реестр предопределённых ошибок."""

    @staticmethod
    def EMPTY_TITLE():
        return UserMessage(
            title="Ошибка в поле 'title'",
            message="Заголовок не может быть пустым",
            suggestion="Введите заголовок для вашей заметки",
            category=ErrorCategory.USER_INPUT
        )

    @staticmethod
    def WHITESPACE_TITLE():
        return UserMessage(
            title="Ошибка в поле 'title'",
            message="Заголовок не может содержать только пробелы",
            suggestion="Введите осмысленный заголовок",
            category=ErrorCategory.USER_INPUT
        )

    @staticmethod
    def INVALID_ATTACHMENT(path, reason):
        return UserMessage(
            title=f"Невалидное вложение '{path}'",
            message=reason,
            suggestion="Проверьте формат пути к файлу",
            category=ErrorCategory.USER_INPUT
        )

    @staticmethod
    def NOTE_NOT_FOUND(identifier):
        return UserMessage(
            title="Заметка не найдена",
            message=f"Заметка с идентификатором '{identifier}' не найдена",
            suggestion="Проверьте правильный ID или выберите другую заметку",
            category=ErrorCategory.USER_INPUT
        )

    @staticmethod
    def EMPTY_LIST(operation):
        return UserMessage(
            title="Нет данных для обработки",
            message=f"Невозможно выполнить '{operation}' на пустом списке",
            suggestion="Создайте заметки перед выполнением этой операции",
            category=ErrorCategory.USER_INPUT
        )

    @staticmethod
    def GET_WITHOUT_ID():
        return UserMessage(
            title="Отсутствует идентификатор",
            message="Для получения заметки требуется --id",
            suggestion="Укажите ID заметки: --id <номер> или --id <uuid>",
            category=ErrorCategory.USER_INPUT
        )

    @staticmethod
    def CREATE_WITHOUT_TITLE():
        return UserMessage(
            title="Отсутствует заголовок",
            message="Для создания заметки требуется --title",
            suggestion="Укажите заголовок: --title \"Ваш заголовок\"",
            category=ErrorCategory.USER_INPUT
        )

    @staticmethod
    def UPDATE_WITHOUT_ID():
        return UserMessage(
            title="Отсутствует идентификатор",
            message="Для обновления заметки требуется --id",
            suggestion="Укажите ID заметки: --id <номер> или --id <uuid>",
            category=ErrorCategory.USER_INPUT
        )

    @staticmethod
    def DELETE_WITHOUT_ID():
        return UserMessage(
            title="Отсутствует идентификатор",
            message="Для удаления заметки требуется --id",
            suggestion="Укажите ID заметки: --id <номер> или --id <uuid>",
            category=ErrorCategory.USER_INPUT
        )

    @staticmethod
    def FILE_NOT_FOUND(path):
        return UserMessage(
            title="Файл не найден",
            message=f"Файл не существует: {path}",
            suggestion="Проверьте правильный путь к файлу",
            category=ErrorCategory.FILE_SYSTEM
        )

    @staticmethod
    def FILE_ACCESS_ERROR(path, reason):
        return UserMessage(
            title="Ошибка доступа к файлу",
            message=f"Невозможно прочитать файл: {path}",
            suggestion=reason or "Проверьте права доступа и доступность диска",
            category=ErrorCategory.FILE_SYSTEM
        )

    @staticmethod
    def FILE_TOO_LARGE(size, max_size):
        return UserMessage(
            title="Файл слишком большой",
            message=f"Размер файла {size} превышает лимит {max_size}",
            suggestion="Загрузите файл меньшего размера",
            category=ErrorCategory.FILE_SYSTEM
        )

    @staticmethod
    def INVALID_JSON():
        return UserMessage(
            title="Файл данных повреждён",
            message="JSON файл имеет некорректную структуру",
            suggestion="Попробуйте восстановить резервную копию или начать заново",
            category=ErrorCategory.DATA_VALIDATION
        )

    @staticmethod
    def INVALID_ATTACHMENT_TYPE(ext):
        return UserMessage(
            title="Неподдерживаемый формат файла",
            message=f"Расширение '{ext}' не поддерживается",
            suggestion="Используйте один из поддерживаемых форматов: PDF, DOC, XLS, изображения и т.д.",
            category=ErrorCategory.DATA_VALIDATION
        )

    @staticmethod
    def INVALID_ATTACHMENT_FORMAT(path):
        return UserMessage(
            title="Некорректный формат вложения",
            message=f"Путь '{path}' имеет неверный формат",
            suggestion="Укажите полный путь к файлу",
            category=ErrorCategory.DATA_VALIDATION
        )

    @staticmethod
    def STORAGE_ERROR(reason):
        return UserMessage(
            title="Ошибка хранения данных",
            message=f"Невозможно сохранить данные: {reason}",
            suggestion="Проверьте свободное место на диске и права доступа",
            category=ErrorCategory.SYSTEM
        )

    @staticmethod
    def BACKUP_CREATED(backup_path):
        return UserMessage(
            title="Создана резервная копия",
            message="Повреждённый файл сохранён для анализа",
            suggestion=f"Резервная копия: {backup_path}",
            category=ErrorCategory.SYSTEM
        )

    @staticmethod
    def UNKNOWN_ERROR(msg):
        return UserMessage(
            title="Произошла ошибка",
            message=msg or "Неизвестная ошибка",
            suggestion="Попробуйте повторить действие позже",
            category=ErrorCategory.SYSTEM
        )


def get_error(error_key: str, **kwargs) -> UserMessage:
    """Получить ошибку по ключу."""
    error_factory = getattr(ErrorRegistry, error_key, None)
    if not error_factory:
        return ErrorRegistry.UNKNOWN_ERROR(f"Неизвестная ошибка: {error_key}")

    if callable(error_factory):
        return error_factory(**kwargs) if kwargs else error_factory()
    return error_factory


def format_error_cli(error: UserMessage) -> str:
    """Форматировать ошибку для CLI."""
    return error.format_cli()


def format_error_web(error: UserMessage) -> Dict[str, Any]:
    """Форматировать ошибку для Web."""
    return error.format_web()


def log_error(error: UserMessage, level: str = "ERROR"):
    """Логировать ошибку."""
    log_func = getattr(logger, level.lower(), logger.error)
    log_func(f"[{error.category.value}] {error.title}: {error.message}")
