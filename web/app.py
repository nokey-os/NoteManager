"""Web интерфейс для NoteMaster на Flask."""

import logging
import os
import sys
from pathlib import Path

from flask import Flask, render_template, request, redirect, url_for, flash, send_file

# Добавляем корень проекта в путь
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from core.note_manager import NoteManager, NoteNotFoundError, ValidationError, NoteManagerError
from core.errors import format_error_for_user
from core.utils import FileValidator
from core.file_manager import FileManager

# Настройка логирования
log_dir = project_root / 'logs'
log_dir.mkdir(exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(log_dir / 'web.log', encoding='utf-8')
    ]
)

logger = logging.getLogger(__name__)

# Создание приложения Flask
app = Flask(__name__)
app.secret_key = os.environ.get('NOTEMASTER_SECRET_KEY', 'change-this-secret-key-in-production')

# Настройка директории для загруженных файлов
UPLOAD_FOLDER = project_root / 'web' / 'static' / 'uploads'
UPLOAD_FOLDER.mkdir(parents=True, exist_ok=True)
app.config['UPLOAD_FOLDER'] = str(UPLOAD_FOLDER)
app.config['MAX_CONTENT_LENGTH'] = 50 * 1024 * 1024  # 50MB макс

# Инициализация NoteManager и FileManager
STORAGE_PATH = str(project_root / 'data' / 'notes.json')
note_manager = NoteManager(STORAGE_PATH)
file_manager = FileManager(str(UPLOAD_FOLDER), max_size_mb=50)

logger.info(f"NoteManager инициализирован с путём: {STORAGE_PATH}")
logger.info(f"FileManager инициализирован: {UPLOAD_FOLDER}")

# Валидатор файлов
file_validator = FileValidator()


# === Маршруты ===

@app.route('/uploads/<filename>')
def uploaded_file(filename):
    """Отдача загруженных файлов для предпросмотра."""
    # Проверка существования файла через FileManager
    if not file_manager.file_exists(filename):
        logger.warning(f"Файл не найден: {filename}")
        flash('Файл не найден', 'error')
        return redirect(url_for('index'))

    file_path = file_manager.get_file_path(filename)

    # Определяем MIME тип
    if filename.lower().endswith('.pdf'):
        mimetype = 'application/pdf'
    elif filename.lower().endswith(('.png', 'jpg', '.jpeg', '.gif')):
        mimetype = f'image/{filename.split(".")[-1].lower()}'
    elif filename.lower().endswith('.txt'):
        mimetype = 'text/plain'
    else:
        mimetype = 'application/octet-stream'

    return send_file(file_path, mimetype=mimetype, as_attachment=False)


@app.route('/')
def index():
    """Главная страница - список всех заметок."""
    logger.info("GET / - Получение списка заметок")
    try:
        notes = note_manager.get_all_notes()
        # Сортируем по убыванию даты создания
        notes_sorted = sorted(notes, key=lambda n: n.timestamp, reverse=True)
        logger.info(f"Найдено {len(notes_sorted)} заметок")
        return render_template('index.html', notes=notes_sorted)
    except Exception as e:
        logger.error(f"Ошибка получения заметок: {e}")
        flash('Ошибка при загрузке заметок', 'error')
        return render_template('index.html', notes=[])


@app.route('/note/<note_id>')
def view_note(note_id):
    """Просмотр заметки по ID."""
    logger.info(f"GET /note/{note_id} - Просмотр заметки")
    try:
        note = note_manager.get_note_by_id(note_id)
        logger.info(f"Заметка найдена: {note.title}")

        # Проверяем существование файлов вложений через FileManager
        attachments_with_status = []
        for att in note.attachments:
            file_info = file_manager.get_file_info(att)
            if file_info:
                attachments_with_status.append({
                    'name': att,
                    'exists': True,
                    'size': file_info['size_formatted'],
                    'icon': file_validator.get_file_icon(att)
                })
            else:
                attachments_with_status.append({
                    'name': att,
                    'exists': False,
                    'size': None,
                    'icon': file_validator.get_file_icon(att)
                })

        return render_template('note.html', note=note, attachments_with_status=attachments_with_status)
    except NoteNotFoundError:
        logger.warning(f"Заметка не найдена: {note_id}")
        flash('Заметка не найдена', 'error')
        return redirect(url_for('index'))
    except Exception as e:
        logger.error(f"Ошибка просмотра заметки: {e}", exc_info=True)
        flash('Ошибка при загрузке заметки', 'error')
        return redirect(url_for('index'))


@app.route('/add', methods=['GET', 'POST'])
def add_page():
    """Страница добавления заметки."""
    if request.method == 'POST':
        logger.info("POST /add - Создание новой заметки")
        try:
            title = request.form.get('title', '').strip()
            content = request.form.get('content', '').strip()

            # Валидация заголовка
            if not title:
                flash('Заголовок не может быть пустым', 'error')
                return render_template('form.html', note=None, error="Заголовок не может быть пустым")

            # Обработка загруженных файлов через FileManager
            attachments = []
            if 'file-input' in request.files:
                files = request.files.getlist('file-input')
                for file in files:
                    if file and file.filename:
                        # Проверка размера
                        file.seek(0, 2)  # Seek to end
                        file_size = file.tell()
                        file.seek(0)  # Reset to beginning

                        if file_size > file_manager.max_size_bytes:
                            flash(f'Файл {file.filename} слишком большой (макс. 50MB)', 'error')
                            continue

                        # Сохранение файла через FileManager
                        success, saved_filename, error = file_manager.save_file(
                            file, file.filename, note_id=None
                        )

                        if success:
                            attachments.append(saved_filename)
                            logger.info(f"Файл сохранён: {saved_filename}")
                        else:
                            logger.error(f"Ошибка сохранения файла {file.filename}: {error}")
                            flash(f'Ошибка сохранения файла {file.filename}: {error}', 'error')

            note = note_manager.create_note(
                title=title,
                content=content,
                attachments=attachments
            )

            logger.info(f"Заметка создана: id={note.id}, title='{note.title}'")
            flash(f'Заметка "{note.title}" успешно создана!', 'success')
            return redirect(url_for('index'))

        except ValidationError as e:
            logger.error(f"Ошибка валидации при создании: {e}")
            flash(format_error_for_user(e), 'error')
        except Exception as e:
            logger.error(f"Ошибка при создании заметки: {e}", exc_info=True)
            flash('Ошибка при создании заметки', 'error')

        return render_template('form.html', note=None)

    logger.info("GET /add - Страница создания заметки")
    return render_template('form.html', note=None, error=None)


@app.route('/edit/<note_id>', methods=['GET', 'POST'])
def edit_note(note_id):
    """Страница редактирования заметки."""
    if request.method == 'POST':
        logger.info(f"POST /edit/{note_id} - Обновление заметки")

        # Получаем заметку
        try:
            note = note_manager.get_note_by_id(note_id)
        except NoteNotFoundError:
            logger.warning(f"Заметка не найдена для редактирования: {note_id}")
            flash('Заметка не найдена', 'error')
            return redirect(url_for('index'))

        try:
            title = request.form.get('title', '').strip()
            content = request.form.get('content', '').strip()

            # Валидация заголовка
            if not title:
                flash('Заголовок не может быть пустым', 'error')
                return render_template('form.html', note=note, error="Заголовок не может быть пустым")

            # Обработка загруженных файлов через FileManager
            attachments = list(note.attachments)  # Копия существующих
            deleted_files = []

            if 'file-input' in request.files:
                files = request.files.getlist('file-input')
                for file in files:
                    if file and file.filename:
                        # Проверка размера
                        file.seek(0, 2)
                        file_size = file.tell()
                        file.seek(0)

                        if file_size > file_manager.max_size_bytes:
                            flash(f'Файл {file.filename} слишком большой (макс. 50MB)', 'error')
                            continue

                        # Сохранение файла
                        success, saved_filename, error = file_manager.save_file(
                            file, file.filename, note_id=note_id
                        )

                        if success:
                            if saved_filename not in attachments:
                                attachments.append(saved_filename)
                            logger.info(f"Новый файл сохранён: {saved_filename}")
                        else:
                            logger.error(f"Ошибка сохранения файла {file.filename}: {error}")
                            flash(f'Ошибка сохранения файла {file.filename}: {error}', 'error')

            # Обновляем только изменённые поля
            update_data = {}
            if title != note.title:
                update_data['title'] = title
            if content != note.content:
                update_data['content'] = content
            if attachments != note.attachments:
                update_data['attachments'] = attachments
                # Удаляем файлы которые больше не прикреплены
                deleted_files = [f for f in note.attachments if f not in attachments]

            if update_data:
                updated_note = note_manager.update_note(note_id, **update_data)
                logger.info(f"Заметка обновлена: id={note_id}")

                # Физическое удаление файлов
                if deleted_files:
                    file_manager.delete_files(deleted_files)

                flash(f'Заметка "{updated_note.title}" успешно обновлена!', 'success')
            else:
                flash('Изменений не внесено', 'info')

            return redirect(url_for('view_note', note_id=note_id))

        except ValidationError as e:
            logger.error(f"Ошибка валидации при обновлении: {e}")
            flash(format_error_for_user(e), 'error')
        except NoteManagerError as e:
            logger.error(f"Ошибка менеджера при обновлении: {e}")
            flash(str(e), 'error')
        except Exception as e:
            logger.error(f"Ошибка при обновлении заметки: {e}", exc_info=True)
            flash('Ошибка при обновлении заметки', 'error')

        return render_template('form.html', note=note)

    logger.info(f"GET /edit/{note_id} - Страница редактирования")
    try:
        note = note_manager.get_note_by_id(note_id)
        return render_template('form.html', note=note, error=None)
    except NoteNotFoundError:
        logger.warning(f"Заметка не найдена для редактирования: {note_id}")
        flash('Заметка не найдена', 'error')
        return redirect(url_for('index'))


@app.route('/delete/<note_id>', methods=['POST'])
def delete_note(note_id):
    """Удаление заметки."""
    logger.info(f"POST /delete/{note_id} - Удаление заметки")
    try:
        note = note_manager.get_note_by_id(note_id)
        note_manager.delete_note(note_id)
        logger.info(f"Заметка удалена: id={note_id}, title='{note.title}'")
        flash(f'Заметка "{note.title}" успешно удалена!', 'success')
    except NoteNotFoundError:
        logger.warning(f"Заметка не найдена для удаления: {note_id}")
        flash('Заметка не найдена', 'error')
    except NoteManagerError as e:
        logger.error(f"Ошибка при удалении: {e}")
        flash(str(e), 'error')
    except Exception as e:
        logger.error(f"Неожиданная ошибка при удалении: {e}", exc_info=True)
        flash('Ошибка при удалении заметки', 'error')

    return redirect(url_for('index'))


# === Обработчики ошибок ===

@app.errorhandler(404)
def not_found(error):
    """Обработка ошибки 404."""
    logger.warning(f"Страница не найдена: {request.path}")
    return render_template('index.html', notes=[], error="Страница не найдена"), 404


@app.errorhandler(500)
def internal_error(error):
    """Обработка ошибки 500."""
    logger.error(f"Внутренняя ошибка сервера: {error}", exc_info=True)
    return render_template('index.html', notes=[], error="Внутренняя ошибка сервера"), 500


@app.errorhandler(Exception)
def handle_exception(e):
    """Обработка всех остальных исключений."""
    logger.error(f"Необработанное исключение: {e}", exc_info=True)
    return render_template('index.html', notes=[], error="Произошла ошибка"), 500


# === Запуск приложения ===

if __name__ == '__main__':
    logger.info("Запуск веб-приложения NoteMaster...")
    debug_mode = os.environ.get('NOTEMASTER_DEBUG', 'false').lower() == 'true'
    app.run(debug=debug_mode, host='0.0.0.0', port=5000)
