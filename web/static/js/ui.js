// UI Enhancements

// File Upload Handler
class FileUploadHandler {
    constructor() {
        this.fileInput = document.getElementById('file-input');
        this.fileList = document.getElementById('file-list');
        this.attachmentsInput = document.getElementById('attachments');
        this.selectedFiles = [];
        
        if (this.fileInput) {
            this.init();
        }
    }
    
    init() {
        this.fileInput.addEventListener('change', (e) => this.handleFileSelect(e));
        
        // Инициализация существующих файлов из скрытого поля
        if (this.attachmentsInput && this.attachmentsInput.value) {
            const existingFiles = this.attachmentsInput.value.split(',').map(f => f.trim()).filter(f => f);
            existingFiles.forEach(filename => {
                this.selectedFiles.push({ name: filename, isExisting: true });
            });
            this.renderFileList();
        }
    }
    
    handleFileSelect(event) {
        const files = Array.from(event.target.files);
        
        files.forEach(file => {
            this.selectedFiles.push({
                name: file.name,
                file: file,
                isExisting: false
            });
        });
        
        this.renderFileList();
        
        // Очищаем инпут, чтобы можно было выбрать те же файлы снова
        this.fileInput.value = '';
    }
    
    removeFile(index) {
        this.selectedFiles.splice(index, 1);
        this.renderFileList();
    }
    
    renderFileList() {
        if (!this.fileList) return;
        
        this.fileList.innerHTML = '';
        
        this.selectedFiles.forEach((fileObj, index) => {
            const fileItem = document.createElement('div');
            fileItem.className = 'file-item';
            fileItem.classList.add(fileObj.isExisting ? 'file-item-existing' : 'file-item-new');
            
            const icon = this.getFileIcon(fileObj.name);
            
            fileItem.innerHTML = `
                <span class="file-item-icon">${icon}</span>
                <span class="file-item-name">${fileObj.name}</span>
                <button type="button" class="file-item-remove" onclick="window.fileHandler.removeFile(${index})">✕</button>
            `;
            
            this.fileList.appendChild(fileItem);
        });
        
        // Обновляем скрытое поле с именами файлов
        this.updateAttachmentsInput();
    }
    
    getFileIcon(filename) {
        const lowerName = filename.toLowerCase();
        if (lowerName.endsWith('.pdf')) return '📄';
        if (lowerName.match(/\.(png|jpg|jpeg|gif|svg)$/)) return '🖼️';
        if (lowerName.match(/\.(mp4|avi|mov|mkv)$/)) return '🎬';
        if (lowerName.match(/\.(zip|rar|7z|tar)$/)) return '📦';
        if (lowerName.match(/\.(xlsx|xls|csv)$/)) return '📊';
        if (lowerName.match(/\.(doc|docx)$/)) return '📝';
        if (lowerName.match(/\.(ppt|pptx)$/)) return '📽️';
        return '📎';
    }
    
    updateAttachmentsInput() {
        if (this.attachmentsInput) {
            const names = this.selectedFiles.map(f => f.name).join(', ');
            this.attachmentsInput.value = names;
        }
    }
}

// Инициализация обработчика файлов
window.fileHandler = null;

document.addEventListener('DOMContentLoaded', () => {
    window.fileHandler = new FileUploadHandler();
});

// Плавный скролл для якорных ссылок
document.querySelectorAll('a[href^="#"]').forEach(anchor => {
    anchor.addEventListener('click', function (e) {
        e.preventDefault();
        const target = document.querySelector(this.getAttribute('href'));
        if (target) {
            target.scrollIntoView({
                behavior: 'smooth',
                block: 'start'
            });
        }
    });
});

// Подсветка полей при валидации
const formInputs = document.querySelectorAll('input[required], textarea[required]');
formInputs.forEach(input => {
    input.addEventListener('invalid', function() {
        this.style.borderColor = 'var(--error)';
    });
    input.addEventListener('valid', function() {
        this.style.borderColor = 'var(--accent)';
    });
    input.addEventListener('blur', function() {
        if (!this.value) {
            this.style.borderColor = '';
        }
    });
});

// Автоматическое скрытие флеш-сообщений
const flashMessages = document.querySelectorAll('.flash');
flashMessages.forEach((flash, index) => {
    setTimeout(() => {
        flash.style.animation = 'slideOut 0.3s ease forwards';
        setTimeout(() => flash.remove(), 300);
    }, 5000 + index * 200);
});

// Добавляем анимацию исчезновения
const style = document.createElement('style');
style.textContent = `
    @keyframes slideOut {
        from {
            opacity: 1;
            transform: translateX(0);
        }
        to {
            opacity: 0;
            transform: translateX(100px);
        }
    }
`;
document.head.appendChild(style);

// Карточки заметок - эффект наведения
const noteCards = document.querySelectorAll('.note-card');
noteCards.forEach(card => {
    card.addEventListener('mouseenter', function() {
        this.style.transition = 'all 0.3s ease';
    });
});

// Кнопки - эффект нажатия
const buttons = document.querySelectorAll('.btn');
buttons.forEach(btn => {
    btn.addEventListener('mousedown', function() {
        this.style.transform = 'translateY(0)';
    });
    btn.addEventListener('mouseup', function() {
        this.style.transform = 'translateY(-2px)';
    });
});

// Консоль лог для разработчика
console.log('%c🍊 NoteMaster Web', 'color: #FF8C00; font-size: 16px; font-weight: bold;');
console.log('%cДобро пожаловать в систему управления заметками!', 'color: #7CFC00; font-size: 12px;');
