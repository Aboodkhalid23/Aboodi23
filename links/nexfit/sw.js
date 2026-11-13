// التحديث التلقائي: يجيب أحدث نسخة من النت أول، وإذا ماكو نت يشتغل من الذاكرة
const V = 'nexfit-v15';
self.addEventListener('install', () => self.skipWaiting());
self.addEventListener('activate', e => {
  e.waitUntil(caches.keys().then(ks => Promise.all(ks.filter(k => k !== V).map(k => caches.delete(k)))).then(() => self.clients.claim()));
});
self.addEventListener('fetch', e => {
  const u = new URL(e.request.url);
  if (e.request.method !== 'GET' || u.origin !== location.origin) return;
  const isImg = /\.(jpg|jpeg|png|webp)$/i.test(u.pathname);
  if (isImg) { // الصور: تطلع فوراً من الذاكرة، وتتحدث بالخلفية
    e.respondWith(caches.open(V).then(c => c.match(e.request).then(r => { const net = fetch(e.request, { cache: 'no-cache' }).then(res => { if (res.ok) c.put(e.request, res.clone()); return res; }).catch(() => r); return r || net; })));
    return;
  }
  // الصفحة والكود: من النت دائماً (بدون ذاكرة المتصفح)، وإذا ماكو نت من الذاكرة
  e.respondWith(fetch(e.request, { cache: 'no-cache' }).then(res => { const c = res.clone(); caches.open(V).then(x => x.put(e.request, c)); return res; }).catch(() => caches.match(e.request).then(r => r || caches.match('./'))));
});
