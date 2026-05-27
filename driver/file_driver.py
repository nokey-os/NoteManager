"""Слой работы с файловой системой."""

import json
import logging
from pathlib import Path
from typing import Any, List

logger = logging.getLogger(__name__)


class FileDriverError(Exception):
    """Базовое исключение для ошибок файлового драйвера."""
    pass


class JSONFileDriver:
    """Драйвер для работы с JSON-файлами."""

    def __init__(self, file_path: str) -> None:
        """
        Инициализация драйвера.

        Args:
            file_path: Путь к JSON-файлу
        """
        self.file_path = Path(file_path)
        self._ensure_directory()

    def _ensure_directory(self) -> None:
        """Создание директории если она не существует."""
        directory = self.file_path.parent
        if not directory.exists():
            directory.mkdir(parents=True, exist_ok=True)
            logger.info(f"Создана директория: {directory}")

    def load(self) -> List[Any]:
        """
        Загрузка данных из JSON-файла.

        Returns:
            Список данных из файла

        Raises:
            FileDriverError: При ошибках чтения или парсинга
        """
        if not self.file_path.exists():
            logger.info(f"Файл не существует, создаём новый: {self.file_path}")
            return []

        try:
            with open(self.file_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                if not isinstance(data, list):
                    error_msg = f"Неверный формат JSON: ожидается список, получен {type(data).__name__}"
                    logger.error(error_msg)
                    raise FileDriverError(error_msg)
                logger.info(f"Успешно загружено {len(data)} записей из {self.file_path}")
                return data
        except json.JSONDecodeError as e:
            error_msg = f"Ошибка парсинга JSON в {self.file_path}: {e}"
            logger.error(error_msg)
            raise FileDriverError(error_msg)
        except IOError as e:
            error_msg = f"Ошибка чтения файла {self.file_path}: {e}"
            logger.error(error_msg)
            raise FileDriverError(error_msg)

    def save(self, data: List[Any]) -> None:
        """
        Сохранение данных в JSON-файл.

        Args:
            data: Список данных для сохранения

        Raises:
            FileDriverError: При ошибках записи
        """
        try:
            with open(self.file_path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            logger.info(f"Успешно сохранено {len(data)} записей в {self.file_path}")
        except IOError as e:
            error_msg = f"Ошибка записи файла {self.file_path}: {e}"
            logger.error(error_msg)
            raise FileDriverError(error_msg)

    def exists(self) -> bool:
        """
        Проверка существования файла.

        Returns:
            True если файл существует, False иначе
        """
        return self.file_path.exists()

    def delete(self) -> bool:
        """
        Удаление файла.

        Returns:
            True если файл был удалён, False если не существовал

        Raises:
            FileDriverError: При ошибках удаления
        """
        if not self.file_path.exists():
            return False

        try:
            self.file_path.unlink()
            logger.info(f"Файл удалён: {self.file_path}")
            return True
        except IOError as e:
            error_msg = f"Ошибка удаления файла {self.file_path}: {e}"
            logger.error(error_msg)
            raise FileDriverError(error_msg)
