// يخلي الصفحة تشتغل بدون إنترنت: يرجّع النسخة المحفوظة فوراً ويحدّثها من الشبكة بالخلفية
const C = 'salah-v6', FILES = ['./', 'data.js', 'manifest.webmanifest', 'icon-180.png', 'icon-512.png', 'takbir.png'];
self.addEventListener('install', e => e.waitUntil(caches.open(C).then(c => c.addAll(FILES)).then(() => self.skipWaiting())));
self.addEventListener('activate', e => e.waitUntil(self.clients.claim()));
self.addEventListener('fetch', e => {
  if (e.request.method !== 'GET') return;
  e.respondWith(caches.open(C).then(c => c.match(e.request, { ignoreSearch: true }).then(hit => {
    const net = fetch(e.request).then(r => { if (r.ok) c.put(e.request, r.clone()); return r; }).catch(() => hit);
    return hit || net;
  })));
});
