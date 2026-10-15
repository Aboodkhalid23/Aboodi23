"""Teleprompter page for the owner: the final script on his phone or laptop while he films (studio step 10).

    python3 studio/tools/prompter.py episodes/<ep>

Writes episodes/<ep>/prompter.html from 04-script.md (and the marks in 08-shoot.md if the visual director wrote
them): big right-to-left text, smooth auto-scroll with a speed slider, tap to pause, mirror for a teleprompter
glass, a focus line, and the estimated time left. The page is published as an Artifact so he opens it from a link."""
import json
import re
import sys
from pathlib import Path

PAGE = """<title>الملقّن</title>
<style>
:root{--bg:#0E0D0C;--fg:#F4EFE6;--mute:#8C857A;--accent:#F2C230;--mark:#E2553B;color-scheme:dark}
*{box-sizing:border-box}
html,body{height:100%;margin:0;background:var(--bg);color:var(--fg)}
body{font-family:"Noto Naskh Arabic","Amiri",system-ui,sans-serif;overflow:hidden}
#stage{position:fixed;inset:0;overflow:hidden}
#text{position:absolute;inset-inline:0;padding:45vh 7vw 80vh;direction:rtl;font-size:var(--size,clamp(28px,7.5vw,56px));line-height:1.75;
  font-weight:600;will-change:transform}
#text p{margin:0 0 1.1em}
#text .mark{color:var(--mark);font-size:.6em;font-family:system-ui,sans-serif;display:block;margin:.4em 0}
.mirror #text{transform-origin:center}
.focus{position:fixed;inset-inline:0;top:38vh;height:14vh;border-block:2px solid rgba(242,194,48,.35);pointer-events:none;
  background:linear-gradient(transparent,rgba(242,194,48,.05),transparent)}
.fade{position:fixed;inset-inline:0;height:30vh;pointer-events:none}
.fade.t{top:0;background:linear-gradient(var(--bg),transparent)}.fade.b{bottom:0;background:linear-gradient(transparent,var(--bg))}
#bar{position:fixed;inset-inline:0;bottom:0;padding:10px 16px calc(10px + env(safe-area-inset-bottom,0px));display:flex;gap:10px;
  align-items:center;flex-wrap:wrap;background:rgba(14,13,12,.92);direction:rtl;font-family:system-ui,sans-serif;font-size:15px;
  transition:opacity .3s}
#bar.hide{opacity:0;pointer-events:none}
button{background:#26231F;color:var(--fg);border:1px solid #3A3630;border-radius:10px;padding:10px 14px;font-size:16px;min-height:44px}
button.go{background:var(--accent);color:#141414;border-color:var(--accent);font-weight:700}
label{display:flex;align-items:center;gap:6px;color:var(--mute)}
input[type=range]{width:120px}
#left{margin-inline-start:auto;color:var(--mute);font-variant-numeric:tabular-nums}
</style>
<div id="stage"><div id="text"></div><div class="focus"></div><div class="fade t"></div><div class="fade b"></div></div>
<div id="bar">
  <button class="go" id="play">▶ ابدي</button>
  <button id="back">⟲ رجّع</button>
  <label>السرعة <input id="speed" type="range" min="40" max="320" value="140"></label>
  <label>الخط <input id="size" type="range" min="24" max="84" value="40"></label>
  <button id="mirror">مرآة</button>
  <span id="left"></span>
</div>
<script>
const DATA = __DATA__;
const $ = (id) => document.getElementById(id);
const text = $("text");
DATA.paras.forEach((p) => { const el = document.createElement("p"); if (p.mark) { el.className = "mark"; el.textContent = "● " + p.mark; } else el.textContent = p.text; text.appendChild(el); });
let y = 0, playing = false, last = 0, mirrored = false, idle;
const wpm = () => +$("speed").value;              // words a minute: 140 ≈ his normal pace
function pxPerSec(){ const words = DATA.words, h = text.scrollHeight - innerHeight * 1.25; return h / Math.max(1, words / wpm() * 60); }
function draw(){ text.style.transform = `translateY(${-y}px)` + (mirrored ? " scaleX(-1)" : "");
  const left = Math.max(0, (text.scrollHeight - innerHeight * 1.25 - y) / pxPerSec()); $("left").textContent = `باقي ${Math.floor(left / 60)}:${String(Math.floor(left % 60)).padStart(2, "0")}`; }
function frame(t){ if (playing){ y += pxPerSec() * Math.min(0.1, (t - last) / 1000); y = Math.min(y, text.scrollHeight); draw(); } last = t; requestAnimationFrame(frame); }
requestAnimationFrame((t) => { last = t; frame(t); });
function toggle(){ playing = !playing; $("play").textContent = playing ? "❚❚ وگّف" : "▶ كمّل"; showBar(); }
function showBar(){ $("bar").classList.remove("hide"); clearTimeout(idle); if (playing) idle = setTimeout(() => $("bar").classList.add("hide"), 2500); }
$("play").onclick = (e) => { e.stopPropagation(); toggle(); };
$("back").onclick = (e) => { e.stopPropagation(); y = Math.max(0, y - innerHeight * 0.4); draw(); };
$("speed").oninput = () => draw();
$("size").oninput = (e) => { document.documentElement.style.setProperty("--size", e.target.value + "px"); draw(); };
$("mirror").onclick = (e) => { e.stopPropagation(); mirrored = !mirrored; draw(); };
$("stage").addEventListener("click", toggle);
addEventListener("keydown", (e) => { if (e.key === " "){ e.preventDefault(); toggle(); } if (e.key === "ArrowUp"){ y = Math.max(0, y - 80); draw(); } if (e.key === "ArrowDown"){ y += 80; draw(); } });
addEventListener("wheel", (e) => { y = Math.max(0, y + e.deltaY); draw(); }, {passive: true});
let ty = null; addEventListener("touchstart", (e) => { ty = e.touches[0].clientY; }, {passive: true});
addEventListener("touchmove", (e) => { if (ty == null) return; const d = ty - e.touches[0].clientY; ty = e.touches[0].clientY; y = Math.max(0, y + d); draw(); }, {passive: true});
try { navigator.wakeLock && navigator.wakeLock.request("screen").catch(() => {}); } catch (_) {}
draw();
</script>
"""


def marks(shoot: Path) -> dict[str, str]:
    """08-shoot.md lines like: - «first words of a sentence» → وگفة / ارفع صوتك / ابتسم."""
    if not shoot.exists():
        return {}
    out = {}
    for line in shoot.read_text(encoding="utf-8").splitlines():
        m = re.match(r"\s*-\s*«([^»]+)»\s*(?:→|->)\s*(.+)", line)
        if m:
            out[m[1].strip()] = m[2].strip()
    return out


def build(ep: Path) -> Path:
    script = (ep / "04-script.md")
    if not script.exists():
        script = ep / "02-draft.md"
    text = script.read_text(encoding="utf-8")
    cues = marks(ep / "08-shoot.md")
    paras = []
    for p in [p.strip() for p in re.split(r"\n\s*\n", text) if p.strip()]:
        hit = next((note for anchor, note in cues.items() if anchor in p), None)
        if hit:
            paras.append({"mark": hit})
        paras.append({"text": p})
    data = {"paras": paras, "words": len(text.split())}
    out = ep / "prompter.html"
    out.write_text(PAGE.replace("__DATA__", json.dumps(data, ensure_ascii=False).replace("</", "<\\/")), encoding="utf-8")
    return out


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("الاستخدام: python3 studio/tools/prompter.py <مجلد الحلقة>")
        sys.exit(2)
    print(f"✅ الملقّن جاهز: {build(Path(sys.argv[1]))}")
