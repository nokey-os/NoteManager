"""Централизованная обработка ошибок NoteMaster."""

from enum import Enum
from typing import Optional


class ErrorCategory(Enum):
    """Категории ошибок."""
    USER_INPUT = "user_input"      # Ошибки ввода пользователя
    FILE_SYSTEM = "file_system"    # Ошибки файловой системы
    DATA_VALIDATION = "data_validation"  # Ошибки валидации данных
    SYSTEM = "system"              # Системные ошибки
    NETWORK = "network"            # Ошибки сети (для web)


class BaseNoteMasterError(Exception):
    """Базовое исключение для NoteMaster."""

    def __init__(
        self,
        message: str,
        category: ErrorCategory = ErrorCategory.SYSTEM,
        user_friendly_message: Optional[str] = None,
        suggestion: Optional[str] = None
    ):
        self.message = message
        self.category = category
        self.user_friendly_message = user_friendly_message or message
        self.suggestion = suggestion
        super().__init__(message)

    def __str__(self) -> str:
        return self.message

    def get_user_message(self) -> str:
        """Получить сообщение для пользователя."""
        result = self.user_friendly_message
        if self.suggestion:
            result += f"\n💡 {self.suggestion}"
        return result


class FileNotExistsError(BaseNoteMasterError):
    """Файл не существует."""

    def __init__(self, file_path: str, suggestion: Optional[str] = None):
        super().__init__(
            message=f"Файл не существует: {file_path}",
            category=ErrorCategory.FILE_SYSTEM,
            user_friendly_message=f"Файл не найден: {file_path}",
            suggestion=suggestion or "Проверьте правильный путь к файлу"
        )


class JSONParseError(BaseNoteMasterError):
    """Ошибка парсинга JSON."""

    def __init__(self, file_path: str, details: str):
        super().__init__(
            message=f"Ошибка парсинга JSON в {file_path}: {details}",
            category=ErrorCategory.DATA_VALIDATION,
            user_friendly_message="Файл данных повреждён",
            suggestion="Попробуйте восстановить резервную копию или начать заново"
        )


class JSONStructureError(BaseNoteMasterError):
    """Ошибка структуры JSON."""

    def __init__(self, expected: str, actual: str):
        super().__init__(
            message=f"Неверная структура JSON: ожидается {expected}, получен {actual}",
            category=ErrorCategory.DATA_VALIDATION,
            user_friendly_message="Структура данных нарушена",
            suggestion="Обратитесь к администратору для восстановления данных"
        )


class ValidationError(BaseNoteMasterError):
    """Ошибка валидации данных."""

    def __init__(self, field: str, message: str, suggestion: Optional[str] = None):
        super().__init__(
            message=f"Валидация поля '{field}' не удалась: {message}",
            category=ErrorCategory.USER_INPUT,
            user_friendly_message=f"Ошибка в поле '{field}': {message}",
            suggestion=suggestion
        )
        self.field = field
        self.suggestion = suggestion


class EmptyTitleError(ValidationError):
    """Пустой заголовок."""

    def __init__(self):
        super().__init__(
            field="title",
            message="Заголовок не может быть пустым",
            suggestion="Введите заголовок для вашей заметки"
        )


class InvalidAttachmentError(ValidationError):
    """Невалидное вложение."""

    def __init__(self, attachment: str, reason: str):
        super().__init__(
            field="attachments",
            message=f"Невалидное вложение '{attachment}': {reason}",
            suggestion="Проверьте формат пути к файлу"
        )


class NoteNotFoundError(BaseNoteMasterError):
    """Заметка не найдена."""

    def __init__(self, note_id: str, suggestion: Optional[str] = None):
        super().__init__(
            message=f"Заметка с ID '{note_id}' не найдена",
            category=ErrorCategory.USER_INPUT,
            user_friendly_message="Заметка не найдена",
            suggestion=suggestion or "Проверьте правильный ID или выберите другую заметку"
        )


class EmptyListError(BaseNoteMasterError):
    """Операция над пустым списком."""

    def __init__(self, operation: str):
        super().__init__(
            message=f"Невозможно выполнить '{operation}' на пустом списке",
            category=ErrorCategory.USER_INPUT,
            user_friendly_message="Нет данных для обработки",
            suggestion="Создайте заметки перед выполнением этой операции"
        )


class NoteManagerError(BaseNoteMasterError):
    """Базовое исключение NoteManager."""

    def __init__(self, message: str, suggestion: Optional[str] = None):
        super().__init__(
            message=message,
            category=ErrorCategory.SYSTEM,
            suggestion=suggestion
        )


class FileSystemError(BaseNoteMasterError):
    """Ошибка файловой системы."""

    def __init__(self, operation: str, file_path: str, details: str):
        super().__init__(
            message=f"Ошибка {operation} файла {file_path}: {details}",
            category=ErrorCategory.FILE_SYSTEM,
            user_friendly_message=f"Ошибка при {operation} файла",
            suggestion="Проверьте права доступа и доступность диска"
        )


class FileCorruptedError(BaseNoteMasterError):
    """Файл повреждён."""

    def __init__(self, file_path: str, backup_path: Optional[str] = None):
        super().__init__(
            message=f"Файл повреждён: {file_path}",
            category=ErrorCategory.DATA_VALIDATION,
            user_friendly_message="Файл данных повреждён",
            suggestion=f"Резервная копия сохранена в: {backup_path}" if backup_path else "Обратитесь к администратору"
        )


def format_error_for_user(error: BaseNoteMasterError) -> str:
    """Форматировать ошибку для отображения пользователю."""
    prefix = ""
    if error.category == ErrorCategory.USER_INPUT:
        prefix = "❌ "
    elif error.category == ErrorCategory.FILE_SYSTEM:
        prefix = "📁 "
    elif error.category == ErrorCategory.DATA_VALIDATION:
        prefix = "⚠️ "
    elif error.category == ErrorCategory.SYSTEM:
        prefix = "🔧 "

    return f"{prefix}{error.get_user_message()}"
