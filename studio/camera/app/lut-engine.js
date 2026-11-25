/* محرك الفلاتر (نسخة JavaScript من scripts/make-luts.py، نفس الرياضيات بالضبط).
 * يصنع ملف .cube لكاميرا Sony ZV-E10 II (من S-Log3/S-Gamut3.Cine إلى Rec.709) من إعدادات الستايل،
 * ويطبّق الستايل على صورة عادية للمعاينة. يشتغل بالمتصفح وبـ Node (للاختبار).
 * إذا تغيّرت الرياضيات بـ make-luts.py، غيّرها هنا هم. الاختبار: node studio/camera/app/test-engine.js
 */
(function (root) {
  "use strict";
  const EXPO = 5 / 3, WHITE_IN = 3.2, OUT_GAMMA = 2.2, SHADOW_SAT = 0.4;
  const BLACK_OUT = 0.03, WHITE_OUT = 0.94, LEGAL_LO = 64 / 1023, LEGAL_HI = 940 / 1023;
  const LUMA = [0.2126, 0.7152, 0.0722];
  const SG3C_TO_XYZ = [[0.5990839208, 0.2489255161, 0.1024464902], [0.2150758201, 0.8850685017, -0.1001443219],
    [-0.0320658495, -0.0276583907, 1.1487819910]];
  const XYZ_TO_709 = [[3.2404542, -1.5371385, -0.4985314], [-0.9692660, 1.8760108, 0.0415560],
    [0.0556434, -0.2040259, 1.0572252]];
  const OK_M1 = [[0.4122214708, 0.5363325363, 0.0514459929], [0.2119034982, 0.6806995451, 0.1073969566],
    [0.0883024619, 0.2817188376, 0.6299787005]];
  const OK_M2 = [[0.2104542553, 0.7936177850, -0.0040720468], [1.9779984951, -2.4285922050, 0.4505937099],
    [0.0259040371, 0.7827717662, -0.8086757660]];

  function mul(A, B) { return A.map((r) => [0, 1, 2].map((j) => r[0] * B[0][j] + r[1] * B[1][j] + r[2] * B[2][j])); }
  function inv(m) {
    const [a, b, c] = m[0], [d, e, f] = m[1], [g, h, i] = m[2];
    const A = e * i - f * h, B = -(d * i - f * g), C = d * h - e * g, det = a * A + b * B + c * C;
    return [[A / det, -(b * i - c * h) / det, (b * f - c * e) / det],
      [B / det, (a * i - c * g) / det, -(a * f - c * d) / det],
      [C / det, -(a * h - b * g) / det, (a * e - b * d) / det]];
  }
  const SG3C_TO_709 = mul(XYZ_TO_709, SG3C_TO_XYZ), R709_TO_SG3C = inv(SG3C_TO_709);
  const OK_M1I = inv(OK_M1), OK_M2I = inv(OK_M2);
  const mv = (M, v) => [M[0][0] * v[0] + M[0][1] * v[1] + M[0][2] * v[2],
    M[1][0] * v[0] + M[1][1] * v[1] + M[1][2] * v[2], M[2][0] * v[0] + M[2][1] * v[1] + M[2][2] * v[2]];
  const clip = (x, a, b) => (x < a ? a : x > b ? b : x);
  const dot = (v, w) => v[0] * w[0] + v[1] * w[1] + v[2] * w[2];

  function slog3ToLin(x) {
    const cut = 171.2102946929 / 1023;
    return x >= cut ? Math.pow(10, (x * 1023 - 420) / 261.5) * 0.19 - 0.01 : (x * 1023 - 95) * 0.01125 / (171.2102946929 - 95);
  }
  function linToSlog3(y) {
    return y >= 0.01125 ? (420 + Math.log10((Math.max(y, 0) + 0.01) / 0.19) * 261.5) / 1023
      : (y * (171.2102946929 - 95) / 0.01125 + 95) / 1023;
  }
  function toLab(rgb) { return mv(OK_M2, mv(OK_M1, rgb.map((x) => Math.max(x, 0))).map(Math.cbrt)); }
  function fromLab(lab) { return mv(OK_M1I, mv(OK_M2I, lab).map((x) => x * x * x)); }
  function ss(e0, e1, x) { const t = clip((x - e0) / (e1 - e0), 0, 1); return t * t * (3 - 2 * t); }
  function hdiff(h, c) { return ((((h - c + 180) % 360) + 360) % 360) - 180; }
  function hw(h, c, w) { return ss(w, 0, Math.abs(hdiff(h, c))); }

  function gamutCompress(rgb, thr = 0.8, lim = 1.25) {
    const ach = Math.max(rgb[0], rgb[1], rgb[2]);
    const safe = ach === 0 ? 1 : Math.abs(ach);
    const scale = (lim - thr) / Math.sqrt(Math.pow((1 - thr) / (lim - thr), -2) - 1);
    return rgb.map((v) => {
      const d = ach === 0 ? 0 : (ach - v) / safe;
      const over = (d - thr) / scale;
      const dc = d < thr ? d : thr + scale * over / Math.sqrt(1 + over * over);
      return ach - dc * safe;
    });
  }
  function toe(x, t) { x = Math.max(x, 0); return x * x / (x + t) * (0.18 + t) / 0.18; }
  function curveConsts(c, g) {
    const wc = Math.pow(WHITE_IN, c), gc = Math.pow(0.18, c);
    const k = wc * gc * (g - 1) / (gc - g * wc);
    return [k, (wc + k) / wc];
  }
  function tonemap(x, c, g, t) {
    const [k, s] = curveConsts(c, g);
    const xc = Math.pow(Math.min(toe(x, t), WHITE_IN), c);
    return s * xc / (xc + k);
  }
  function tonemapInv(y, c, g, t) {
    const [k, s] = curveConsts(c, g);
    const u = Math.pow(k * y / Math.max(s - y, 1e-6), 1 / c) * 0.18 / (0.18 + t);
    return (u + Math.sqrt(u * u + 4 * u * t)) / 2;
  }

  const BASE = { contrast: 1.6, gray: 0.17, toe: 0.004, wb: [1, 1], sat: 1, vib: 0, dens: 0.3, teal: 0,
    sh: [0, 0], hi: [0, 0], skin: 0.6, fade: 0, rgb_pop: 0.15 };
  const PRO_BASE = { skin_pull: 0, skin_c: [0.05, 0.09], skin_norm: 0, skin_lift: 0, red: [25, 0, 0, 0],
    amber: [68, 0, 0, 0], blue: [245, 0, 0, 0], blue_skin: 0, wall: 0, green: 0, spill: 0, accent: [0, 0] };

  function proColor(L, C, h, q) {
    q = Object.assign({}, PRO_BASE, q);
    const sk = hw(h, 52, 40) * ss(0.012, 0.03, C) * ss(0.15, 0.10, C) * ss(0.12, 0.3, L) * ss(0.97, 0.85, L);
    h = h - q.skin_pull * sk * hdiff(h, 55);
    const [lo, hi] = q.skin_c;
    C = C + q.skin_norm * sk * (clip(C, lo, hi) - C);
    L = L + q.skin_lift * sk * ss(0.2, 0.5, L) * ss(0.85, 0.6, L);
    const rest = 1 - sk;
    for (const [key, center, width, cmin] of [["red", 22, 26, 0.09], ["amber", 68, 24, 0.07], ["blue", 250, 50, 0.05]]) {
      const [target, shift, sat, dens] = q[key];
      const w = hw(h, center, width) * ss(cmin, cmin + 0.07, C) * rest;
      h = h - shift * w * hdiff(h, target);
      C = C * (1 + sat * w);
      L = L * (1 - dens * w);
    }
    const bs = hw(h, 250, 55) * ss(0.11, 0.04, C) * ss(0.18, 0.4, L);
    C = C * (1 - q.blue_skin * bs);
    const sp = ss(0.11, 0.04, C) * ss(0.15, 0.35, L) * (1 - sk);
    C = C * (1 - q.spill * sp);
    const ac = ss(0.1, 0.18, C) * (1 - sk);
    C = C * (1 + q.accent[0] * ac);
    L = L * (1 - q.accent[1] * ac);
    const wl = ss(0.055, 0.02, C) * ss(0.45, 0.7, L);
    C = C * (1 - q.wall * wl);
    const g = hw(h, 140, 40) * ss(0.01, 0.04, C);
    h = h - 0.25 * q.green * g * hdiff(h, 110);
    C = C * (1 - 0.3 * q.green * g);
    return [L, C, ((h % 360) + 360) % 360];
  }

  /** قيمة S-Log3 (ثلاث أرقام 0-1) -> قيمة الفلتر الجاهزة (بمستوى الناتج) */
  function applyLook(slog, p) {
    p = Object.assign({}, BASE, p);
    let lin = slog.map((x) => slog3ToLin(x) * Math.pow(2, -EXPO));
    lin = gamutCompress(mv(SG3C_TO_709, lin));
    lin = [lin[0] * p.wb[0], lin[1], lin[2] * p.wb[1]];
    const mono = p.mono;
    if (mono) { const m = Math.max(dot(lin, mono), 0); lin = [m, m, m]; }
    let Y = Math.max(dot(lin, LUMA), 0);
    const peak = Math.max(lin[0], lin[1], lin[2]);
    const w = ss(WHITE_IN * 0.2, WHITE_IN * 0.95, Math.max(Y, peak * 0.5));
    const tgt = Math.max(Y, peak * 0.6);
    lin = lin.map((x) => Math.max(x * (1 - w) + tgt * w, 0));

    const c = p.contrast, g = p.gray, t = p.toe;
    const per = lin.map((x) => tonemap(x, c, g, t));
    Y = Math.max(dot(lin, LUMA), 1e-9);
    const tY = tonemap(Y, c, g, t);
    const mix = 0.55 - 0.35 * p.rgb_pop;
    let disp = lin.map((x, i) => per[i] * mix + clip(x / Y, 0, 4) * tY * (1 - mix));
    const hl = ss(0.6, 1.6, Math.max(disp[0], disp[1], disp[2]));
    disp = disp.map((x, i) => clip(x * (1 - hl) + per[i] * hl, 0, 1));

    const lab = toLab(disp);
    let L = lab[0], C = Math.hypot(lab[1], lab[2]);
    let h = ((Math.atan2(lab[2], lab[1]) * 180 / Math.PI) % 360 + 360) % 360;
    if (p.pro) [L, C, h] = proColor(L, C, h, p.pro);
    if (!mono) {
      const skin = hw(h, 55, 30) * ss(0.015, 0.045, C) * ss(0.21, 0.13, C);
      const sel = ss(0.012, 0.05, C);
      const warm = hw(h, 60, 60) * sel, cool = hw(h, 225, 80) * sel;
      const green = hw(h, 140, 42) * sel * (1 - cool), mag = hw(h, 335, 40) * sel, blue = hw(h, 262, 50) * sel;
      const red = hw(h, 22, 32) * ss(0.08, 0.2, C);
      const tl = p.teal;
      h = h - tl * (0.45 * warm * hdiff(h, 58) + 0.55 * cool * hdiff(h, 212) + 14 * green);
      h = h + (p.green || 0) * green + (p.blue || 0) * blue;
      h = h - 0.3 * p.skin * skin * hdiff(h, 55);
      let gain = p.sat * (1 + 0.2 * tl * warm) * (1 + 0.15 * tl * cool) * (1 - 0.3 * tl * green);
      gain *= (1 - 0.25 * tl * mag) * (1 + (p.green_sat || 0) * green);
      gain *= (1 + (p.warm_sat || 0) * warm) * (1 + (p.blue_sat || 0) * blue);
      gain *= 1 + (p.red_sat || 0) * red;
      gain *= 1 + p.vib * ss(0.01, 0.05, C) * ss(0.2, 0.08, C);
      gain *= 1 + 0.35 * p.rgb_pop * ss(0.09, 0.2, C) * (1 - skin);
      gain = 1 + (gain - 1) * (1 - (gain > 1 ? 0.65 : 0.35) * p.skin * skin);
      gain *= SHADOW_SAT + (1 - SHADOW_SAT) * ss(0.07, 0.24, L);
      C *= gain;
      if (p.bleach) C *= 1 - 0.55 * p.bleach;
      L = L * (1 - 0.16 * p.dens * ss(0.04, 0.24, C) * (1 - 0.7 * skin));
    }
    if (p.bleach) L = L + 0.07 * p.bleach * Math.sin(2 * Math.PI * (L - 0.5));

    const ws = ss(0.02, 0.2, L) * ss(0.62, 0.22, L), wh = ss(0.5, 0.88, L);
    const hr = h * Math.PI / 180, shr = p.sh[0] * Math.PI / 180, hir = p.hi[0] * Math.PI / 180;
    const a = C * Math.cos(hr) + p.sh[1] * Math.cos(shr) * ws + p.hi[1] * Math.cos(hir) * wh;
    const b = C * Math.sin(hr) + p.sh[1] * Math.sin(shr) * ws + p.hi[1] * Math.sin(hir) * wh;
    L = clip(L, 0, 1);
    const at = (s) => fromLab([L, a * s, b * s]);
    let lo = 0, hi = 4;
    for (let i = 0; i < 14; i++) {
      const mid = (lo + hi) / 2, rgb = at(mid);
      if (Math.min(rgb[0], rgb[1], rgb[2]) >= 0 && Math.max(rgb[0], rgb[1], rgb[2]) <= 1) lo = mid; else hi = mid;
    }
    const x = 1 / Math.max(lo, 1e-3), knee = 0.6;
    const soft = knee + (1 - knee) * Math.tanh((x - knee) / (1 - knee));
    let v = at(x > knee ? soft / x : 1).map((q) => Math.pow(clip(q, 0, 1), 1 / OUT_GAMMA));
    if (p.film) v = v.map((q) => q - 0.05 * ss(0.7, 1, q));
    v = v.map((q) => p.fade + q * (1 - p.fade));
    return v.map((q) => BLACK_OUT + (WHITE_OUT - BLACK_OUT) * clip(q, 0, 1));
  }

  /** جدول الفلتر: Float32Array بترتيب cube (الأحمر يتغير أسرع)، n نقطة لكل لون */
  function buildTable(p, n = 33, smooth = true) {
    const T = new Float32Array(n * n * n * 3);
    for (let bi = 0; bi < n; bi++) for (let gi = 0; gi < n; gi++) for (let ri = 0; ri < n; ri++) {
      const o = applyLook([ri / (n - 1), gi / (n - 1), bi / (n - 1)], p);
      const k = ((bi * n + gi) * n + ri) * 3;
      T[k] = o[0]; T[k + 1] = o[1]; T[k + 2] = o[2];
    }
    return smooth ? smoothJumps(T, n) : T;
  }

  /** ينعّم بس القفزات الكبيرة (أضواء نيون قوية)، مثل smooth_jumps بالبايثون */
  function smoothJumps(T, n, limit = 0.15, passes = 3) {
    const N3 = n * n * n, idx = (b, g, r) => (b * n + g) * n + r;
    const chroma = new Float32Array(N3);
    for (let b = 0; b < n; b++) for (let g = 0; g < n; g++) for (let r = 0; r < n; r++) {
      const vs = [r, g, b].map((q) => q / (n - 1));
      chroma[idx(b, g, r)] = ss(0.06, 0.16, Math.max(...vs) - Math.min(...vs));
    }
    for (let pass = 0; pass < passes; pass++) {
      const blur = new Float32Array(N3 * 3), jump = new Float32Array(N3);
      const cl = (q) => (q < 0 ? 0 : q > n - 1 ? n - 1 : q);
      for (let b = 0; b < n; b++) for (let g = 0; g < n; g++) for (let r = 0; r < n; r++) {
        const o = idx(b, g, r) * 3;
        for (let db = -1; db <= 1; db++) for (let dg = -1; dg <= 1; dg++) for (let dr = -1; dr <= 1; dr++) {
          const s = idx(cl(b + db), cl(g + dg), cl(r + dr)) * 3;
          blur[o] += T[s]; blur[o + 1] += T[s + 1]; blur[o + 2] += T[s + 2];
        }
        blur[o] /= 27; blur[o + 1] /= 27; blur[o + 2] /= 27;
      }
      const step = [n * n, n, 1];
      for (let ax = 0; ax < 3; ax++) {
        for (let b = 0; b < n; b++) for (let g = 0; g < n; g++) for (let r = 0; r < n; r++) {
          const pos = [b, g, r];
          if (pos[ax] === n - 1) continue;
          const i0 = idx(b, g, r), i1 = i0 + step[ax];
          const d = Math.max(Math.abs(T[i1 * 3] - T[i0 * 3]), Math.abs(T[i1 * 3 + 1] - T[i0 * 3 + 1]),
            Math.abs(T[i1 * 3 + 2] - T[i0 * 3 + 2]));
          if (d > jump[i0]) jump[i0] = d;
          if (d > jump[i1]) jump[i1] = d;
        }
      }
      for (let i = 0; i < N3; i++) {
        const w = ss(limit * 0.6, limit * 1.5, jump[i]) * chroma[i];
        for (let c = 0; c < 3; c++) T[i * 3 + c] = T[i * 3 + c] * (1 - w) + blur[i * 3 + c] * w;
      }
    }
    for (let i = 0; i < T.length; i++) T[i] = clip(T[i], 0, 1);
    return T;
  }

  /** نص ملف .cube (نفس صيغة make-luts.py: بلا أسطر تعليق) + فحص السلامة */
  function cubeText(T, n, title) {
    const gray = [];
    for (let i = 0; i < n; i++) { const k = ((i * n + i) * n + i) * 3; gray.push(dot([T[k], T[k + 1], T[k + 2]], LUMA)); }
    for (let i = 1; i < n; i++) if (gray[i] - gray[i - 1] < -1e-4) throw new Error("التدرج من الأسود للأبيض مو متصاعد");
    if (!(gray[3] < BLACK_OUT + 0.08 && gray[n - 1] > WHITE_OUT - 0.05)) throw new Error("الأسود أو الأبيض بمكان غلط");
    const lines = [`TITLE "${title.replace(/[^\x20-\x7e]/g, "").replace(/"/g, "")}"`, `LUT_3D_SIZE ${n}`,
      "DOMAIN_MIN 0.0 0.0 0.0", "DOMAIN_MAX 1.0 1.0 1.0"];
    for (let i = 0; i < T.length; i += 3) lines.push(`${T[i].toFixed(5)} ${T[i + 1].toFixed(5)} ${T[i + 2].toFixed(5)}`);
    return lines.join("\n") + "\n";
  }

  /** تطبيق جدول على قيمة (تقريب ثلاثي خطي) */
  function sample(T, n, r, g, b) {
    const f = (x) => clip(x, 0, 1) * (n - 1);
    const xr = f(r), xg = f(g), xb = f(b);
    const r0 = Math.min(Math.floor(xr), n - 2), g0 = Math.min(Math.floor(xg), n - 2), b0 = Math.min(Math.floor(xb), n - 2);
    const fr = xr - r0, fg = xg - g0, fb = xb - b0, out = [0, 0, 0];
    for (let db = 0; db < 2; db++) for (let dg = 0; dg < 2; dg++) for (let dr = 0; dr < 2; dr++) {
      const w = (dr ? fr : 1 - fr) * (dg ? fg : 1 - fg) * (db ? fb : 1 - fb);
      const k = (((b0 + db) * n + (g0 + dg)) * n + (r0 + dr)) * 3;
      out[0] += w * T[k]; out[1] += w * T[k + 1]; out[2] += w * T[k + 2];
    }
    return out;
  }

  /** صورة عادية (sRGB 0-255) -> شكلها لو انصورت خام S-Log3 بإضاءة أفتح بـ EXPO (للمعاينة) */
  const CLEAN = { contrast: 1.5, gray: 0.175, toe: 0.004 };
  function photoToSlog(r8, g8, b8) {
    const d = [r8, g8, b8].map((v) => { v /= 255; return v <= 0.04045 ? v / 12.92 : Math.pow((v + 0.055) / 1.055, 2.4); });
    const Y = Math.max(dot(d, LUMA), 1e-6);
    const Ys = tonemapInv(Math.min(Y, 0.999), CLEAN.contrast, CLEAN.gray, CLEAN.toe);
    const scene = d.map((x) => Math.max(Ys + (x / Y * Ys - Ys) / 1.12, 0) * Math.pow(2, EXPO));
    return mv(R709_TO_SG3C, scene).map((x) => linToSlog3(Math.max(x, -0.01)));
  }
  const onScreen = (v) => clip((v - LEGAL_LO) / (LEGAL_HI - LEGAL_LO), 0, 1);

  /** إحصاء ألوان صورة مرجعية (للذكاء الاصطناعي): سطوع وتشبع ولون الظلال والوسط والإضاءات */
  function imageStats(data) {
    const zones = { shadows: [0, 0, 0, 0, 0], mids: [0, 0, 0, 0, 0], highs: [0, 0, 0, 0, 0] };
    const Ls = [];
    for (let i = 0; i < data.length; i += 16) {
      const lin = [data[i], data[i + 1], data[i + 2]].map((v) => { v /= 255; return v <= 0.04045 ? v / 12.92 : Math.pow((v + 0.055) / 1.055, 2.4); });
      const [L, a, b] = toLab(lin);
      Ls.push(L);
      const z = L < 0.35 ? zones.shadows : L < 0.7 ? zones.mids : zones.highs;
      z[0]++; z[1] += a; z[2] += b; z[3] += Math.hypot(a, b); z[4] += L;
    }
    Ls.sort((x, y) => x - y);
    const q = (p) => +Ls[Math.floor(p * (Ls.length - 1))].toFixed(3);
    const zone = (z) => z[0] ? { share: +(z[0] / Ls.length).toFixed(2), tint_hue_deg: Math.round(((Math.atan2(z[2], z[1]) * 180 / Math.PI) + 360) % 360),
      tint_strength: +(Math.hypot(z[1], z[2]) / z[0]).toFixed(3), avg_chroma: +(z[3] / z[0]).toFixed(3) } : null;
    return { oklab_lightness_percentiles: { p5: q(0.05), p25: q(0.25), p50: q(0.5), p75: q(0.75), p95: q(0.95) },
      shadows: zone(zones.shadows), mids: zone(zones.mids), highlights: zone(zones.highs) };
  }

  root.LutEngine = { applyLook, buildTable, cubeText, sample, photoToSlog, onScreen, imageStats, BASE, PRO_BASE };
})(typeof window !== "undefined" ? window : globalThis);
