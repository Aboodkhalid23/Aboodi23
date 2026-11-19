const V="noto-1795107106";
const SHELL=["./","./index.html","./manifest.webmanifest","./icon-180.png","./icon-192.png","./icon-512.png"];
self.addEventListener("install",e=>{e.waitUntil(caches.open(V).then(c=>c.addAll(SHELL)));self.skipWaiting();});
self.addEventListener("activate",e=>{e.waitUntil(caches.keys().then(ks=>Promise.all(ks.filter(k=>k!==V).map(k=>caches.delete(k)))).then(()=>self.clients.claim()));});
self.addEventListener("fetch",e=>{
  const r=e.request;if(r.method!=="GET")return;
  const u=new URL(r.url);const font=u.host.endsWith("fonts.googleapis.com")||u.host.endsWith("fonts.gstatic.com");
  if(u.origin!==location.origin&&!font)return;
  const page=r.mode==="navigate"||u.pathname.endsWith("/")||u.pathname.endsWith(".html");
  e.respondWith(caches.open(V).then(async c=>{const hit=await c.match(r,{ignoreSearch:u.origin===location.origin});
    const net=fetch(r,page?{cache:"no-store"}:undefined).then(res=>{if(res&&(res.ok||res.type==="opaque"))c.put(r,res.clone());return res;});
    /* الصفحة نفسها: من النت أول (آخر نسخة)، وإذا ماكو نت من الذاكرة. الباقي: من الذاكرة أول */
    if(page)return net.catch(()=>hit);
    return hit||net.catch(()=>hit);}));
});
