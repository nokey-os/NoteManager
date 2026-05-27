"""Тесты для CLI модуля."""

import sys
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest

# Добавляем корень проекта в путь
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


class TestCLIParsing:
    """Тесты парсинга аргументов."""

    def test_parse_attachments_empty(self):
        """Тест парсинга пустых вложений."""
        from app.cli.cli import parse_attachments
        result = parse_attachments("")
        assert result == []

    def test_parse_attachments_single(self):
        """Тест парсинга одного вложения."""
        from app.cli.cli import parse_attachments
        result = parse_attachments("/path/to/file")
        assert result == ["/path/to/file"]

    def test_parse_attachments_multiple(self):
        """Тест парсинга нескольких вложений."""
        from app.cli.cli import parse_attachments
        result = parse_attachments("/path1, /path2, /path3")
        assert result == ["/path1", "/path2", "/path3"]

    def test_parse_attachments_with_spaces(self):
        """Тест парсинга вложений с пробелами."""
        from app.cli.cli import parse_attachments
        result = parse_attachments("  /path1  ,  /path2  ")
        assert result == ["/path1", "/path2"]


class TestCLIFormat:
    """Тесты форматирования вывода."""

    def test_format_note_table_empty(self):
        """Тест форматирования пустого списка."""
        from app.cli.cli import format_note_table

        result = format_note_table([])
        assert "Нет заметок" in result

    def test_format_note_table_single(self):
        """Тест форматирования одной заметки."""
        from app.cli.cli import format_note_table

        mock_note = MagicMock()
        mock_note.id = "550e8400-e29b-41d4-a716-446655440000"
        mock_note.title = "Тестовая заметка"
        mock_note.timestamp = "2024-01-15T10:30:00"

        result = format_note_table([mock_note], show_numbers=False)

        assert "550e8400" in result
        assert "Тестовая заметка" in result
        assert "Всего: 1 заметок" in result

    def test_format_note_table_with_numbers(self):
        """Тест форматирования с порядковыми номерами."""
        from app.cli.cli import format_note_table

        mock_note = MagicMock()
        mock_note.id = "550e8400-e29b-41d4-a716-446655440000"
        mock_note.title = "Заметка"
        mock_note.timestamp = "2024-01-15T10:30:00"

        result = format_note_table([mock_note], show_numbers=True)

        assert "#    |" in result
        assert "1    |" in result
        assert "Заметка" in result

    def test_format_note_detail(self):
        """Тест форматирования деталей заметки."""
        from app.cli.cli import format_note_detail

        mock_note = MagicMock()
        mock_note.id = "test-id-123"
        mock_note.title = "Test Title"
        mock_note.content = "Test Content"
        mock_note.timestamp = "2024-01-15T10:30:00"
        mock_note.attachments = ["/file1", "/file2"]

        result = format_note_detail(mock_note)

        assert "test-id-123" in result
        assert "Test Title" in result
        assert "Test Content" in result
        assert "/file1" in result
        assert "/file2" in result

    def test_format_note_detail_no_attachments(self):
        """Тест форматирования без вложений."""
        from app.cli.cli import format_note_detail

        mock_note = MagicMock()
        mock_note.id = "test-id"
        mock_note.title = "Title"
        mock_note.content = "Content"
        mock_note.timestamp = "2024-01-15T10:30:00"
        mock_note.attachments = []

        result = format_note_detail(mock_note)

        assert "Вложений: нет" in result


class TestCLIResolveNoteId:
    """Тесты разрешения ID заметок."""

    def test_resolve_by_number(self):
        """Тест разрешения по порядковому номеру."""
        from app.cli.cli import resolve_note_id

        mock_manager = MagicMock()
        mock_note1 = MagicMock()
        mock_note1.id = "uuid-1"
        mock_note2 = MagicMock()
        mock_note2.id = "uuid-2"
        mock_manager.get_all_notes.return_value = [mock_note1, mock_note2]

        result = resolve_note_id(mock_manager, "1")
        assert result == "uuid-1"

        result = resolve_note_id(mock_manager, "2")
        assert result == "uuid-2"

    def test_resolve_by_number_out_of_range(self):
        """Тест что номер вне диапазона вызывает ошибку."""
        from app.cli.cli import resolve_note_id
        from core.note_manager import NoteNotFoundError

        mock_manager = MagicMock()
        mock_note = MagicMock()
        mock_note.id = "uuid-1"
        mock_manager.get_all_notes.return_value = [mock_note]

        with pytest.raises(NoteNotFoundError, match="не найдена"):
            resolve_note_id(mock_manager, "5")

    def test_resolve_by_empty_list(self):
        """Тест что пустой список вызывает ошибку."""
        from app.cli.cli import resolve_note_id
        from core.note_manager import NoteNotFoundError

        mock_manager = MagicMock()
        mock_manager.get_all_notes.return_value = []

        with pytest.raises(NoteNotFoundError, match="пуст"):
            resolve_note_id(mock_manager, "1")

    def test_resolve_by_full_uuid(self):
        """Тест разрешения по полному UUID."""
        from app.cli.cli import resolve_note_id

        mock_manager = MagicMock()
        mock_note = MagicMock()
        mock_note.id = "550e8400-e29b-41d4-a716-446655440000"
        mock_manager.get_all_notes.return_value = [mock_note]

        result = resolve_note_id(mock_manager, "550e8400-e29b-41d4-a716-446655440000")
        assert result == "550e8400-e29b-41d4-a716-446655440000"

    def test_resolve_by_partial_uuid(self):
        """Тест разрешения по части UUID."""
        from app.cli.cli import resolve_note_id

        mock_manager = MagicMock()
        mock_note = MagicMock()
        mock_note.id = "550e8400-e29b-41d4-a716-446655440000"
        mock_manager.get_all_notes.return_value = [mock_note]

        result = resolve_note_id(mock_manager, "550e8400")
        assert result == "550e8400-e29b-41d4-a716-446655440000"

    def test_resolve_not_found(self):
        """Тест что несуществующий ID вызывает ошибку."""
        from app.cli.cli import resolve_note_id
        from core.note_manager import NoteNotFoundError

        mock_manager = MagicMock()
        mock_note = MagicMock()
        mock_note.id = "uuid-1"
        mock_manager.get_all_notes.return_value = [mock_note]

        with pytest.raises(NoteNotFoundError, match="не найдена"):
            resolve_note_id(mock_manager, "non-existent")


class TestCLICommands:
    """Тесты команд CLI."""

    @pytest.fixture
    def mock_manager(self):
        """Создание мок менеджера."""
        manager = MagicMock()
        return manager

    def test_cmd_list(self, mock_manager, capsys):
        """Тест команды list."""
        from app.cli.cli import cmd_list

        mock_note = MagicMock()
        mock_note.id = "test-id"
        mock_note.title = "Test"
        mock_note.timestamp = "2024-01-15T10:30:00"
        mock_manager.get_all_notes.return_value = [mock_note]

        cmd_list(mock_manager)

        mock_manager.get_all_notes.assert_called_once()
        captured = capsys.readouterr()
        assert "Test" in captured.out

    def test_cmd_get_success(self, mock_manager, capsys):
        """Тест успешной команды get."""
        from app.cli.cli import cmd_get

        mock_note = MagicMock()
        mock_note.id = "test-id"
        mock_note.title = "Test"
        mock_note.content = "Content"
        mock_note.timestamp = "2024-01-15T10:30:00"
        mock_note.attachments = []

        def get_note_by_id(uuid):
            return mock_note

        mock_manager.get_note_by_id.side_effect = get_note_by_id
        mock_manager.get_all_notes.return_value = [mock_note]

        cmd_get(mock_manager, "test-id")

        mock_manager.get_note_by_id.assert_called_once_with("test-id")
        captured = capsys.readouterr()
        assert "Test" in captured.out

    def test_cmd_get_by_number(self, mock_manager, capsys):
        """Тест get по порядковому номеру."""
        from app.cli.cli import cmd_get

        mock_note = MagicMock()
        mock_note.id = "test-uuid-123"
        mock_note.title = "Test"
        mock_note.content = "Content"
        mock_note.timestamp = "2024-01-15T10:30:00"
        mock_note.attachments = []

        def get_note_by_id(uuid):
            return mock_note

        mock_manager.get_note_by_id.side_effect = get_note_by_id
        mock_manager.get_all_notes.return_value = [mock_note]

        cmd_get(mock_manager, "1")

        mock_manager.get_note_by_id.assert_called_once_with("test-uuid-123")
        captured = capsys.readouterr()
        assert "Test" in captured.out

    def test_cmd_get_not_found(self, mock_manager, capsys):
        """Тест команды get с несуществующим ID."""
        from app.cli.cli import cmd_get

        mock_manager.get_all_notes.return_value = []

        cmd_get(mock_manager, "non-existent")

        captured = capsys.readouterr()
        assert "Ошибка" in captured.out

    def test_cmd_create_success(self, mock_manager, capsys):
        """Тест успешного создания заметки."""
        from app.cli.cli import cmd_create

        mock_note = MagicMock()
        mock_note.id = "new-id"
        mock_note.title = "New Note"
        mock_note.content = "Content"
        mock_note.timestamp = "2024-01-15T10:30:00"
        mock_note.attachments = []
        mock_manager.create_note.return_value = mock_note

        cmd_create(mock_manager, "New Note", "Content", [])

        mock_manager.create_note.assert_called_once()
        captured = capsys.readouterr()
        assert "Заметка создана" in captured.out

    def test_cmd_create_validation_error(self, mock_manager, capsys):
        """Тест ошибки валидации при создании."""
        from app.cli.cli import cmd_create
        from core.errors import ValidationError

        mock_manager.create_note.side_effect = ValidationError("title", "Empty title", "Suggestion")

        cmd_create(mock_manager, "", "", [])

        captured = capsys.readouterr()
        assert "Ошибка" in captured.out or "Заметка не найдена" not in captured.out

    def test_cmd_update_success(self, mock_manager, capsys):
        """Тест успешного обновления."""
        from app.cli.cli import cmd_update

        mock_note = MagicMock()
        mock_note.id = "test-uuid"
        mock_note.title = "Updated"
        mock_note.content = "Updated Content"
        mock_note.timestamp = "2024-01-15T10:30:00"
        mock_note.attachments = []
        mock_manager.update_note.return_value = mock_note
        mock_manager.get_all_notes.return_value = [mock_note]

        cmd_update(mock_manager, "test-uuid", title="Updated")

        mock_manager.update_note.assert_called_once_with("test-uuid", title="Updated")
        captured = capsys.readouterr()
        assert "обновлена" in captured.out

    def test_cmd_update_by_number(self, mock_manager, capsys):
        """Тест обновления по номеру."""
        from app.cli.cli import cmd_update

        mock_note = MagicMock()
        mock_note.id = "test-uuid-456"
        mock_note.title = "Updated"
        mock_note.content = "Updated Content"
        mock_note.timestamp = "2024-01-15T10:30:00"
        mock_note.attachments = []
        mock_manager.update_note.return_value = mock_note
        mock_manager.get_all_notes.return_value = [mock_note]

        cmd_update(mock_manager, "1", title="Updated")

        mock_manager.update_note.assert_called_once_with("test-uuid-456", title="Updated")
        captured = capsys.readouterr()
        assert "обновлена" in captured.out

    def test_cmd_delete_success(self, mock_manager, capsys):
        """Тест успешного удаления."""
        from app.cli.cli import cmd_delete

        mock_note = MagicMock()
        mock_note.id = "test-uuid"
        mock_manager.get_all_notes.return_value = [mock_note]
        mock_manager.delete_note.return_value = True

        cmd_delete(mock_manager, "test-uuid")

        mock_manager.delete_note.assert_called_once_with("test-uuid")
        captured = capsys.readouterr()
        assert "удалена" in captured.out

    def test_cmd_delete_by_number(self, mock_manager, capsys):
        """Тест удаления по номеру."""
        from app.cli.cli import cmd_delete

        mock_note = MagicMock()
        mock_note.id = "test-uuid-789"
        mock_manager.get_all_notes.return_value = [mock_note]
        mock_manager.delete_note.return_value = True

        cmd_delete(mock_manager, "1")

        mock_manager.delete_note.assert_called_once_with("test-uuid-789")
        captured = capsys.readouterr()
        assert "удалена" in captured.out

    def test_cmd_delete_not_found(self, mock_manager, capsys):
        """Тест удаления несуществующей заметки."""
        from app.cli.cli import cmd_delete

        mock_manager.get_all_notes.return_value = []

        cmd_delete(mock_manager, "non-existent")

        captured = capsys.readouterr()
        assert "Заметка не найдена" in captured.out


class TestCLIArgParser:
    """Тесты парсера аргументов."""

    def test_argparser_list_command(self):
        """Тест аргумента --list."""
        from app.cli.cli import setup_argparser

        parser = setup_argparser()
        args = parser.parse_args(["--list"])

        assert args.list is True

    def test_argparser_create_command(self):
        """Тест аргумента --create."""
        from app.cli.cli import setup_argparser

        parser = setup_argparser()
        args = parser.parse_args(["--create", "--title", "Test"])

        assert args.create is True
        assert args.title == "Test"

    def test_argparser_update_command(self):
        """Тест аргумента --update."""
        from app.cli.cli import setup_argparser

        parser = setup_argparser()
        args = parser.parse_args(["--update", "--id", "test-id", "--title", "New"])

        assert args.update is True
        assert args.id == "test-id"
        assert args.title == "New"

    def test_argparser_delete_command(self):
        """Тест аргумента --delete."""
        from app.cli.cli import setup_argparser

        parser = setup_argparser()
        args = parser.parse_args(["--delete", "--id", "test-id"])

        assert args.delete is True
        assert args.id == "test-id"

    def test_argparser_interactive_command(self):
        """Тест аргумента --interactive."""
        from app.cli.cli import setup_argparser

        parser = setup_argparser()
        args = parser.parse_args(["--interactive"])

        assert args.interactive is True


class TestCLIIntegration:
    """Интеграционные тесты CLI."""

    @patch("app.cli.cli.NoteManager")
    @patch("app.cli.cli.sys.argv", ["cli.py", "--list"])
    def test_main_list_command(self, mock_manager_cls, capsys):
        """Тест main с командой list."""
        from app.cli.cli import main

        mock_manager = MagicMock()
        mock_manager.get_all_notes.return_value = []
        mock_manager_cls.return_value = mock_manager

        result = main()

        assert result == 0
        mock_manager.get_all_notes.assert_called_once()

    @patch("app.cli.cli.NoteManager")
    @patch("app.cli.cli.sys.argv", ["cli.py", "--get", "--id", "test-id"])
    def test_main_get_command(self, mock_manager_cls):
        """Тест main с командой get."""
        from app.cli.cli import main

        mock_manager = MagicMock()
        mock_note = MagicMock()
        mock_note.id = "test-id"
        mock_note.title = "Test"
        mock_note.content = ""
        mock_note.timestamp = "2024-01-15T10:30:00"
        mock_note.attachments = []
        mock_manager.get_note_by_id.return_value = mock_note
        mock_manager.get_all_notes.return_value = [mock_note]
        mock_manager_cls.return_value = mock_manager

        result = main()

        assert result == 0
        mock_manager.get_note_by_id.assert_called_once_with("test-id")

    @patch("app.cli.cli.NoteManager")
    @patch("app.cli.cli.sys.argv", ["cli.py", "--create", "--title", "Test"])
    def test_main_create_command(self, mock_manager_cls):
        """Тест main с командой create."""
        from app.cli.cli import main

        mock_manager = MagicMock()
        mock_note = MagicMock()
        mock_note.id = "new-id"
        mock_note.title = "Test"
        mock_note.content = ""
        mock_note.timestamp = "2024-01-15T10:30:00"
        mock_note.attachments = []
        mock_manager.create_note.return_value = mock_note
        mock_manager_cls.return_value = mock_manager

        result = main()

        assert result == 0
        mock_manager.create_note.assert_called_once()

    @patch("app.cli.cli.NoteManager")
    @patch("app.cli.cli.sys.argv", ["cli.py", "--delete", "--id", "test-id"])
    def test_main_delete_command(self, mock_manager_cls):
        """Тест main с командой delete."""
        from app.cli.cli import main

        mock_manager = MagicMock()
        mock_note = MagicMock()
        mock_note.id = "test-id"
        mock_manager.get_all_notes.return_value = [mock_note]
        mock_manager.delete_note.return_value = True
        mock_manager_cls.return_value = mock_manager

        result = main()

        assert result == 0
        mock_manager.delete_note.assert_called_once_with("test-id")

    @patch("app.cli.cli.NoteManager")
    @patch("app.cli.cli.sys.argv", ["cli.py"])
    def test_main_no_args_defaults_to_interactive(self, mock_manager_cls):
        """Тест что без аргументов запускается интерактивный режим."""
        from app.cli.cli import main

        mock_manager = MagicMock()
        mock_manager_cls.return_value = mock_manager

        with patch("app.cli.cli.run_interactive"):
            result = main()

        assert result == 0


class TestCLIValidation:
    """Тесты валидации CLI."""

    @patch("app.cli.cli.NoteManager")
    @patch("app.cli.cli.sys.argv", ["cli.py", "--get"])
    def test_get_without_id_error(self, mock_manager_cls, capsys):
        """Тест что get без ID возвращает ошибку."""
        from app.cli.cli import main

        mock_manager_cls.return_value = MagicMock()

        result = main()

        assert result == 1
        captured = capsys.readouterr()
        assert "требуется --id" in captured.out

    @patch("app.cli.cli.NoteManager")
    @patch("app.cli.cli.sys.argv", ["cli.py", "--create"])
    def test_create_without_title_error(self, mock_manager_cls, capsys):
        """Тест что create без title возвращает ошибку."""
        from app.cli.cli import main

        mock_manager_cls.return_value = MagicMock()

        result = main()

        assert result == 1
        captured = capsys.readouterr()
        assert "требуется --title" in captured.out

    @patch("app.cli.cli.NoteManager")
    @patch("app.cli.cli.sys.argv", ["cli.py", "--update"])
    def test_update_without_id_error(self, mock_manager_cls, capsys):
        """Тест что update без ID возвращает ошибку."""
        from app.cli.cli import main

        mock_manager_cls.return_value = MagicMock()

        result = main()

        assert result == 1
        captured = capsys.readouterr()
        assert "требуется --id" in captured.out

    @patch("app.cli.cli.NoteManager")
    @patch("app.cli.cli.sys.argv", ["cli.py", "--delete"])
    def test_delete_without_id_error(self, mock_manager_cls, capsys):
        """Тест что delete без ID возвращает ошибку."""
        from app.cli.cli import main

        mock_manager_cls.return_value = MagicMock()

        result = main()

        assert result == 1
        captured = capsys.readouterr()
        assert "требуется --id" in captured.out
