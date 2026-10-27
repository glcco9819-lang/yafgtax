// YFG Service Worker v15 — version 0.3.0.02 — full chat messenger + customers tab
const CACHE='yfg-desk-v15';
const ASSETS=['/','/static/style.css','/static/themes.css','/static/app.js','/static/performance.js','/static/enhanced.js','/static/themes.js','/static/icon.svg','/static/icon-192.png','/static/icon-512.png','/manifest.webmanifest'];

self.addEventListener('install', e => e.waitUntil(
  caches.open(CACHE).then(c => c.addAll(ASSETS)).then(() => self.skipWaiting())
));

self.addEventListener('activate', e => e.waitUntil(
  caches.keys().then(keys => Promise.all(
    keys.filter(k => k !== CACHE).map(k => caches.delete(k))
  )).then(() => self.clients.claim())
));

// Network-first strategy for HTML/JS/CSS — always check network before cache
self.addEventListener('fetch', e => {
  const u = new URL(e.request.url);
  if (e.request.method !== 'GET' || u.pathname.startsWith('/api/')) return;

  // For navigation requests and static assets, prefer network (so updates show immediately)
  e.respondWith(
    fetch(e.request).then(r => {
      if (r.ok && u.origin === location.origin) {
        const copy = r.clone();
        caches.open(CACHE).then(cache => cache.put(e.request, copy));
      }
      return r;
    }).catch(() => caches.match(e.request).then(c => c || caches.match('/')))
  );
});
