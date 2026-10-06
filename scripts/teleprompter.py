#!/usr/bin/env python3
"""يحوّل السكربت لصفحة تلقين (Teleprompter) تفتحها بالموبايل أو اللابتوب وانت تصوّر.

الاستخدام:
    python3 scripts/teleprompter.py episodes/<الحلقة>/04-script.md
ينتج: نفس المجلد/teleprompter.html

بالصفحة: تمرير تلقائي، سرعة تتغير، حجم خط يتغير، وضع المراية (للزجاج)، ومسطرة قراءة.
الأزرار: مسافة = تشغيل/إيقاف، أسهم فوق/جوه = السرعة، + / - = حجم الخط، M = مراية.
"""
import html
import os
import sys


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)
    src = sys.argv[1]
    text = open(src, encoding="utf-8").read()
    blocks = []
    for para in text.split("\n\n"):
        lines = [html.escape(l.strip()) for l in para.splitlines() if l.strip()]
        if not lines:
            continue
        if len(lines) == 1 and lines[0] in ("الهوك", "السكربت", "هوك بديل"):
            blocks.append(f'<h2>{lines[0]}</h2>')
        else:
            blocks.append("<p>" + "<br>".join(lines) + "</p>")
    words = len(text.split())
    out = os.path.join(os.path.dirname(src) or ".", "teleprompter.html")
    page = TEMPLATE.replace("{{BODY}}", "\n".join(blocks)).replace("{{WORDS}}", str(words))
    open(out, "w", encoding="utf-8").write(page)
    print(f"✅ {out}  ({words} كلمة، ~{round(words / 140)} دقيقة)")


TEMPLATE = """<!doctype html>
<html lang="ar" dir="rtl"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>التلقين</title>
<style>
 *{box-sizing:border-box}
 html,body{overflow-x:hidden;max-width:100%}
 body{margin:0;background:#000;color:#fff;font-family:Tahoma,Arial,sans-serif}
 #wrap{padding:45vh 6vw;font-size:var(--fs,clamp(26px,7vw,56px));line-height:1.6;word-wrap:break-word}
 #wrap.mirror{transform:scaleX(-1)}
 h2{color:#ffd400;font-size:.7em;margin:1.5em 0 .5em}
 p{margin:0 0 1.2em}
 #ruler{position:fixed;top:40vh;left:0;right:0;height:1.8em;border-top:2px solid #ffd40088;border-bottom:2px solid #ffd40088;pointer-events:none;font-size:var(--fs,clamp(26px,7vw,56px))}
 #bar{position:fixed;bottom:0;left:0;right:0;background:#111c;display:flex;flex-wrap:wrap;gap:6px;padding:6px;justify-content:center;align-items:center;font-size:14px}
 button{background:#333;color:#fff;border:0;padding:8px 10px;border-radius:8px;font-size:14px}
</style></head><body>
<div id="ruler"></div>
<div id="wrap">{{BODY}}</div>
<div id="bar">
 <button onclick="toggle()">▶︎ / ⏸</button>
 <button onclick="sp(-0.2)">أبطأ</button><span id="s">1.0</span><button onclick="sp(0.2)">أسرع</button>
 <button onclick="fs(-4)">A-</button><button onclick="fs(4)">A+</button>
 <button onclick="document.getElementById('wrap').classList.toggle('mirror')">مراية</button>
 <span>{{WORDS}} كلمة</span>
</div>
<script>
let run=false,speed=1.0,size=Math.round(Math.min(56,Math.max(26,innerWidth*0.07))),acc=0;
function toggle(){run=!run}
function sp(d){speed=Math.max(0.2,+(speed+d).toFixed(1));document.getElementById('s').textContent=speed.toFixed(1)}
function fs(d){size=Math.max(20,size+d);document.documentElement.style.setProperty('--fs',size+'px')}
function tick(){if(run){acc+=speed*0.6;if(acc>=1){window.scrollBy(0,Math.floor(acc));acc%=1}}requestAnimationFrame(tick)}
document.addEventListener('keydown',e=>{if(e.code==='Space'){e.preventDefault();toggle()}
 if(e.key==='ArrowUp')sp(0.2);if(e.key==='ArrowDown')sp(-0.2);if(e.key==='+')fs(4);if(e.key==='-')fs(-4);
 if(e.key==='m'||e.key==='M')document.getElementById('wrap').classList.toggle('mirror')});
tick();
</script></body></html>
"""

if __name__ == "__main__":
    main()
