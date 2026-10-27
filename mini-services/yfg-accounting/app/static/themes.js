// YFG Theme Switcher v2.1 — Only shows AFTER login
// 5 themes: Teal, Emerald, Copper, Night, YFG

(function() {
  'use strict';

  const THEMES = [
    {val: 'teal', label: 'تیل', color: '#0b8f89'},
    {val: 'emerald', label: 'زمردی', color: '#10b981'},
    {val: 'copper', label: 'مسی', color: '#b87333'},
    {val: 'night', label: 'شب', color: '#6366f1'},
    {val: 'yfg', label: 'YFG', color: '#0b8f89'},
  ];

  const STORAGE_KEY = 'yfg-theme';
  let switcherEl = null;
  let observer = null;

  function init() {
    // Load saved theme or default to teal
    const saved = localStorage.getItem(STORAGE_KEY) || 'teal';
    applyTheme(saved);

    // Wait for body to exist, then add switcher (hidden initially)
    const tryInit = setInterval(() => {
      if (document.body) {
        clearInterval(tryInit);
        addSwitcher();
        watchLoginState();
      }
    }, 200);
  }

  function applyTheme(theme) {
    document.documentElement.setAttribute('data-theme', theme);
    document.body?.setAttribute('data-yfg-theme', theme);
    localStorage.setItem(STORAGE_KEY, theme);

    const colors = {
      teal: '11, 143, 137',
      emerald: '16, 185, 129',
      copper: '184, 115, 51',
      night: '99, 102, 241',
      yfg: '11, 143, 137',
    };
    document.documentElement.style.setProperty('--accent-rgb', colors[theme] || colors.teal);

    // Update active button
    document.querySelectorAll('.yfg-theme-btn').forEach(btn => {
      btn.classList.toggle('active', btn.dataset.themeVal === theme);
    });
  }

  function addSwitcher() {
    if (document.querySelector('.yfg-theme-switcher')) return;

    // Load themes.css if not already loaded
    if (!document.querySelector('link[href*="themes.css"]')) {
      const link = document.createElement('link');
      link.rel = 'stylesheet';
      link.href = '/static/themes.css';
      document.head.appendChild(link);
    }

    const switcher = document.createElement('div');
    switcher.className = 'yfg-theme-switcher';
    switcher.style.display = 'none'; // Hidden until login
    switcher.innerHTML = `
      <span class="yfg-theme-switcher-label">تم</span>
      ${THEMES.map(t => `
        <button class="yfg-theme-btn" data-theme-val="${t.val}" title="${t.label}"
                style="background:${t.color};${t.val === 'yfg' ? 'background:linear-gradient(135deg, #0b8f89, #f59e0b);' : ''}"></button>
      `).join('')}
    `;

    switcher.querySelectorAll('.yfg-theme-btn').forEach(btn => {
      btn.addEventListener('click', () => {
        applyTheme(btn.dataset.themeVal);
        showToast(`تم «${THEMES.find(t => t.val === btn.dataset.themeVal).label}» فعال شد`);
      });
    });

    document.body.appendChild(switcher);
    switcherEl = switcher;

    // Set active
    const current = localStorage.getItem(STORAGE_KEY) || 'teal';
    applyTheme(current);
  }

  // Watch for login/logout state changes
  function watchLoginState() {
    // Use MutationObserver to detect when appView becomes visible
    const appView = document.getElementById('appView');
    const authView = document.getElementById('authView');

    if (!appView || !authView) {
      // Retry if elements not found yet
      setTimeout(watchLoginState, 500);
      return;
    }

    // Check every 500ms if app is visible
    const checkState = setInterval(() => {
      const isAppVisible = !appView.classList.contains('hidden');
      if (switcherEl) {
        if (isAppVisible) {
          switcherEl.style.display = 'flex'; // Show after login
        } else {
          switcherEl.style.display = 'none'; // Hide on login page
        }
      }
    }, 500);
  }

  function showToast(msg) {
    const toast = document.getElementById('toast');
    if (!toast) { console.log(msg); return; }
    toast.textContent = msg;
    toast.style.background = 'rgba(11, 143, 137, 0.9)';
    toast.classList.remove('hidden');
    clearTimeout(showToast.timer);
    showToast.timer = setTimeout(() => toast.classList.add('hidden'), 2000);
  }

  // Initialize
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else {
    init();
  }
})();
