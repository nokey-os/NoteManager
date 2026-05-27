"""CLI интерфейс для NoteMaster."""

import argparse
import logging
import sys
from datetime import datetime
from pathlib import Path
from typing import List

# Добавляем корень проекта в путь
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from core.note_manager import (
    NoteManager,
    NoteNotFoundError,
    NoteManagerError
)
from core.errors import (
    format_error_for_user,
    ValidationError
)
from core.utils import FileValidator, parse_attachment_string

# Настройка логирования
log_dir = project_root / 'logs'
log_dir.mkdir(exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(log_dir / 'cli.log', encoding='utf-8')
    ]
)

logger = logging.getLogger(__name__)

# Путь к хранилищу заметок
STORAGE_PATH = str(project_root / 'data' / 'notes.json')

# Валидатор файлов
file_validator = FileValidator()


def setup_argparser() -> argparse.ArgumentParser:
    """Создание парсера аргументов командной строки."""
    parser = argparse.ArgumentParser(
        prog="cli.py",
        description="NoteMaster CLI — управление заметками через терминал",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Примеры использования:
  python -m app.cli.cli --list
  python -m app.cli.cli --get --id 550e8400-e29b-41d4-a716-446655440000
  python -m app.cli.cli --create --title "Заметка" --content "Текст"
  python -m app.cli.cli --update --id <uuid> --title "Новый заголовок"
  python -m app.cli.cli --delete --id <uuid>
  python -m app.cli.cli --interactive
        """
    )

    # Команды
    parser.add_argument(
        "--list", "-l",
        action="store_true",
        help="Показать все заметки"
    )

    parser.add_argument(
        "--get", "-g",
        action="store_true",
        help="Получить заметку по ID"
    )

    parser.add_argument(
        "--create", "-c",
        action="store_true",
        help="Создать новую заметку"
    )

    parser.add_argument(
        "--update", "-u",
        action="store_true",
        help="Обновить существующую заметку"
    )

    parser.add_argument(
        "--delete", "-d",
        action="store_true",
        help="Удалить заметку"
    )

    parser.add_argument(
        "--interactive", "-i",
        action="store_true",
        help="Запустить интерактивный режим"
    )

    # Общие аргументы
    parser.add_argument(
        "--id",
        type=str,
        help="ID заметки (для get, update, delete)"
    )

    parser.add_argument(
        "--title",
        type=str,
        help="Заголовок заметки (для create, update)"
    )

    parser.add_argument(
        "--content",
        type=str,
        default="",
        help="Содержание заметки (для create, update)"
    )

    parser.add_argument(
        "--attachments",
        type=str,
        default="",
        help="Вложения через запятую (для create, update)"
    )

    return parser


def parse_attachments(attachments_str: str) -> List[str]:
    """
    Парсинг строки вложений.

    Args:
        attachments_str: Строка с путями через запятую

    Returns:
        Список путей
    """
    return parse_attachment_string(attachments_str)


def format_note_table(notes: List, show_numbers: bool = False) -> str:
    """
    Форматирование списка заметок в таблицу.

    Args:
        notes: Список заметок
        show_numbers: Показывать ли порядковые номера

    Returns:
        Строка с таблицей
    """
    if not notes:
        return "Нет заметок."

    # Заголовок таблицы
    if show_numbers:
        lines = [
            "=" * 90,
            f"{'#':<4} | {'UUID':<32} | {'Заголовок':<25} | {'Дата':<20}",
            "=" * 90
        ]
    else:
        lines = [
            "=" * 80,
            f"{'UUID':<36} | {'Заголовок':<25} | {'Дата':<20}",
            "=" * 80
        ]

    # Строки
    for idx, note in enumerate(notes, start=1):
        note_id = note.id[:8] + "..." if len(note.id) > 8 else note.id
        title = note.title[:23] + ".." if len(note.title) > 25 else note.title
        # Извлекаем дату из timestamp
        try:
            dt = datetime.fromisoformat(note.timestamp)
            date_str = dt.strftime("%Y-%m-%d %H:%M")
        except (ValueError, AttributeError):
            date_str = note.timestamp[:16] if note.timestamp else "N/A"

        if show_numbers:
            lines.append(f"{idx:<4} | {note_id:<32} | {title:<25} | {date_str:<20}")
        else:
            lines.append(f"{note_id:<36} | {title:<25} | {date_str:<20}")

    separator = "=" * 90 if show_numbers else "=" * 80
    lines.append(separator)
    lines.append(f"Всего: {len(notes)} заметок")

    return "\n".join(lines)


def format_note_detail(note) -> str:
    """
    Форматирование одной заметки с подробностями.

    Args:
        note: Заметка

    Returns:
        Строка с деталями
    """
    lines = [
        "=" * 50,
        f"ID:      {note.id}",
        f"Заголовок: {note.title}",
        "-" * 50,
        "Содержание:",
        note.content if note.content else "(нет содержимого)",
        "-" * 50,
    ]

    # Дата
    try:
        dt = datetime.fromisoformat(note.timestamp)
        date_str = dt.strftime("%Y-%m-%d %H:%M:%S")
    except (ValueError, AttributeError):
        date_str = note.timestamp
    lines.append(f"Дата:    {date_str}")

    # Вложения
    if note.attachments:
        lines.append("Вложения:")
        for att in note.attachments:
            icon = file_validator.get_file_icon(att)
            lines.append(f"  {icon} {att}")
    else:
        lines.append("Вложений: нет")

    lines.append("=" * 50)
    return "\n".join(lines)


def resolve_note_id(manager: NoteManager, identifier: str) -> str:
    """
    Преобразование идентификатора в UUID.

    Поддерживает:
    - UUID (полный или сокращённый)
    - Порядковый номер (1, 2, 3...)

    Args:
        manager: NoteManager instance
        identifier: Порядковый номер или UUID

    Returns:
        UUID заметки

    Raises:
        NoteNotFoundError: Если заметка не найдена
    """
    identifier = identifier.strip()

    # Проверяем, что это порядковый номер
    if identifier.isdigit():
        num = int(identifier)
        notes = manager.get_all_notes()

        if not notes:
            raise NoteNotFoundError("Список заметок пуст")

        if 1 <= num <= len(notes):
            uuid = notes[num - 1].id
            logger.debug(f"Порядковый номер {num} -> UUID {uuid[:8]}...")
            return uuid
        else:
            raise NoteNotFoundError(
                f"Заметка с номером {num} не найдена. "
                f"Доступны номера от 1 до {len(notes)}"
            )

    # Ищем по UUID (полному или частичному)
    notes = manager.get_all_notes()
    for note in notes:
        if note.id == identifier or note.id.startswith(identifier):
            logger.debug(f"UUID {identifier} -> {note.id}")
            return note.id

    raise NoteNotFoundError(
        f"Заметка с идентификатором '{identifier}' не найдена. "
        "Используйте порядковый номер (1, 2, 3...) или UUID"
    )


def cmd_list(manager: NoteManager) -> None:
    """Команда: показать все заметки."""
    logger.info("Выполняется команда: list")
    notes = manager.get_all_notes()
    print(format_note_table(notes, show_numbers=True))


def cmd_get(manager: NoteManager, note_id: str) -> None:
    """Команда: получить заметку по ID."""
    logger.info(f"Выполняется команда: get (id={note_id})")
    try:
        uuid = resolve_note_id(manager, note_id)
        note = manager.get_note_by_id(uuid)
        print(format_note_detail(note))
    except NoteNotFoundError as e:
        print(f"Ошибка: {e}")
        logger.error(f"Заметка не найдена: {note_id}")


def cmd_create(manager: NoteManager, title: str, content: str, attachments: List[str]) -> None:
    """Команда: создать заметку."""
    logger.info(f"Выполняется команда: create (title='{title}')")
    try:
        note = manager.create_note(title=title, content=content, attachments=attachments)
        print("[OK] Заметка создана:")
        print(format_note_detail(note))
        logger.info(f"Заметка создана: id={note.id}")
    except ValidationError as e:
        print(format_error_for_user(e))
        logger.error(f"Ошибка валидации при создании: {e}")
    except Exception as e:
        print(f"Ошибка: {e}")
        logger.error(f"Ошибка при создании: {e}", exc_info=True)


def cmd_update(manager: NoteManager, identifier: str, **kwargs) -> None:
    """Команда: обновить заметку."""
    logger.info(f"Выполняется команда: update (id={identifier})")
    try:
        uuid = resolve_note_id(manager, identifier)

        # Фильтруем None значения
        update_data = {k: v for k, v in kwargs.items() if v is not None}
        if not update_data:
            print("Ошибка: нет полей для обновления")
            return

        note = manager.update_note(uuid, **update_data)
        print("[OK] Заметка обновлена:")
        print(format_note_detail(note))
        logger.info(f"Заметка обновлена: id={uuid}")
    except NoteNotFoundError as e:
        print(format_error_for_user(e))
        logger.error(f"Заметка не найдена при обновлении: {identifier}")
    except ValidationError as e:
        print(format_error_for_user(e))
        logger.error(f"Ошибка валидации при обновлении: {identifier}")
    except NoteManagerError as e:
        print(format_error_for_user(e))
        logger.error(f"Ошибка менеджера при обновлении: {identifier}")
    except Exception as e:
        print(f"Ошибка: {e}")
        logger.error(f"Ошибка при обновлении: {e}", exc_info=True)


def cmd_delete(manager: NoteManager, identifier: str) -> None:
    """Команда: удалить заметку."""
    logger.info(f"Выполняется команда: delete (id={identifier})")
    try:
        uuid = resolve_note_id(manager, identifier)
        manager.delete_note(uuid)
        print(f"[OK] Заметка удалена: #{identifier} (UUID: {uuid[:8]}...)")
        logger.info(f"Заметка удалена: id={uuid}")
    except NoteNotFoundError as e:
        print(format_error_for_user(e))
        logger.error(f"Заметка не найдена при удалении: {identifier}")
    except NoteManagerError as e:
        print(format_error_for_user(e))
        logger.error(f"Ошибка менеджера при удалении: {identifier}")
    except Exception as e:
        print(f"Ошибка: {e}")
        logger.error(f"Ошибка при удалении: {e}", exc_info=True)


def run_interactive(manager: NoteManager) -> None:
    """Запуск интерактивного режима."""
    logger.info("Запуск интерактивного режима")

    while True:
        print("\n" + "=" * 40)
        print("  NoteMaster CLI — Интерактивный режим")
        print("=" * 40)
        print("1. Создать заметку")
        print("2. Показать все заметки")
        print("3. Показать заметку по ID")
        print("4. Обновить заметку")
        print("5. Удалить заметку")
        print("6. Выход")
        print("-" * 40)

        choice = input("Выберите действие (1-6): ").strip()

        if choice == "1":
            print("\n--- Создание заметки ---")
            title = input("Заголовок (обязательно): ").strip()
            if not title:
                print("Ошибка: заголовок не может быть пустым")
                continue

            content = input("Содержание (опционально): ").strip()
            attachments_str = input("Вложения через запятую (опционально): ").strip()
            attachments = parse_attachments(attachments_str)

            try:
                note = manager.create_note(title=title, content=content, attachments=attachments)
                print(f"[OK] Заметка создана: #{len(manager.get_all_notes())} (UUID: {note.id[:8]}...)")
                logger.info(f"Создана заметка: id={note.id}")
            except ValidationError as e:
                print(f"Ошибка: {e}")
                logger.error(f"Ошибка валидации: {e}")

        elif choice == "2":
            print("\n--- Все заметки ---")
            cmd_list(manager)

        elif choice == "3":
            print("\n--- Получение заметки ---")
            print("Список заметок:")
            cmd_list(manager)
            note_id = input("\nВведите номер или ID заметки: ").strip()
            if not note_id:
                print("Ошибка: ID не может быть пустым")
                continue
            cmd_get(manager, note_id)

        elif choice == "4":
            print("\n--- Обновление заметки ---")
            print("Список заметок:")
            cmd_list(manager)
            note_id = input("\nВведите номер или ID заметки: ").strip()
            if not note_id:
                print("Ошибка: ID не может быть пустым")
                continue

            print("\nПоля для обновления (оставьте пустым, чтобы не менять):")
            title = input("Новый заголовок: ").strip() or None
            content = input("Новое содержание: ").strip() or None
            attachments_str = input("Новые вложения (через запятую): ").strip() or None
            attachments = parse_attachments(attachments_str) if attachments_str else None

            update_kwargs = {}
            if title:
                update_kwargs["title"] = title
            if content:
                update_kwargs["content"] = content
            if attachments is not None:
                update_kwargs["attachments"] = attachments

            if update_kwargs:
                cmd_update(manager, note_id, **update_kwargs)
            else:
                print("Нет полей для обновления")

        elif choice == "5":
            print("\n--- Удаление заметки ---")
            print("Список заметок:")
            cmd_list(manager)
            note_id = input("\nВведите номер или ID заметки: ").strip()
            if not note_id:
                print("Ошибка: ID не может быть пустым")
                continue
            cmd_delete(manager, note_id)

        elif choice == "6":
            print("До свидания!")
            logger.info("Завершение работы CLI")
            break

        else:
            print("Неверный выбор. Попробуйте снова.")


def main() -> int:
    """
    Точка входа CLI.

    Returns:
        Код выхода (0 - успех, 1 - ошибка)
    """
    parser = setup_argparser()
    args = parser.parse_args()

    # Если нет аргументов, запускаем интерактивный режим
    if not any([args.list, args.get, args.create, args.update, args.delete, args.interactive]):
        args.interactive = True

    # Инициализация менеджера
    try:
        manager = NoteManager(STORAGE_PATH)
    except Exception as e:
        print(f"Ошибка инициализации: {e}")
        logger.error(f"Ошибка инициализации NoteManager: {e}")
        return 1

    # Обработка команд
    if args.interactive:
        run_interactive(manager)

    elif args.list:
        cmd_list(manager)

    elif args.get:
        if not args.id:
            print("Ошибка: требуется --id для команды --get")
            return 1
        cmd_get(manager, args.id)

    elif args.create:
        if not args.title:
            print("Ошибка: требуется --title для команды --create")
            return 1
        attachments = parse_attachments(args.attachments)
        cmd_create(manager, args.title, args.content, attachments)

    elif args.update:
        if not args.id:
            print("Ошибка: требуется --id для команды --update")
            return 1
        update_kwargs = {}
        if args.title:
            update_kwargs["title"] = args.title
        if args.content:
            update_kwargs["content"] = args.content
        if args.attachments:
            update_kwargs["attachments"] = parse_attachments(args.attachments)
        cmd_update(manager, args.id, **update_kwargs)

    elif args.delete:
        if not args.id:
            print("Ошибка: требуется --id для команды --delete")
            return 1
        cmd_delete(manager, args.id)

    return 0


if __name__ == "__main__":
    sys.exit(main())
