// Background Animation - Плавающие круги

class BackgroundAnimation {
    constructor() {
        this.circles = document.querySelectorAll('.circle');
        this.init();
    }
    
    init() {
        // Добавляем случайные начальные позиции
        this.circles.forEach(circle => {
            const randomX = Math.random() * 100 - 50;
            const randomY = Math.random() * 100 - 50;
            circle.style.transform = `translate(${randomX}px, ${randomY}px)`;
        });
        
        // Запускаем анимацию
        this.animate();
    }
    
    animate() {
        const time = Date.now() * 0.001; // Время в секундах
        
        this.circles.forEach((circle, index) => {
            const baseDelay = index * 5;
            const x = Math.sin(time + baseDelay) * 30;
            const y = Math.cos(time * 0.7 + baseDelay) * 30;
            const rotation = Math.sin(time * 0.5 + baseDelay) * 45;
            
            circle.style.transform = `translate(${x}px, ${y}px) rotate(${rotation}deg)`;
        });
        
        requestAnimationFrame(() => this.animate());
    }
    
    // Уменьшаем анимацию при движении мыши (для производительности)
    reduceMotion() {
        this.circles.forEach(circle => {
            circle.style.animationDuration = '40s';
        });
    }
    
    // Увеличиваем анимацию при взаимодействии
    enhanceMotion() {
        this.circles.forEach(circle => {
            circle.style.animationDuration = '15s';
        });
    }
}

// Инициализация при загрузке
let backgroundAnim;

document.addEventListener('DOMContentLoaded', () => {
    backgroundAnim = new BackgroundAnimation();
    
    // Проверка предпочтений пользователя о снижении анимации
    const prefersReducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)');
    if (prefersReducedMotion.matches) {
        backgroundAnim.reduceMotion();
    }
    
    // Адаптация при взаимодействии с мышью
    let activityTimeout;
    document.addEventListener('mousemove', () => {
        backgroundAnim.enhanceMotion();
        clearTimeout(activityTimeout);
        activityTimeout = setTimeout(() => {
            backgroundAnim.reduceMotion();
        }, 5000);
    });
});

// Динамическое изменение цвета кругов в зависимости от времени суток
function updateTimeBasedColors() {
    const hour = new Date().getHours();
    const circles = document.querySelectorAll('.circle');
    
    let opacity = 0.1;
    
    if (hour >= 6 && hour < 12) {
        // Утро - более яркие цвета
        opacity = 0.15;
    } else if (hour >= 18 || hour < 6) {
        // Вечер/ночь - более тусклые
        opacity = 0.08;
    }
    
    circles.forEach(circle => {
        circle.style.opacity = opacity;
    });
}

updateTimeBasedColors();
setInterval(updateTimeBasedColors, 60000); // Проверка каждую минуту

console.log('%c Background animation initialized', 'color: #7CFC00; font-size: 10px;');
