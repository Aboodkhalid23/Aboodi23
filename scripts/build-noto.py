#!/usr/bin/env python3
"""يبني تطبيق Noto المستقل (للشاشة الرئيسية) من نفس كود النسخة الي داخل Claude.

الاستخدام:
    python3 scripts/build-noto.py [مجلد الإخراج]
المصدر: studio/teleprompter-app.html  ←  الإخراج: links/noto/
بعدين ينشره GitHub Pages تلقائياً لما يوصل الفرع الرئيسي.
"""
import json, os, sys, time
from PIL import Image

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(ROOT, "studio", "teleprompter-app.html")
ICON = os.path.join(ROOT, "studio", "noto-icons", "Noto-N.png")
OUT = sys.argv[1] if len(sys.argv) > 1 else os.path.join(ROOT, "links", "noto")
os.makedirs(OUT, exist_ok=True)
ver = str(int(time.time()))

body = open(SRC, encoding="utf-8").read()
body = body.replace("<title>Noto</title>\n", "", 1)

head = f"""<!doctype html>
<html lang="ar" dir="rtl">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
<meta name="apple-mobile-web-app-capable" content="yes">
<meta name="mobile-web-app-capable" content="yes">
<meta name="apple-mobile-web-app-status-bar-style" content="black">
<meta name="robots" content="noindex, nofollow">
<link rel="manifest" href="manifest.webmanifest">
<link rel="apple-touch-icon" href="icon-180.png">
<link rel="icon" href="icon-192.png">
<title>Noto</title>
<style>body{{margin:0}}</style>
<script>if("serviceWorker" in navigator&&location.protocol==="https:"){{addEventListener("load",()=>navigator.serviceWorker.register("sw.js?v={ver}",{{updateViaCache:"none"}}).then(r=>r.update()).catch(()=>{{}}));let re=false;navigator.serviceWorker.addEventListener("controllerchange",()=>{{if(re)return;re=true;location.reload();}});}}</script>
</head>
<body>
"""
open(os.path.join(OUT, "index.html"), "w", encoding="utf-8").write(head + body + "\n</body>\n</html>\n")

manifest = {"name": "Noto", "short_name": "Noto", "lang": "ar", "dir": "rtl", "start_url": "./", "scope": "./",
            "display": "standalone", "orientation": "any", "background_color": "#0a0b0d", "theme_color": "#0a0b0d",
            "icons": [{"src": "icon-192.png", "sizes": "192x192", "type": "image/png"},
                      {"src": "icon-512.png", "sizes": "512x512", "type": "image/png"},
                      {"src": "icon-512.png", "sizes": "512x512", "type": "image/png", "purpose": "maskable"}]}
json.dump(manifest, open(os.path.join(OUT, "manifest.webmanifest"), "w", encoding="utf-8"), ensure_ascii=False)

im = Image.open(ICON).convert("RGB")
for n in (180, 192, 512):
    im.resize((n, n), Image.LANCZOS).save(os.path.join(OUT, f"icon-{n}.png"), optimize=True)

sw = """const V="noto-%s";
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
""" % ver
open(os.path.join(OUT, "sw.js"), "w", encoding="utf-8").write(sw)
print("✅ Noto انبنى بـ", OUT)
