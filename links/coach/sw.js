// التطبيق انتقل لـ ../nexfit/. هذا يمسح النسخة القديمة من الموبايل وينقلك للجديدة
self.addEventListener('install', () => self.skipWaiting());
self.addEventListener('activate', e => {
  e.waitUntil((async () => {
    for (const k of await caches.keys()) await caches.delete(k);
    await self.clients.claim();
    for (const c of await self.clients.matchAll({ type: 'window' })) { try { c.navigate(new URL('../nexfit/', self.registration.scope).href); } catch (er) {} }
    await self.registration.unregister();
  })());
});
self.addEventListener('fetch', e => { if (e.request.mode === 'navigate') e.respondWith(Response.redirect(new URL('../nexfit/', self.registration.scope).href, 302)); });
