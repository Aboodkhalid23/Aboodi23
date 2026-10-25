// score.js — the Motion Score runtime (docs/COMPILER.md, stage 2). Evaluates a *resolved* score: every time already in
// seconds, every move a segment { t0, t1, v0, v1, ease }. Parsing and checking happen in scripts/score/ (Python);
// this file only evaluates, and must give the same numbers as scripts/score/runtime.py (tests/test_score.py checks).
//
//   Score.load(resolved)
//   Score.cam(id, t)        → { x, y, zoom, rot, rotDeg }   t = film time; canvas: camBegin(c.x, c.y, c.zoom, c.rot)
//   Score.camLocal(id, lt)  → same with time inside the shot (HyperFrames compositions)
//   Score.svgCamLocal(id, lt) → that camera as an SVG transform: S.cam.setAttribute('transform', …)
//   Score.track(id, name, t), Score.cue(name), Score.beat(n), Score.held(id, t)  (cadence: on twos → 12 drawings/s)
//   Score.shot(id)          → { start, end, cadence, ref_shot }
// Pure functions of t: safe for parallel, out-of-order frame rendering.
(function (root) {
  const clamp = (x, a = 0, b = 1) => Math.max(a, Math.min(b, x));
  const hash = (i) => { const x = Math.sin(i * 127.1 + 311.7) * 43758.5453; return x - Math.floor(x); };

  // ---------- eases (GSAP's formulas, the same table as perception/curves.py) ----------
  const pw = (p) => ({ in: (u) => u ** p, out: (u) => 1 - (1 - u) ** p, inOut: (u) => (u < 0.5 ? (2 * u) ** p / 2 : 1 - (2 * (1 - u)) ** p / 2) });
  const NAMED = { none: (u) => u };
  for (const n of [1, 2, 3, 4]) for (const [k, f] of Object.entries(pw(n + 1))) NAMED[`power${n}.${k}`] = f;
  Object.assign(NAMED, {
    'sine.in': (u) => 1 - Math.cos((u * Math.PI) / 2), 'sine.out': (u) => Math.sin((u * Math.PI) / 2), 'sine.inOut': (u) => -(Math.cos(Math.PI * u) - 1) / 2,
    'expo.in': (u) => (u <= 0 ? 0 : 2 ** (10 * (u - 1))), 'expo.out': (u) => (u >= 1 ? 1 : 1 - 2 ** (-10 * u)),
    'expo.inOut': (u) => (u < 0.5 ? 2 ** (20 * u - 10) / 2 : (2 - 2 ** (-20 * u + 10)) / 2),
    'circ.in': (u) => 1 - Math.sqrt(clamp(1 - u * u)), 'circ.out': (u) => Math.sqrt(clamp(1 - (u - 1) ** 2)),
    'back.out': (u) => 1 + 2.70158 * (u - 1) ** 3 + 1.70158 * (u - 1) ** 2, 'back.in': (u) => 2.70158 * u ** 3 - 1.70158 * u ** 2,
  });
  function back(dir, s, u) {
    if (dir === 'in') return (s + 1) * u ** 3 - s * u ** 2;
    if (dir === 'out') return 1 + (s + 1) * (u - 1) ** 3 + s * (u - 1) ** 2;
    const s2 = s * 1.525;
    return u < 0.5 ? ((2 * u) ** 2 * ((s2 + 1) * 2 * u - s2)) / 2 : ((2 * u - 2) ** 2 * ((s2 + 1) * (2 * u - 2) + s2) + 2) / 2;
  }
  function bezier(u, x1, y1, x2, y2) {   // CSS cubic-bezier: solve x(s) = u by bisection (30 steps, as runtime.py)
    let lo = 0, hi = 1;
    for (let i = 0; i < 30; i++) {
      const s = (lo + hi) / 2, x = 3 * (1 - s) ** 2 * s * x1 + 3 * (1 - s) * s ** 2 * x2 + s ** 3;
      if (x < u) lo = s; else hi = s;
    }
    const s = (lo + hi) / 2;
    return 3 * (1 - s) ** 2 * s * y1 + 3 * (1 - s) * s ** 2 * y2 + s ** 3;
  }
  function spring(tau, omega, zeta) {
    zeta = Math.min(zeta, 0.999); tau = Math.max(0, tau);
    const wd = omega * Math.sqrt(1 - zeta * zeta);
    return 1 - Math.exp(-zeta * omega * tau) * (Math.cos(wd * tau) + ((zeta * omega) / wd) * Math.sin(wd * tau));
  }
  function progress(e, u, elapsed) {
    u = clamp(u);
    switch (e.kind) {
      case 'named': return NAMED[e.name](u);
      case 'back': return back(e.dir, e.s, u);
      case 'bezier': return bezier(u, ...e.p);
      case 'hold': return u >= 1 ? 1 : 0;
      case 'spring': return spring(elapsed, e.omega, e.zeta);
      default: throw new Error(`score.js: unknown ease kind ${e.kind}`);
    }
  }

  // ---------- evaluation ----------
  function channel(segs, base, t) {
    let cur = null;
    for (const s of segs || []) { if (s.t0 <= t) cur = s; else break; }
    if (!cur) return base;
    const span = cur.t1 - cur.t0;
    const p = cur.ease.kind === 'spring' ? progress(cur.ease, 0, t - cur.t0) : span <= 0 ? 1 : progress(cur.ease, (t - cur.t0) / span);
    return cur.v0 + (cur.v1 - cur.v0) * p;
  }
  function shake(sh, t) {
    if (t < sh.t0) return [0, 0];
    const f = Math.floor(t * sh.rate + 1e-6), k = sh.amp * Math.exp(-sh.decay * (t - sh.t0));
    return [(hash(f * 1.7 + sh.seed) - 0.5) * 2 * k, (hash(f * 2.3 + 9 + sh.seed) - 0.5) * 2 * k];
  }

  let R = null, SHOTS = {};
  const need = (id) => { const s = SHOTS[id]; if (!s) throw new Error(`score.js: no shot ${id} in the score (have ${Object.keys(SHOTS).join(', ')})`); return s; };
  const Score = {
    load(resolved) { R = resolved; SHOTS = Object.fromEntries(resolved.shots.map((s) => [s.id, s])); return Score; },
    get data() { return R; },
    shot(id) { const s = need(id); return { start: s.start, end: s.end, dur: s.end - s.start, cadence: s.cadence, ref_shot: s.ref_shot }; },
    cam(id, t) {
      const c = need(id).camera, v = {};
      for (const ch of ['x', 'y', 'zoom', 'rot']) v[ch] = channel(c.channels[ch], c.base[ch], t);
      const d = c.drift;   // a slow change over the whole shot, layered under the moves (zoom multiplies)
      if (d) {
        const span = d.t1 - d.t0, p = progress(d.ease, span > 0 ? (t - d.t0) / span : 1, 0);
        for (const [ch, by] of Object.entries(d.by)) v[ch] = ch === 'zoom' ? v[ch] * by ** p : v[ch] + by * p;
      }
      for (const sh of c.shakes) { const [dx, dy] = shake(sh, t); v.x += dx; v.y += dy; }
      v.rotDeg = (v.rot * 180) / Math.PI;
      return v;
    },
    camLocal(id, lt) { return Score.cam(id, need(id).start + lt); },
    // SVG engines (HyperFrames): the same camera as canvas camBegin(x, y, zoom, rot), as a transform for the camera group.
    // Use it instead of a project Kit's own S.camera(), whose handling of roll differs between projects (some ignore it):
    //   S.cam.setAttribute('transform', Score.svgCamLocal('S3', t))
    svgCam(id, t) {
      const c = Score.cam(id, t), [w, h] = R.size || [1920, 1080];
      return `translate(${w / 2},${h / 2}) rotate(${c.rotDeg.toFixed(4)}) scale(${c.zoom.toFixed(5)}) translate(${(-c.x).toFixed(3)},${(-c.y).toFixed(3)})`;
    },
    svgCamLocal(id, lt) { return Score.svgCam(id, need(id).start + lt); },
    track(id, name, t) {
      const tr = need(id).tracks[name];
      if (!tr) throw new Error(`score.js: shot ${id} has no track "${name}"`);
      return channel(tr.segs, tr.base, t);
    },
    cue(name) { if (!(name in R.cues)) throw new Error(`score.js: no cue "${name}"`); return R.cues[name]; },
    beat(n) { return R.offset + (n * 60) / R.bpm; },
    held(id, t) {
      const s = need(id), n = s.cadence;
      if (n <= 1) return t;
      const f = Math.max(0, Math.floor((t - s.start) * R.fps + 1e-6));   // ≥ 0: JS and Python disagree on % of negatives
      return s.start + (f - (f % n)) / R.fps;
    },
  };
  if (typeof module !== 'undefined' && module.exports) module.exports = Score;
  else root.Score = Score;
})(typeof window !== 'undefined' ? window : globalThis);
