// ==========================================
// DARK MODE TOGGLE
// ==========================================

document.addEventListener('DOMContentLoaded', function() {
    const savedTheme = localStorage.getItem('theme');
    
    if (savedTheme === 'dark') {
        document.body.classList.add('dark-mode');
        updateToggleButton(true);
    } else if (savedTheme === 'light') {
        document.body.classList.remove('dark-mode');
        updateToggleButton(false);
    } else {
        if (window.matchMedia && window.matchMedia('(prefers-color-scheme: dark)').matches) {
            document.body.classList.add('dark-mode');
            localStorage.setItem('theme', 'dark');
            updateToggleButton(true);
        }
    }

    if (!document.getElementById('themeToggle')) {
        const toggleBtn = document.createElement('button');
        toggleBtn.id = 'themeToggle';
        toggleBtn.className = 'theme-toggle';
        toggleBtn.innerHTML = '🌙';
        toggleBtn.setAttribute('aria-label', 'Toggle Dark Mode');
        document.body.appendChild(toggleBtn);
        
        if (document.body.classList.contains('dark-mode')) {
            toggleBtn.innerHTML = '☀️';
            toggleBtn.classList.add('dark');
        }

        toggleBtn.addEventListener('click', function() {
            const isDark = document.body.classList.toggle('dark-mode');
            
            if (isDark) {
                localStorage.setItem('theme', 'dark');
                this.innerHTML = '☀️';
                this.classList.add('dark');
            } else {
                localStorage.setItem('theme', 'light');
                this.innerHTML = '🌙';
                this.classList.remove('dark');
            }
            
            updateToggleButton(isDark);
        });
    }
});

function updateToggleButton(isDark) {
    const toggle = document.getElementById('themeToggle');
    if (toggle) {
        if (isDark) {
            toggle.innerHTML = '☀️';
            toggle.classList.add('dark');
        } else {
            toggle.innerHTML = '🌙';
            toggle.classList.remove('dark');
        }
    }
}

document.addEventListener('keydown', function(e) {
    if (e.ctrlKey && e.shiftKey && (e.key === 'D' || e.key === 'd')) {
        e.preventDefault();
        const toggle = document.getElementById('themeToggle');
        if (toggle) {
            toggle.click();
        }
    }
});

console.log('🌙 Dark Mode loaded! Press Ctrl+Shift+D to toggle.');