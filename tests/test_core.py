"""Тесты для модуля NoteManager."""

import json
import pytest
from pathlib import Path

import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from models import Note
from core.note_manager import (
    NoteManager,
    NoteNotFoundError,
    NoteManagerError
)
from driver.file_driver import JSONFileDriver, FileDriverError
from core.errors import (
    EmptyTitleError,
    NoteNotFoundError as CoreNoteNotFoundError,
    EmptyListError,
    ErrorCategory,
    ValidationError
)
from core.json_recovery import JSONRecoveryManager
from core.utils import FileValidator, parse_attachment_string


# Тестовые данные
TEST_STORAGE_PATH = "data/test_notes.json"


@pytest.fixture
def clean_test_storage():
    """Очистка тестового хранилища до и после теста."""
    test_file = Path(TEST_STORAGE_PATH)
    if test_file.exists():
        test_file.unlink()
    yield
    if test_file.exists():
        test_file.unlink()


@pytest.fixture
def note_manager(clean_test_storage):
    """Создание NoteManager для тестов."""
    return NoteManager(TEST_STORAGE_PATH)


class TestNoteModel:
    """Тесты модели Note."""

    def test_note_creation(self):
        """Тест создания заметки."""
        note = Note(title="Test Note", content="Content")
        assert note.title == "Test Note"
        assert note.content == "Content"
        assert note.id is not None
        assert note.attachments == []

    def test_note_empty_title_raises(self):
        """Тест что пустой заголовок вызывает ошибку."""
        with pytest.raises(ValueError, match="Title cannot be empty"):
            Note(title="")

    def test_note_invalid_attachments_raises(self):
        """Тест что невалидные вложения вызывают ошибку."""
        with pytest.raises(TypeError, match="Attachments must be a list"):
            Note(title="Test", attachments="not a list")

    def test_note_to_dict(self):
        """Тест сериализации заметки."""
        note = Note(title="Test", content="Content", attachments=["/path/to/file"])
        data = note.to_dict()
        assert data["title"] == "Test"
        assert data["content"] == "Content"
        assert data["attachments"] == ["/path/to/file"]
        assert "id" in data
        assert "timestamp" in data

    def test_note_from_dict(self):
        """Тест десериализации заметки."""
        data = {
            "id": "test-id-123",
            "title": "Test Title",
            "content": "Test Content",
            "timestamp": "2024-01-01T00:00:00",
            "attachments": ["/file1", "/file2"]
        }
        note = Note.from_dict(data)
        assert note.id == "test-id-123"
        assert note.title == "Test Title"
        assert note.content == "Test Content"


class TestNoteManagerCRUD:
    """Тесты CRUD операций NoteManager."""

    def test_create_note(self, note_manager):
        """Тест создания заметки."""
        note = note_manager.create_note("Test Title", "Test Content")

        assert note.title == "Test Title"
        assert note.content == "Test Content"
        assert note.id is not None

        notes = note_manager.get_all_notes()
        assert len(notes) == 1
        assert notes[0].id == note.id

    def test_create_note_empty_title_raises(self, note_manager):
        """Тест что пустой заголовок вызывает ошибку."""
        with pytest.raises(EmptyTitleError):
            note_manager.create_note("")

    def test_create_note_whitespace_title_raises(self, note_manager):
        """Тест что только пробелы в заголовке вызывают ошибку."""
        with pytest.raises(EmptyTitleError):
            note_manager.create_note("   ")

    def test_create_note_with_attachments(self, note_manager):
        """Тест создания заметки с вложениями."""
        note = note_manager.create_note(
            "Test",
            "Content",
            attachments=["/path/to/file1.pdf", "/path/to/file2.docx"]
        )
        assert note.attachments == ["/path/to/file1.pdf", "/path/to/file2.docx"]

    def test_get_all_notes_empty(self, note_manager):
        """Тест получения пустого списка заметок."""
        notes = note_manager.get_all_notes()
        assert notes == []

    def test_get_all_notes_returns_copy(self, note_manager):
        """Тест что get_all_notes возвращает копию списка."""
        note_manager.create_note("Test", "Content")
        notes1 = note_manager.get_all_notes()
        notes2 = note_manager.get_all_notes()
        assert notes1 is not notes2

    def test_get_note_by_id(self, note_manager):
        """Тест получения заметки по ID."""
        note = note_manager.create_note("Test", "Content")
        found = note_manager.get_note_by_id(note.id)

        assert found.id == note.id
        assert found.title == note.title

    def test_get_note_by_id_not_found(self, note_manager):
        """Тест что несуществующий ID вызывает ошибку."""
        with pytest.raises(NoteNotFoundError):
            note_manager.get_note_by_id("non-existent-id")

    def test_update_note(self, note_manager):
        """Тест обновления заметки."""
        note = note_manager.create_note("Original Title", "Original Content")

        updated = note_manager.update_note(
            note.id,
            title="Updated Title",
            content="Updated Content"
        )

        assert updated.title == "Updated Title"
        assert updated.content == "Updated Content"

        # Проверка что изменения сохранены
        found = note_manager.get_note_by_id(note.id)
        assert found.title == "Updated Title"

    def test_update_note_partial(self, note_manager):
        """Тест частичного обновления заметки."""
        note = note_manager.create_note("Title", "Content")

        # Обновляем только заголовок
        updated = note_manager.update_note(note.id, title="New Title")

        assert updated.title == "New Title"
        assert updated.content == "Content"  # Не изменилось

    def test_update_note_empty_title_raises(self, note_manager):
        """Тест что пустой заголовок при обновлении вызывает ошибку."""
        note = note_manager.create_note("Title", "Content")

        with pytest.raises(EmptyTitleError):
            note_manager.update_note(note.id, title="")

    def test_update_note_invalid_attachments_raises(self, note_manager):
        """Тест что невалидные вложения вызывают ошибку."""
        note = note_manager.create_note("Title", "Content")

        with pytest.raises(ValidationError):
            note_manager.update_note(note.id, attachments="not a list")

    def test_update_note_empty_list_raises(self, note_manager):
        """Тест что обновление пустого списка вызывает ошибку."""
        with pytest.raises(NoteManagerError):
            note_manager.update_note("some-id", title="Test")

    def test_delete_note(self, note_manager):
        """Тест удаления заметки."""
        note = note_manager.create_note("To Delete", "Content")

        result = note_manager.delete_note(note.id)

        assert result is True
        notes = note_manager.get_all_notes()
        assert len(notes) == 0

        with pytest.raises(NoteNotFoundError):
            note_manager.get_note_by_id(note.id)

    def test_delete_note_empty_list_raises(self, note_manager):
        """Тест что удаление из пустого списка вызывает ошибку."""
        with pytest.raises(NoteManagerError):
            note_manager.delete_note("some-id")

    def test_delete_note_not_found(self, note_manager):
        """Тест что удаление несуществующей заметки вызывает ошибку."""
        note_manager.create_note("Test", "Content")

        with pytest.raises(NoteNotFoundError):
            note_manager.delete_note("non-existent-id")


class TestPersistence:
    """Тесты сохранения и загрузки данных."""

    def test_notes_persist_after_recreate(self, clean_test_storage):
        """Тест что заметки сохраняются после пересоздания менеджера."""
        # Создаём заметки
        manager1 = NoteManager(TEST_STORAGE_PATH)
        note1 = manager1.create_note("Persistent Note", "Content")

        # Создаём новый менеджер
        manager2 = NoteManager(TEST_STORAGE_PATH)
        notes = manager2.get_all_notes()

        assert len(notes) == 1
        assert notes[0].id == note1.id
        assert notes[0].title == "Persistent Note"

    def test_file_created_on_first_save(self, clean_test_storage):
        """Тест что файл создаётся при первом сохранении."""
        manager = NoteManager(TEST_STORAGE_PATH)
        assert not Path(TEST_STORAGE_PATH).exists()

        manager.create_note("Test", "Content")
        assert Path(TEST_STORAGE_PATH).exists()

    def test_load_empty_from_nonexistent_file(self, clean_test_storage):
        """Тест что загружается пустой список если файла нет."""
        manager = NoteManager(TEST_STORAGE_PATH)
        notes = manager.get_all_notes()
        assert notes == []


class TestFileDriver:
    """Тесты файлового драйвера."""

    def test_save_and_load(self, clean_test_storage):
        """Тест сохранения и загрузки данных."""
        driver = JSONFileDriver(TEST_STORAGE_PATH)
        test_data = [{"id": "1", "name": "Test"}, {"id": "2", "name": "Test2"}]

        driver.save(test_data)
        loaded = driver.load()

        assert loaded == test_data

    def test_load_nonexistent_file_returns_empty(self, clean_test_storage):
        """Тест что загрузка несуществующего файла возвращает пустой список."""
        driver = JSONFileDriver(TEST_STORAGE_PATH)
        data = driver.load()
        assert data == []

    def test_load_invalid_json_raises(self, clean_test_storage):
        """Тест что битый JSON вызывает ошибку."""
        driver = JSONFileDriver(TEST_STORAGE_PATH)

        # Создаём невалидный JSON
        with open(TEST_STORAGE_PATH, "w") as f:
            f.write("not valid json {{{")

        with pytest.raises(FileDriverError):
            driver.load()

    def test_load_non_list_json_raises(self, clean_test_storage):
        """Тест что JSON не списком вызывает ошибку."""
        driver = JSONFileDriver(TEST_STORAGE_PATH)

        with open(TEST_STORAGE_PATH, "w") as f:
            json.dump({"key": "value"}, f)

        with pytest.raises(FileDriverError):
            driver.load()


class TestErrorHandling:
    """Тесты обработки ошибок."""

    def test_empty_title_error_has_suggestion(self):
        """Тест что ошибка пустого заголовка имеет подсказку."""
        error = EmptyTitleError()
        assert error.suggestion is not None
        assert error.category == ErrorCategory.USER_INPUT

    def test_note_not_found_error_has_suggestion(self):
        """Тест что ошибка несуществующей заметки имеет подсказку."""
        error = CoreNoteNotFoundError("test-id-123")
        assert error.suggestion is not None
        assert error.category == ErrorCategory.USER_INPUT

    def test_empty_list_error_has_suggestion(self):
        """Тест что ошибка пустого списка имеет подсказку."""
        error = EmptyListError("test_operation")
        assert error.suggestion is not None


class TestJSONRecovery:
    """Тесты восстановления JSON."""

    def test_recovery_manager_validates_existing_file(self, clean_test_storage):
        """Тест валидации существующего файла."""
        # Создаём валидный файл
        with open(TEST_STORAGE_PATH, "w") as f:
            json.dump([{"id": "1", "title": "Test"}], f)

        manager = JSONRecoveryManager(TEST_STORAGE_PATH)
        is_valid, error = manager.validate_json_file()

        assert is_valid is True
        assert error is None

    def test_recovery_manager_detects_invalid_json(self, clean_test_storage):
        """Тест обнаружения битого JSON."""
        with open(TEST_STORAGE_PATH, "w") as f:
            f.write("invalid json {{{")

        manager = JSONRecoveryManager(TEST_STORAGE_PATH)
        is_valid, error = manager.validate_json_file()

        assert is_valid is False
        assert error is not None

    def test_recovery_manager_detects_wrong_structure(self, clean_test_storage):
        """Тест обнаружения неверной структуры."""
        with open(TEST_STORAGE_PATH, "w") as f:
            json.dump({"not": "a list"}, f)

        manager = JSONRecoveryManager(TEST_STORAGE_PATH)
        is_valid, error = manager.validate_json_file()

        assert is_valid is False
        assert "список" in error.lower() or "list" in error.lower()

    def test_recovery_creates_backup(self, clean_test_storage):
        """Тест создания резервной копии."""
        # Создаём файл
        with open(TEST_STORAGE_PATH, "w") as f:
            json.dump([{"id": "1", "title": "Test"}], f)

        manager = JSONRecoveryManager(TEST_STORAGE_PATH)
        backup_path = manager.create_backup()

        assert backup_path is not None
        assert Path(backup_path).exists()


class TestFileValidator:
    """Тесты валидатора файлов."""

    def test_parse_attachment_string_empty(self):
        """Тест парсинга пустой строки."""
        result = parse_attachment_string("")
        assert result == []

    def test_parse_attachment_string_whitespace(self):
        """Тест парсинга строки с пробелами."""
        result = parse_attachment_string("   ")
        assert result == []

    def test_parse_attachment_string_valid(self):
        """Тест парсинга валидной строки."""
        result = parse_attachment_string("/path1, /path2, /path3")
        assert result == ["/path1", "/path2", "/path3"]

    def test_file_validator_rejects_empty_path(self):
        """Тест что пустой путь невалиден."""
        validator = FileValidator()
        is_valid, error = validator.validate_path("")
        assert is_valid is False
        assert error is not None

    def test_file_validator_accepts_valid_extension(self):
        """Тест что валидное расширение принимается."""
        validator = FileValidator()
        is_valid, error = validator.validate_path("/test.pdf", must_exist=False)
        assert is_valid is True

    def test_file_validator_rejects_invalid_extension(self):
        """Тест что невалидное расширение отклоняется."""
        validator = FileValidator()
        is_valid, error = validator.validate_path("/test.xyz", must_exist=False)
        assert is_valid is False
