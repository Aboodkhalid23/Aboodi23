"""End to end through a real engine: the engine kit (kit.js + render.mjs, unchanged) renders a scene whose camera comes
only from the compiled Motion Score, in headless Chrome; perception measures the film; the measurement must equal the
render-free prediction. Skipped where Chrome or puppeteer-core is not available (CI).

This is the test that found the roll/translation coupling missing from predict.py and the rest-before-a-move that
perception took for a held drawing."""
import glob
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

from perception import distance, fingerprint
from score import model, predict
from score.cli import compile_js
from score.runtime import Score

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, "..", "..", "..", "..", ".."))
KIT = os.path.join(REPO, ".claude", "skills", "video-clone", "assets", "engine-kit")
CHROMES = [os.environ.get("CHROME_PATH"), r"C:/Program Files/Google/Chrome/Application/chrome.exe",
           r"C:/Program Files (x86)/Google/Chrome/Application/chrome.exe", "/usr/bin/google-chrome", "/usr/bin/chromium"]


def _puppeteer() -> str | None:
    env = os.environ.get("REELMIMIC_NODE_MODULES")
    if env and os.path.isdir(os.path.join(env, "puppeteer-core")):
        return env
    found = glob.glob(os.path.join(REPO, ".claude", "skills", "*", "template", "node_modules", "puppeteer-core")) + \
        glob.glob(os.path.join(REPO, "projects", "*", "build", "node_modules", "puppeteer-core"))
    return os.path.dirname(found[0]) if found else None


NODE_MODULES = _puppeteer()
CHROME = next((c for c in CHROMES if c and os.path.exists(c)), None)
pytestmark = pytest.mark.skipif(not (shutil.which("node") and NODE_MODULES and CHROME), reason="needs node, Chrome and puppeteer-core")

FILM = {"version": 1, "fps": 24, "bpm": 120, "offset": 0, "duration": 4, "cues": {"hit": "B6"}}
SHOTS = [
    {"id": "S1", "start": "0", "end": "B4", "camera": {"moves": [
        {"at": "S+3f", "dur": "0.75s", "by": {"zoom": 1.35}, "ease": "power3.out"},
        {"at": "B2", "dur": "0.8s", "by": {"x": 380}, "ease": {"bezier": [0.4, 0, 0.2, 1]}}]}},
    {"id": "S2", "start": "B4", "end": "4", "camera": {"base": {"x": 1100, "y": 500, "zoom": 1.2}, "moves": [
        {"at": "S+2f", "to": {"rot": 0.18}, "ease": {"spring": {"omega": 9, "zeta": 0.45}}},
        {"at": "B6", "dur": "0.5s", "by": {"y": 160}, "ease": "sine.inOut"}], "shakes": [{"at": "hit", "amp": 10, "decay": 7}]}},
]
SCENE = """
function world(seed) {
  const r = rnd('world' + seed);
  G.fillStyle = seed ? '#1d2a44' : '#3b2a1e'; G.fillRect(-1500, -1500, W + 3000, H + 3000);
  for (let i = 0; i < 900; i++) {
    const x = -1200 + r() * (W + 2400), y = -1200 + r() * (H + 2400), s = 6 + r() * 46;
    G.fillStyle = `hsl(${Math.floor(r() * 360)},${50 + r() * 40}%,${35 + r() * 45}%)`;
    G.beginPath(); if (r() < .5) G.arc(x, y, s, 0, TAU); else G.rect(x, y, s * 1.6, s); G.fill();
  }
}
shots([
  [0, (t) => { const c = Score.cam('S1', t); camBegin(c.x, c.y, c.zoom, c.rot); world(0); }],
  [2, (t) => { const c = Score.cam('S2', t); camBegin(c.x, c.y, c.zoom, c.rot); world(1); }],
]);
"""


def _link(src: str, dst: str):
    if sys.platform == "win32":
        subprocess.run(["cmd", "/c", "mklink", "/J", dst, src], check=True, capture_output=True)
    else:
        os.symlink(src, dst)


def test_engine_render_matches_prediction(tmp_path):
    d = tmp_path / "proj"
    (d / "src" / "scenes").mkdir(parents=True)
    shutil.copy(os.path.join(KIT, "render.mjs"), d)
    shutil.copy(os.path.join(KIT, "package.json"), d)
    shutil.copy(os.path.join(KIT, "kit.js"), d / "src" / "kit.js")
    html = Path(KIT, "studio.html").read_text(encoding="utf-8")
    html = html.replace("<!-- ENGINE-LIBS -->", '<script src="src/score.js"></script>').replace("<!-- SCENES -->", '<script src="src/scenes/world.js"></script>')
    (d / "studio.html").write_text(html, encoding="utf-8")
    (d / "src" / "config.js").write_text("const PROJECT = { duration: 4, bpm: 120, offset: 0, fps: 24 };", encoding="utf-8")
    (d / "src" / "scenes" / "world.js").write_text(SCENE, encoding="utf-8")
    resolved, diag = model.resolve_score({**FILM, "shots": SHOTS})
    assert diag.ok, diag.errors
    (d / "src" / "score.js").write_text(compile_js(resolved), encoding="utf-8")
    _link(NODE_MODULES, str(d / "node_modules"))
    try:
        subprocess.run(["node", "render.mjs", "--clip", "--out=out/video.mp4", f"--chrome={CHROME}"], cwd=d, check=True, capture_output=True, timeout=300)
        meas = fingerprint.extract(str(d / "out" / "video.mp4"), shots=[{"id": "S1", "start_s": 0, "end_s": 2}, {"id": "S2", "start_s": 2, "end_s": 4}])
    finally:
        if sys.platform == "win32":
            subprocess.run(["cmd", "/c", "rmdir", str(d / "node_modules")], capture_output=True)   # the junction, not its target
    pred = {p["id"]: p for p in predict.predicted_shots(Score(resolved))}
    for s in meas["shots"]:
        p = pred[s["id"]]
        assert set(s["move"]["kind"]) == set(p["move"]["kind"]), (s["id"], s["move"]["kind"], p["move"]["kind"])
        for ax in ("x", "y", "z", "r"):
            assert s["move"]["amount"][ax] == pytest.approx(p["move"]["amount"][ax], abs=0.004), (s["id"], ax)
        score, _, findings = distance.camera_pair(s, p)
        assert score > 95, (s["id"], score, json.dumps(findings))


def test_svg_camera_is_the_canvas_camera(tmp_path):
    """Score.svgCam (HyperFrames) and camBegin(...Score.cam) (canvas engines) must put every world point at the same
    screen position: checked in Chrome through the SVG's own getScreenCTM against kit.js toScreen."""
    resolved, _ = model.resolve_score({**FILM, "shots": SHOTS})
    page = tmp_path / "svg.html"
    page.write_text(f"""<!doctype html><html><body style="margin:0">
<svg id="s" width="1920" height="1080" viewBox="0 0 1920 1080"><g id="cam"><circle id="p" r="1"/></g></svg>
<script>const W = 1920, H = 1080;</script>
<script>{Path(KIT, 'kit.js').read_text(encoding='utf-8').split('// ---------- shots ----------')[0].replace('const W = 1920, H = 1080, TAU', 'const TAU').replace('const DUR = PROJECT.duration, BPM = PROJECT.bpm || 120, BEAT = 60 / BPM, OFF = PROJECT.offset || 0;', '').replace('const FPS = PROJECT.fps || 24;', '')}</script>
<script>{compile_js(resolved)}</script>
<script>
function toScreenCam(x, y, c) {{ const dx = (x - c.x) * c.zoom, dy = (y - c.y) * c.zoom, co = Math.cos(c.rot), si = Math.sin(c.rot); return [W / 2 + dx * co - dy * si, H / 2 + dx * si + dy * co]; }}
window.check = () => {{
  const out = [], g = document.getElementById('cam'), pt = document.getElementById('s').createSVGPoint();
  for (const [id, t] of [['S1', 0.3], ['S1', 1.4], ['S2', 2.4], ['S2', 3.2], ['S2', 3.9]]) {{
    g.setAttribute('transform', Score.svgCam(id, t));
    const m = g.getCTM(), c = Score.cam(id, t);
    for (const [x, y] of [[0, 0], [960, 540], [1700, 200], [300, 900]]) {{
      pt.x = x; pt.y = y; const p = pt.matrixTransform(m), q = toScreenCam(x, y, c);
      out.push(Math.hypot(p.x - q[0], p.y - q[1]));
    }}
  }}
  return out;
}};
</script></body></html>""", encoding="utf-8")
    js = tmp_path / "run.mjs"
    js.write_text(f"""import puppeteer from 'puppeteer-core';
const b = await puppeteer.launch({{ executablePath: {json.dumps(CHROME)}, headless: true }});
const p = await b.newPage(); await p.goto({json.dumps(page.as_uri())});
console.log(JSON.stringify(await p.evaluate(() => window.check()))); await b.close();""", encoding="utf-8")
    _link(NODE_MODULES, str(tmp_path / "node_modules"))
    try:
        r = subprocess.run(["node", str(js)], cwd=tmp_path, capture_output=True, text=True, timeout=120)
    finally:
        if sys.platform == "win32":
            subprocess.run(["cmd", "/c", "rmdir", str(tmp_path / "node_modules")], capture_output=True)
    assert r.returncode == 0, r.stderr
    err = json.loads(r.stdout.strip().splitlines()[-1])
    assert max(err) < 0.05, err   # pixels
