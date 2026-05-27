"""Точка входа приложения."""

import logging
import sys
from pathlib import Path

# Добавляем корень проекта в путь
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from core.note_manager import NoteManager, NoteNotFoundError

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("logs/app.log", encoding="utf-8")
    ]
)

logger = logging.getLogger(__name__)


def demo() -> None:
    """Демонстрация работы NoteManager."""
    # Создаём менеджер с кастомным путём
    manager = NoteManager("data/notes.json")

    print("\n=== NoteMaster - Демонстрация ===\n")

    # Создание заметок
    print("1. Создание заметок:")
    note1 = manager.create_note(
        title="Приветственное сообщение",
        content="Это первая заметка в системе NoteMaster.",
        attachments=["/docs/readme.md"]
    )
    print(f"   Создана заметка: {note1.title} (id: {note1.id[:8]}...)")

    note2 = manager.create_note(
        title="Список задач",
        content="- Изучить API\n- Написать тесты\n- Деплой",
        attachments=[]
    )
    print(f"   Создана заметка: {note2.title} (id: {note2.id[:8]}...)")

    # Получение всех заметок
    print("\n2. Все заметки:")
    all_notes = manager.get_all_notes()
    for note in all_notes:
        print(f"   - {note.title} ({note.id[:8]}...)")

    # Получение по ID
    print("\n3. Получение заметки по ID:")
    try:
        note = manager.get_note_by_id(note1.id)
        print(f"   Найдена: {note.title}")
    except NoteNotFoundError as e:
        print(f"   Ошибка: {e}")

    # Обновление заметки
    print("\n4. Обновление заметки:")
    updated = manager.update_note(
        note1.id,
        content="Обновлённое содержание первой заметки.",
        title="Приветственное сообщение (обновлено)"
    )
    print(f"   Обновлена: {updated.title}")

    # Удаление заметки
    print("\n5. Удаление заметки:")
    manager.delete_note(note2.id)
    print(f"   Удалена заметка: {note2.title}")

    # Оставшиеся заметки
    print("\n6. Оставшиеся заметки:")
    remaining = manager.get_all_notes()
    for note in remaining:
        print(f"   - {note.title}")

    print("\n=== Демонстрация завершена ===\n")


if __name__ == "__main__":
    demo()
