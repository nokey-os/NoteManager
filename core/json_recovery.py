"""Модуль проверки и восстановления JSON хранилища."""

import json
import logging
import shutil
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)


class JSONRecoveryManager:
    """Менеджер восстановления JSON файлов."""

    def __init__(self, file_path: str):
        """
        Инициализация менеджера восстановления.

        Args:
            file_path: Путь к JSON файлу
        """
        self.file_path = Path(file_path)
        self.backup_path = Path(str(file_path).replace('.json', '_backup.json'))

    def validate_json_file(self) -> Tuple[bool, Optional[str]]:
        """
        Валидация JSON файла.

        Returns:
            (is_valid, error_message)
        """
        if not self.file_path.exists():
            return True, None  # Файл не существует - ок (создадим новый)

        # Попытка чтения
        try:
            with open(self.file_path, 'r', encoding='utf-8') as f:
                content = f.read()
        except IOError as e:
            return False, f"Ошибка чтения файла: {e}"

        # Попытка парсинга
        try:
            data = json.loads(content)
        except json.JSONDecodeError as e:
            return False, f"Ошибка парсинга JSON: {e}"

        # Проверка структуры
        if not isinstance(data, list):
            return False, f"Ожидается список, получен {type(data).__name__}"

        # Валидация элементов (если это заметки)
        for idx, item in enumerate(data):
            if not isinstance(item, dict):
                return False, f"Элемент {idx} должен быть объектом, получен {type(item).__name__}"

            # Проверка обязательных полей для заметки
            required_fields = ['id', 'title']
            for field in required_fields:
                if field not in item:
                    logger.warning(f"Поле '{field}' отсутствует в элементе {idx}")

        return True, None

    def validate_note_structure(self, note_data: Dict[str, Any]) -> Tuple[bool, List[str]]:
        """
        Валидация структуры заметки.

        Args:
            note_data: Словарь с данными заметки

        Returns:
            (is_valid, list_of_errors)
        """
        errors = []

        # Обязательные поля
        if 'id' not in note_data:
            errors.append("Отсутствует поле 'id'")
        elif not isinstance(note_data['id'], str):
            errors.append("Поле 'id' должно быть строкой")

        if 'title' not in note_data:
            errors.append("Отсутствует поле 'title'")
        elif not isinstance(note_data['title'], str):
            errors.append("Поле 'title' должно быть строкой")

        # Опциональные поля
        if 'content' in note_data and not isinstance(note_data['content'], str):
            errors.append("Поле 'content' должно быть строкой")

        if 'timestamp' in note_data and not isinstance(note_data['timestamp'], str):
            errors.append("Поле 'timestamp' должно быть строкой")

        if 'attachments' in note_data:
            if not isinstance(note_data['attachments'], list):
                errors.append("Поле 'attachments' должно быть списком")
            elif not all(isinstance(att, str) for att in note_data['attachments']):
                errors.append("Все элементы 'attachments' должны быть строками")

        return len(errors) == 0, errors

    def create_backup(self) -> Optional[str]:
        """
        Создание резервной копии файла.

        Returns:
            Путь к резервной копии или None
        """
        if not self.file_path.exists():
            return None

        try:
            # Добавляем временную метку к имени бэкапа
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            backup_name = self.file_path.stem + f'_backup_{timestamp}.json'
            backup_path = self.file_path.parent / backup_name

            shutil.copy2(self.file_path, backup_path)
            logger.info(f"Создана резервная копия: {backup_path}")
            return str(backup_path)

        except IOError as e:
            logger.error(f"Не удалось создать резервную копию: {e}")
            return None

    def recover_file(self) -> Tuple[bool, Optional[str]]:
        """
        Попытка восстановления файла.

        Returns:
            (success, message)
        """
        if not self.file_path.exists():
            return True, "Файл не существует, создадим новый"

        # Создаём резервную копию перед восстановлением
        backup_path = self.create_backup()

        try:
            # Чтение и парсинг
            with open(self.file_path, 'r', encoding='utf-8') as f:
                content = f.read()

            data = json.loads(content)

            # Если это не список - создаём новый
            if not isinstance(data, list):
                logger.warning("Неверная структура JSON, создаём новый файл")
                self._create_empty_file()
                return True, "Создан новый файл (старый не был списком)"

            # Фильтрация невалидных элементов
            valid_items = []
            invalid_count = 0

            for idx, item in enumerate(data):
                if isinstance(item, dict):
                    is_valid, _ = self.validate_note_structure(item)
                    if is_valid:
                        valid_items.append(item)
                    else:
                        invalid_count += 1
                        logger.warning(f"Элемент {idx} удалён за невалидность")
                else:
                    invalid_count += 1

            # Сохранение восстановленных данных
            if invalid_count > 0:
                with open(self.file_path, 'w', encoding='utf-8') as f:
                    json.dump(valid_items, f, indent=2, ensure_ascii=False)
                logger.info(f"Восстановлено: {len(valid_items)} элементов, удалено: {invalid_count}")

            return True, f"Восстановлено {len(valid_items)} элементов"

        except json.JSONDecodeError as e:
            logger.error(f"Невозможно восстановить файл: {e}")
            self._create_empty_file()
            return False, f"Файл повреждён, создан новый. Бэкап: {backup_path}"

        except IOError as e:
            logger.error(f"Ошибка при восстановлении: {e}")
            self._create_empty_file()
            return False, f"Ошибка доступа к файлу. Бэкап: {backup_path}"

    def _create_empty_file(self) -> None:
        """Создание пустого JSON файла."""
        self.file_path.parent.mkdir(parents=True, exist_ok=True)
        with open(self.file_path, 'w', encoding='utf-8') as f:
            json.dump([], f, indent=2, ensure_ascii=False)
        logger.info(f"Создан новый пустой файл: {self.file_path}")

    def check_and_recovery(self) -> Dict[str, Any]:
        """
        Проверка и автоматическое восстановление.

        Returns:
            Статус проверки
        """
        result = {
            'status': 'ok',
            'file_exists': False,
            'is_valid': False,
            'recovery_needed': False,
            'recovery_success': False,
            'message': '',
            'backup_created': False,
            'backup_path': None
        }

        # Проверка существования
        result['file_exists'] = self.file_path.exists()

        if not result['file_exists']:
            result['is_valid'] = True
            result['message'] = 'Файл не существует (будет создан при первой записи)'
            return result

        # Валидация
        is_valid, error_msg = self.validate_json_file()
        result['is_valid'] = is_valid

        if is_valid:
            result['message'] = 'Файл валиден'
            return result

        # Требуется восстановление
        result['recovery_needed'] = True
        result['status'] = 'warning'
        result['message'] = f'Файл требует восстановления: {error_msg}'

        # Попытка восстановления
        recovery_success, recovery_msg = self.recover_file()
        result['recovery_success'] = recovery_success

        if recovery_success:
            result['message'] = recovery_msg
            result['status'] = 'recovered'
        else:
            result['status'] = 'error'

        return result


def safe_json_loads(file_path: str) -> Tuple[List[Any], Optional[str]]:
    """
    Безопасная загрузка JSON с автоматическим восстановлением.

    Args:
        file_path: Путь к файлу

    Returns:
        (data, error_message)
    """
    recovery_manager = JSONRecoveryManager(file_path)
    status = recovery_manager.check_and_recovery()

    if status['status'] == 'error':
        return [], status['message']

    if not Path(file_path).exists():
        return [], None

    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        return data if isinstance(data, list) else [], None
    except Exception as e:
        return [], f"Ошибка загрузки: {e}"
