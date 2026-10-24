// YFG Theme System — Day/Night only
// Two themes: day (light, default) and night (dark)
// Toggle button in topbar: ☀ (day) / ☾ (night)
// Persists choice in localStorage; defaults to 'day'

(function() {
  'use strict';

  const THEMES = [
    {val: 'day', label: 'روز', icon: '☀', mode: 'light'},
    {val: 'night', label: 'شب', icon: '☾', mode: 'dark'},
  ];

  const STORAGE_KEY = 'yfg-theme';
  const DEFAULT_THEME = 'day';
  let toggleBtnEl = null;

  function init() {
    // Apply saved or default theme as early as possible
    const saved = localStorage.getItem(STORAGE_KEY) || DEFAULT_THEME;
    applyTheme(saved);

    // Wait for DOM ready, then attach to button
    const tryInit = setInterval(() => {
      if (document.body && document.getElementById('themeBtn')) {
        clearInterval(tryInit);
        attachToButton();
      }
    }, 100);

    // Safety: stop trying after 10 seconds
    setTimeout(() => clearInterval(tryInit), 10000);
  }

  function applyTheme(theme) {
    // Validate theme value
    if (!THEMES.find(t => t.val === theme)) theme = DEFAULT_THEME;
    document.documentElement.setAttribute('data-theme', theme);
    document.body?.setAttribute('data-yfg-theme', theme);
    localStorage.setItem(STORAGE_KEY, theme);
    updateButton(theme);
  }

  function toggle() {
    const current = localStorage.getItem(STORAGE_KEY) || DEFAULT_THEME;
    const next = current === 'day' ? 'night' : 'day';
    applyTheme(next);
    const tInfo = THEMES.find(t => t.val === next);
    showToast(`تم «${tInfo.label}» فعال شد`);
  }

  function updateButton(theme) {
    if (!toggleBtnEl) {
      toggleBtnEl = document.getElementById('themeBtn');
    }
    if (!toggleBtnEl) return;
    const tInfo = THEMES.find(t => t.val === theme);
    if (!tInfo) return;
    const iconEl = toggleBtnEl.querySelector('.theme-icon');
    const labelEl = toggleBtnEl.querySelector('.theme-label');
    if (iconEl) iconEl.textContent = tInfo.icon;
    if (labelEl) labelEl.textContent = tInfo.label;
    toggleBtnEl.title = `تم فعلی: ${tInfo.label} (کلیک برای تعویض)`;
  }

  function attachToButton() {
    const btn = document.getElementById('themeBtn');
    if (!btn) return;
    if (btn.dataset.themeAttached === '1') return;
    btn.dataset.themeAttached = '1';
    toggleBtnEl = btn;
    btn.addEventListener('click', (ev) => {
      ev.stopPropagation();
      toggle();
    });
    // Set initial button display
    updateButton(localStorage.getItem(STORAGE_KEY) || DEFAULT_THEME);
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
