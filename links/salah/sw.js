// يخلي التطبيق يشتغل بدون إنترنت. بوجود الإنترنت ياخذ أحدث نسخة دائماً، وبدونه يرجّع النسخة المحفوظة
const C = 'salah-v25', FILES = ['./', 'data.js', 'adhkar.js', 'calc.js', 'fonts/amiri.woff2', 'fonts/ui-500.woff2', 'fonts/ui-700.woff2', 'fonts/ui-num.woff2', 'manifest.webmanifest', 'icon-180.png', 'icon-192.png', 'icon-512.png', 'takbir.png'];
self.addEventListener('install', e => e.waitUntil(caches.open(C).then(c => c.addAll(FILES)).then(() => self.skipWaiting())));
// من تتفعل نسخة جديدة فوگ نسخة قديمة: نمسح المحفوظ القديم ونعيد تحميل أي صفحة مفتوحة، حتى النسخ القديمة الي ما تعرف تحدّث نفسها
self.addEventListener('activate', e => e.waitUntil(caches.keys().then(ks => {
  const old = ks.filter(k => k !== C);
  return Promise.all(old.map(k => caches.delete(k))).then(() => self.clients.claim())
    .then(() => { if (old.length) self.clients.matchAll({ type: 'window' }).then(cs => cs.forEach(c => c.navigate(c.url).catch(() => {}))); });   // بدون انتظار، حتى ما يعلگ التفعيل
})));
self.addEventListener('fetch', e => {
  if (e.request.method !== 'GET' || new URL(e.request.url).origin !== location.origin || /version\.txt/.test(e.request.url)) return;
  e.respondWith(caches.open(C).then(c => {
    const saved = () => c.match(e.request, { ignoreSearch: true });
    const net = fetch(e.request, { cache: 'no-cache' }).then(r => { if (r.ok) c.put(e.request, r.clone()); return r; });
    const slow = new Promise(ok => setTimeout(ok, 3000)).then(saved);          // شبكة بطيئة: لا ننتظر أكثر من 3 ثواني
    return Promise.race([net, slow.then(r => r || net)]).catch(saved).then(r => r || net);
  }));
});
