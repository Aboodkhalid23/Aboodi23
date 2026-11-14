// يحفظ التطبيق بالتلفون حتى يشتغل بدون إنترنت، ويجيب النسخة الجديدة إذا اكو نت
var C='tinta-v27';
self.addEventListener('install',function(e){e.waitUntil(caches.open(C).then(function(c){return c.addAll(['./','index.html','icon-180.png','icon-192.png','icon-512.png','manifest.webmanifest','config.js'])}));self.skipWaiting();});
self.addEventListener('activate',function(e){e.waitUntil(self.clients.claim());});
self.addEventListener('fetch',function(e){
  if(e.request.method!=='GET')return;
  e.respondWith(fetch(e.request,{cache:'no-cache'}).then(function(r){var cp=r.clone();caches.open(C).then(function(c){c.put(e.request,cp)});return r;}).catch(function(){return caches.match(e.request,{ignoreSearch:true}).then(function(m){return m||caches.match('index.html')})}));
});
