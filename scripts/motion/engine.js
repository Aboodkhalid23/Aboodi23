// محرك موشن گرافيك أوّاب (الإصدار 2): رسم توضيحي فاخر بالكود على canvas
// الصفحة تستدعي window.R(t) لكل إطار. البيانات بـ window.D: {lang,segs,times,total,beats,hl,title,label,src,quran}
// قاعدة شرعية: ما نرسم نبي ولا صحابي ولا ملَك. الشخصيات بس "مسلم عادي" يطبق معنى الحديث، والنساء بحجاب وبدون ملامح
// البنية: خلفيات بطبقات (تنرسم مرة وحدة وتنحفظ) + كاميرا لكل لقطة بعمق (parallax) + انتقالات بقناع + نص حركي + لمسات أخيرة (تظليل، حبيبات)
(function () {
const W = 720, H = 1280, GY = 1120, M = 70, TAU = Math.PI * 2;
const cv = document.getElementById('c');
let x = cv.getContext('2d');
const D = window.D, AR = D.lang === 'ar';
// ===== منحنيات الحركة =====
const clamp = (v, a = 0, b = 1) => v < a ? a : v > b ? b : v;
const eOut = p => { p = clamp(p); return 1 - Math.pow(1 - p, 4); };
const eIn = p => { p = clamp(p); return p * p * p; };
const eIO = p => { p = clamp(p); return p < .5 ? 4 * p * p * p : 1 - Math.pow(-2 * p + 2, 3) / 2; };
const sine = p => { p = clamp(p); return .5 - .5 * Math.cos(Math.PI * p); };
const spr = p => p <= 0 ? 0 : p >= 1 ? 1 : 1 - Math.exp(-6 * p) * Math.cos(8 * p) * (1 - p);
const ease = eIO;
const back = p => { p = clamp(p); const c = 1.7; return 1 + (c + 1) * Math.pow(p - 1, 3) + c * Math.pow(p - 1, 2); };
const lerp = (a, b, p) => a + (b - a) * p;
const rnd = s => { const v = Math.sin(s * 127.1 + 3.7) * 43758.5453; return v - Math.floor(v); };
const strip = s => s.replace(/[ؐ-ًؚ-ٰٟۖ-ۭـ]/g, '');
const R = a => a * Math.PI / 180;
const icon = new Image(); icon.src = D.icon || 'icon-192.png';
const hex = h => { h = h.replace('#', ''); if (h.length === 3) h = h.split('').map(c => c + c).join(''); return [parseInt(h.slice(0, 2), 16), parseInt(h.slice(2, 4), 16), parseInt(h.slice(4, 6), 16)]; };
const mix = (a, b, k) => { const A = hex(a), B = hex(b); return `rgb(${A.map((v, i) => Math.round(lerp(v, B[i], k))).join(',')})`; };
const rgba = (h, a) => { const c = hex(h); return `rgba(${c[0]},${c[1]},${c[2]},${a})`; };

// ===== الألوان والسلاسل =====
const C = { gold: '#e9bd5f', gold2: '#c9962e', ink: '#f3ecd8', navy: '#0b1026', teal: '#1f4d44', green: '#2f6b57', cream: '#f4ead8', sand: '#e6d3b3', brown: '#7a5a3c', rose: '#b98b8b' };
const SER_OF = { 'من الأربعين النووية': 'nawawi', "An-Nawawi's Forty Hadith": 'nawawi', 'قصص الأنبياء من القرآن': 'prophets', 'Stories of the Prophets': 'prophets', 'يوم القيامة والجنة والنار': 'akhira', 'The Last Day, Paradise & Hell': 'akhira', 'التسامح والأخلاق': 'akhlaq', 'Forgiveness & Character': 'akhlaq', 'ذكر الله والرحمة': 'dhikr', 'Remembrance & Mercy': 'dhikr', 'قصص من السنة': 'stories', 'Stories from the Sunnah': 'stories' };
// لكل سلسلة: لون التمييز على الغامق والفاتح، لون التدرج النهائي، خلفية المقدمة، وأنواع الانتقالات
const SERIES = {
  nawawi: { acc: '#f2c45f', accL: '#a2412c', tint: '#ffb860', ta: .06, deep: ['#0c2a25', '#04110f'], tr: ['arch', 'iris', 'slide', 'arch'] },
  prophets: { acc: '#f3c76a', accL: '#1d5d78', tint: '#4fa8c8', ta: .07, deep: ['#0b2238', '#030a14'], tr: ['arch', 'slide', 'iris', 'flash'] },
  akhira: { acc: '#f0c46a', accL: '#7a2d52', tint: '#7a6ad0', ta: .08, deep: ['#16122e', '#05040f'], tr: ['flash', 'iris', 'arch'] },
  akhlaq: { acc: '#f4c56c', accL: '#a2412c', tint: '#ff9a7a', ta: .06, deep: ['#2a1420', '#0c0509'], tr: ['iris', 'arch', 'slide'] },
  dhikr: { acc: '#f1cd72', accL: '#2a6b4c', tint: '#9fe0a0', ta: .05, deep: ['#0d2a1c', '#03100a'], tr: ['arch', 'flash', 'iris'] },
  stories: { acc: '#f2c25e', accL: '#a2412c', tint: '#ffb070', ta: .06, deep: ['#2a1a0e', '#0d0804'], tr: ['slide', 'arch', 'iris'] },
};
const SK = D.ser || SER_OF[D.label] || 'nawawi', SE = SERIES[SK] || SERIES.nawawi;

// ===== أدوات رسم عامة =====
function circ(cx, cy, r, f) { x.beginPath(); x.arc(cx, cy, r, 0, TAU); x.fillStyle = f; x.fill(); }
function ell(cx, cy, rx, ry, f, rot = 0) { x.beginPath(); x.ellipse(cx, cy, rx, ry, rot, 0, TAU); x.fillStyle = f; x.fill(); }
function rr(px, py, w, h, r, f) { x.beginPath(); x.roundRect(px, py, w, h, r); x.fillStyle = f; x.fill(); }
function blob(pts, fill) { x.beginPath(); pts.forEach((p, i) => i ? x.lineTo(p[0], p[1]) : x.moveTo(p[0], p[1])); x.closePath(); x.fillStyle = fill; x.fill(); }
function smooth(pts, fill, close = true) { // منحنى ناعم يمر بين النقاط
  x.beginPath(); const n = pts.length; x.moveTo((pts[0][0] + pts[n - 1][0]) / 2, (pts[0][1] + pts[n - 1][1]) / 2);
  for (let i = 0; i < n; i++) { const a = pts[i], b = pts[(i + 1) % n]; x.quadraticCurveTo(a[0], a[1], (a[0] + b[0]) / 2, (a[1] + b[1]) / 2); }
  x.closePath(); if (fill) { x.fillStyle = fill; x.fill(); }
}
function grad(a, b, y0 = 0, y1 = H) { const g = x.createLinearGradient(0, y0, 0, y1); g.addColorStop(0, a); g.addColorStop(1, b); return g; }
function vgrad(stops, y0 = 0, y1 = H) { const g = x.createLinearGradient(0, y0, 0, y1); stops.forEach(([o, c]) => g.addColorStop(o, c)); return g; }
function hgrad(stops, x0, x1) { const g = x.createLinearGradient(x0, 0, x1, 0); stops.forEach(([o, c]) => g.addColorStop(o, c)); return g; }
function glow(cx, cy, r, col, a = 1) { const g = x.createRadialGradient(cx, cy, 0, cx, cy, r); g.addColorStop(0, rgba(col, a)); g.addColorStop(.4, rgba(col, a * .35)); g.addColorStop(1, rgba(col, 0)); x.fillStyle = g; x.fillRect(cx - r, cy - r, 2 * r, 2 * r); }
function star8(px, py, r, f) { x.save(); x.translate(px, py); for (let k = 0; k < 2; k++) { x.rotate(R(45 * k)); x.fillStyle = f; x.fillRect(-r * .7, -r * .7, r * 1.4, r * 1.4); } x.restore(); }
function twinkle(px, py, r, col, a = 1) { // نجمة رباعية لامعة
  x.save(); x.globalAlpha *= a; x.translate(px, py); x.fillStyle = col; x.beginPath();
  for (let i = 0; i < 4; i++) { const an = i * Math.PI / 2; x.lineTo(Math.cos(an) * r, Math.sin(an) * r); x.lineTo(Math.cos(an + Math.PI / 4) * r * .22, Math.sin(an + Math.PI / 4) * r * .22); }
  x.closePath(); x.fill(); x.globalAlpha *= .5; circ(0, 0, r * .45, col); x.restore();
}
function heartShape(px, py, s, f) { x.save(); x.translate(px, py); x.scale(s, s); x.beginPath(); x.moveTo(0, 12); x.bezierCurveTo(-26, -6, -14, -30, 0, -16); x.bezierCurveTo(14, -30, 26, -6, 0, 12); x.fillStyle = f; x.fill(); x.restore(); }
function archPath(p, cx, by, w, h) { // قوس إسلامي مدبّب
  p.moveTo(cx - w / 2, by); p.lineTo(cx - w / 2, by - h + w * .45);
  p.bezierCurveTo(cx - w / 2, by - h + w * .05, cx - w * .12, by - h - w * .05, cx, by - h - w * .2);
  p.bezierCurveTo(cx + w * .12, by - h - w * .05, cx + w / 2, by - h + w * .05, cx + w / 2, by - h + w * .45);
  p.lineTo(cx + w / 2, by); p.closePath(); return p;
}
function arch(px, py, w, h, f) { x.beginPath(); archPath(x, px, py, w, h); x.fillStyle = f; x.fill(); }
function starPoly(p, cx, cy, r, n, k, rot = 0) { for (let i = 0; i <= n; i++) { const a = rot + (i * k % n) * TAU / n - Math.PI / 2; i ? p.lineTo(cx + Math.cos(a) * r, cy + Math.sin(a) * r) : p.moveTo(cx + Math.cos(a) * r, cy + Math.sin(a) * r); } return p; }
// ===== تخزين الطبقات الثابتة (نرسمها مرة وحدة) =====
const CACHE = {};
function bake(key, fn, w = W + 2 * M, h = H, ox = M, oy = 0) {
  if (CACHE[key]) return CACHE[key];
  const c = document.createElement('canvas'); c.width = w; c.height = h; const o = x; x = c.getContext('2d'); x.translate(ox, oy); fn(); x = o; return CACHE[key] = c;
}
// ===== الكاميرا =====
let CAM = { x: 0, y: 0, z: 0 }, SKYP = false;
function applyCam(d) { const z = 1 + CAM.z * d; x.translate(360 + CAM.x * d, 900 + CAM.y * d); x.scale(z, z); x.translate(-360, -900); }
function L(d, key, fn) { const c = bake(key, fn); x.save(); applyCam(d); x.drawImage(c, -M, 0); x.restore(); }
function A(d, fn) { x.save(); applyCam(d); fn(); x.restore(); }

// ===== الشخصيات =====
const PEOPLE = {
  man: { th: '#f4f1ea', sh: '#cfc8b8', sk: '#e2aa7c', bd: '#3b2a20', cap: 'kufi', capc: '#ffffff' },
  man2: { th: '#2f6b57', sh: '#21503f', sk: '#c98e5e', bd: '#2a1d15', cap: 'ghutra', capc: '#f7f5f0', agal: 1 },
  poor: { th: '#8a7b66', sh: '#675a48', sk: '#c48f63', bd: '#7d7a76', cap: 'kufi', capc: '#a89a84', patch: '#6a5c4a' },
  elder: { th: '#ebe5d6', sh: '#c9bfab', sk: '#d9a479', bd: '#f3f1ec', cap: 'ghutra', capc: '#ffffff', cane: 1 },
  child: { th: '#f6f3ec', sh: '#d3cbbb', sk: '#ebb88b', bd: null, cap: 'kufi', capc: '#ffffff', s: .64, kid: 1 },
  boy2: { th: '#3d6e8f', sh: '#2c5470', sk: '#dca577', bd: null, cap: 'kufi', capc: '#ffffff', s: .64, kid: 1 },
  woman: { th: '#8f6a80', sh: '#6c4d60', sk: '#e3b08a', hij: '#5a4155', w: 1 },
  woman2: { th: '#b09968', sh: '#8a744a', sk: '#d9a27a', hij: '#6b583a', w: 1 },
};
// الوقفات: زاوية الجذع، ذراع بعيدة [كتف، كوع]، ذراع قريبة، وضع الرجلين (0 واگف، 1 گاعد، 2 ساجد/جالس على ركبه)
const POSE = {
  stand: { tor: 0, la: [6, 8], ra: [-6, 8], legs: 0 },
  give: { tor: 6, la: [6, 8], ra: [72, 8], legs: 0, palm: 1 },
  receive: { tor: 4, la: [40, 30], ra: [55, 30], legs: 0, palm: 1 },
  raise: { tor: 0, la: [6, 8], ra: [150, -25], legs: 0, finger: 1 },
  point: { tor: 3, la: [6, 8], ra: [95, 0], legs: 0, finger: 2 },
  dua: { tor: 0, la: [30, 115], ra: [42, 112], legs: 0, palm: 2 },
  duasit: { tor: 0, la: [30, 115], ra: [42, 112], legs: 2, palm: 2 },
  pray: { tor: 0, la: [22, 118], ra: [28, 112], legs: 0 },
  ruku: { tor: 86, la: [-70, 0], ra: [-62, 0], legs: 0 },
  sujud: { tor: 108, la: [-40, 34], ra: [-32, 34], legs: 2, low: 1, head: -8 },
  sit: { tor: 0, la: [22, 50], ra: [30, 50], legs: 1 },
  kneel: { tor: 0, la: [18, 40], ra: [24, 40], legs: 2 },
  read: { tor: 4, la: [34, 82], ra: [40, 80], legs: 1, book: 1 },
  readst: { tor: 4, la: [34, 82], ra: [40, 80], legs: 0, book: 1 },
  sitbeg: { tor: 6, la: [10, 20], ra: [62, 30], legs: 1, palm: 1 },
  wash: { tor: 18, la: [50, 35], ra: [58, 35], legs: 0 },
  washsit: { tor: 14, la: [50, 35], ra: [58, 35], legs: 1 },
  heart: { tor: 0, la: [6, 8], ra: [25, 125], legs: 0 },
  silent: { tor: 0, la: [6, 8], ra: [28, 150], legs: 0, finger: 1 },
  think: { tor: 0, la: [16, 100], ra: [22, 145], legs: 0 },
  carry: { tor: 0, la: [160, 10], ra: [165, 10], legs: 0, box: 1 },
  lift: { tor: 35, la: [70, 10], ra: [76, 10], legs: 0 },
  open: { tor: 0, la: [40, 20], ra: [48, 20], legs: 0, palm: 1 },
  sad: { tor: 10, la: [4, 6], ra: [-4, 6], legs: 0, head: 18 },
  hug: { tor: 8, la: [70, 60], ra: [78, 60], legs: 0 },
  walk: { tor: 4, la: [0, 10], ra: [0, 10], legs: 0, walk: 1 },
  cane: { tor: 8, la: [6, 8], ra: [40, 20], legs: 0 },
  angry: { tor: 4, la: [20, 70], ra: [26, 70], legs: 0, fist: 1 },
  calm: { tor: 0, la: [10, 20], ra: [-6, 8], legs: 0 },
};
// تعابير الوجه حسب الوقفة: 1 مبتسم، 2 حزين، 3 زعلان، 4 عيون مغمضة (خشوع)
const MOOD = { give: 1, receive: 1, heart: 1, hug: 1, open: 1, raise: 1, point: 1, calm: 1, sad: 2, sitbeg: 2, angry: 3, dua: 4, duasit: 4, pray: 4, ruku: 4, sujud: 4, read: 5, readst: 5, think: 6 };
function rot(px, py, a) { const c = Math.cos(a), s = Math.sin(a); return [px * c - py * s, px * s + py * c]; }
function limb(ax, ay, a1, a2, L1, L2, w, col, tor, cuff) {
  // الزوايا من الأسفل، والموجب لگدّام
  const t1 = R(a1) + tor, t2 = t1 + R(a2);
  const ex = ax + Math.sin(t1) * L1, ey = ay + Math.cos(t1) * L1;
  const hx = ex + Math.sin(t2) * L2, hy = ey + Math.cos(t2) * L2;
  x.lineCap = 'round'; x.lineJoin = 'round'; x.strokeStyle = col;
  x.lineWidth = w; x.beginPath(); x.moveTo(ax, ay); x.lineTo(ex, ey); x.stroke();
  x.lineWidth = w * .86; x.beginPath(); x.moveTo(ex, ey); x.lineTo(hx - Math.sin(t2) * 4, hy - Math.cos(t2) * 4); x.stroke();
  if (cuff) { x.strokeStyle = cuff; x.lineWidth = w * .9; x.lineCap = 'butt'; x.beginPath(); x.moveTo(hx - Math.sin(t2) * 9, hy - Math.cos(t2) * 9); x.lineTo(hx - Math.sin(t2) * 5, hy - Math.cos(t2) * 5); x.stroke(); x.lineCap = 'round'; }
  return [hx, hy, t2];
}
function hand(h, sk, kind, dark) {
  x.save(); x.translate(h[0], h[1]); x.rotate(-h[2]);
  const shade = mix(sk, '#5a3020', .25);
  if (kind === 'fist') { circ(0, 4, 10.5, sk); ell(-3, 2, 4, 6, shade); }
  else if (kind === 'palm') { ell(0, 7, 12, 10, sk); ell(-10, 2, 4.5, 7, sk, -.5); x.fillStyle = shade; x.globalAlpha *= .5; ell(2, 6, 6, 4, shade); }
  else { ell(0, 7, 9.5, 12, sk); ell(8, 1, 4, 7, sk, .5); if (dark) { x.globalAlpha *= .35; ell(-3, 8, 5, 8, shade); } }
  if (kind === 'finger') { x.strokeStyle = sk; x.lineWidth = 6.5; x.lineCap = 'round'; x.beginPath(); x.moveTo(0, 12); x.lineTo(0, 27); x.stroke(); }
  x.restore();
}
function person(a, t) {
  const P = PEOPLE[a.type] || PEOPLE.man, p = a.pose, s = (a.s || 1) * (P.s || 1) * 1.22;
  const sd = a.seed, mood = MOOD[p.name] || 0;
  x.save(); x.translate(a.x, a.y);
  // ظل ناعم على الأرض
  x.save(); x.globalAlpha = .22 * a.al; x.scale(1, .2); const sr = (p.l1 > .5 || p.l2 > .5 ? 82 : 60) * s; const sg = x.createRadialGradient(0, 0, 0, 0, 0, sr); sg.addColorStop(0, 'rgba(20,12,8,1)'); sg.addColorStop(1, 'rgba(20,12,8,0)'); x.fillStyle = sg; x.fillRect(-sr, -sr, sr * 2, sr * 2); x.restore();
  x.scale(s * a.dir, s); x.globalAlpha = a.al;
  const br = Math.sin(t * 2.1 + sd), walk = p.walk ? Math.sin(a.wph) : 0, wc = p.walk ? Math.cos(a.wph) : 0;
  const bob = p.walk ? -Math.abs(wc) * 5 : br * .6;
  const sway = Math.sin(t * 1.5 + sd) * 1.6 + walk * 5;
  let hipY = lerp(lerp(-100, -50, p.l1), -62, p.l2) - (p.low || 0) * 22 + bob, hipX = lerp(0, -18, p.l2) - (p.low || 0) * 10;
  const kid = P.kid ? 1 : 0;
  const thG = hgrad([[0, P.sh], [.42, P.th], [1, mix(P.th, '#ffffff', .25)]], -46, 46);
  // الجزء الأسفل
  if (p.l1 < .5 && p.l2 < .5) {
    const f1 = walk * 17, f2 = -walk * 17, l1 = Math.max(0, wc) * 7, l2 = Math.max(0, -wc) * 7;
    ell(-14 + f2, -5 - l2, 17, 7, '#2e241d'); ell(14 + f1, -5 - l1, 17, 7, '#3f3227');
    x.beginPath(); x.moveTo(-28, hipY); x.quadraticCurveTo(-34, hipY * .5, -42 + sway, -6); x.quadraticCurveTo(0, -1 + Math.sin(t * 2 + sd) * 1.5, 42 + sway, -7); x.quadraticCurveTo(34, hipY * .5, 30, hipY); x.closePath(); x.fillStyle = P.w ? P.th : thG; x.fill();
    x.strokeStyle = rgba('#000000', .08); x.lineWidth = 2.5; x.beginPath(); x.moveTo(-6, hipY + 10); x.quadraticCurveTo(-10 + sway * .4, -40, -14 + sway, -10); x.moveTo(14, hipY + 16); x.quadraticCurveTo(16 + sway * .4, -40, 20 + sway, -10); x.stroke();
    if (P.patch) rr(8, -58, 18, 16, 4, P.patch);
  } else if (p.l1 >= p.l2) {
    smooth([[-64, -2], [-60, -40], [-20, -56], [30, -50], [76, -30], [78, -4]], P.th);
    x.globalAlpha *= .9; smooth([[-64, -2], [-60, -40], [-24, -52], [-10, -2]], P.sh); x.globalAlpha = a.al;
    ell(66, -8, 16, 7, '#3f3227');
  } else {
    const hy = hipY, hx2 = hipX;
    smooth([[-58, -4], [-52, hy + 12], [hx2 + 6, hy - 8], [hx2 + 42, hy + 4], [56, -18], [52, -2]], P.th);
    x.globalAlpha *= .9; smooth([[-58, -4], [-52, hy + 12], [hx2 - 4, hy - 2], [-26, -4]], P.sh); x.globalAlpha = a.al; ell(-64, -6, 14, 6, '#3f3227');
  }
  if (P.cane) { x.strokeStyle = '#6b4a2b'; x.lineWidth = 7; x.lineCap = 'round'; x.beginPath(); x.moveTo(80, -2); x.lineTo(72, -122); x.quadraticCurveTo(68, -142, 52, -138); x.stroke(); }
  // الجذع
  const tor = R(p.tor) + br * .006;
  const hip = [hipX, hipY];
  const at = (dx, dy) => { const r = rot(dx, dy, tor); return [hip[0] + r[0], hip[1] + r[1]]; };
  const S1 = at(-8, -94 + br * .8), S2 = at(12, -94 + br * .8);
  const sk = P.sk, L1 = 44, L2 = 40, swing = p.walk ? R(walk * 22) : 0;
  const hk = k => p.fist > .5 ? 'fist' : p.palm > .5 ? 'palm' : k;
  // ذراع بعيدة
  const h1 = limb(S1[0], S1[1], p.la[0], p.la[1], L1, L2, 22, mix(P.sh, '#000000', .08), tor - swing, null);
  hand(h1, mix(sk, '#000000', .1), hk(''), 1);
  // جسم
  x.save(); x.translate(hip[0], hip[1]); x.rotate(tor);
  x.beginPath(); x.moveTo(-30, 14); x.lineTo(-29, -78); x.quadraticCurveTo(-28, -100 + br * .8, -8, -102 + br * .8); x.lineTo(16, -102 + br * .8); x.quadraticCurveTo(32, -100, 32, -78); x.lineTo(33, 14); x.closePath();
  x.fillStyle = P.w ? P.th : thG; x.fill();
  if (P.w) { x.globalAlpha *= .85; blob([[-30, 14], [-29, -78], [-24, -96], [-12, -100], [-10, 14]], P.sh); x.globalAlpha = a.al; }
  else { x.strokeStyle = rgba('#000000', .12); x.lineWidth = 2.5; x.beginPath(); x.moveTo(14, -96); x.lineTo(14, -58); x.stroke(); circ(14, -86, 2, rgba('#000000', .15)); circ(14, -74, 2, rgba('#000000', .15)); }
  // الرأس
  const hs = kid ? 1.16 : 1;
  const nod = Math.sin(t * .9 + sd * 1.3) * .035 + (p.walk ? Math.sin(a.wph * 2) * .015 : 0);
  x.translate(4, -128 + br * .9); x.rotate(R(p.head || 0) + nod); x.scale(hs, hs);
  if (P.w) {
    ell(-2, 24, 40, 34, P.hij); circ(0, -2, 33, P.hij);
    x.beginPath(); x.ellipse(10, 0, 20, 24, .1, 0, TAU); x.fillStyle = sk; x.fill();
    x.strokeStyle = rgba('#000000', .14); x.lineWidth = 3; x.beginPath(); x.arc(4, 2, 30, -1.2, 1.4); x.stroke();
    x.globalAlpha *= .5; ell(-14, 30, 10, 22, mix(P.hij, '#000000', .2)); x.globalAlpha = a.al;
  } else {
    rr(-8, 16, 20, 18, 6, mix(sk, '#000000', .12));
    const fg = x.createRadialGradient(10, -10, 4, 0, 0, 34); fg.addColorStop(0, mix(sk, '#ffffff', .12)); fg.addColorStop(1, mix(sk, '#7a3a20', .12)); circ(0, 0, 30, fg);
    ell(-20, 4, 6.5, 8, mix(sk, '#7a3a20', .15));
    ell(29, 3, 4.5, 4, mix(sk, '#7a3a20', .12));
    if (P.bd) { x.beginPath(); x.moveTo(-24, 0); x.quadraticCurveTo(-24, 40, 8, 40); x.quadraticCurveTo(30, 38, 30, 8); x.quadraticCurveTo(24, 16, 16, 14); x.quadraticCurveTo(4, 18, -6, 10); x.quadraticCurveTo(-14, 8, -18, 0); x.closePath(); x.fillStyle = P.bd; x.fill(); }
    // العين والحاجب والفم
    const bl = ((t + rnd(sd) * 4) % 4.2) < .13 ? .1 : 1, closed = mood === 4 || (mood === 5);
    x.strokeStyle = '#2a1d15'; x.lineCap = 'round';
    if (closed) { x.lineWidth = 2.6; x.beginPath(); x.arc(15, mood === 5 ? 0 : -3, 4.5, .2, Math.PI - .2); x.stroke(); }
    else { x.save(); x.translate(15, -3); x.scale(1, bl); ell(0, 0, 3.4, 4.4, '#2a1d15'); circ(1.2, -1.6, 1.1, 'rgba(255,255,255,.8)'); x.restore(); }
    const bA = mood === 2 ? .25 : mood === 3 ? -.3 : mood === 6 ? .15 : 0;
    x.lineWidth = 2.6; x.beginPath(); x.moveTo(9, -13 - bA * 6); x.lineTo(21, -13 + bA * 6); x.stroke();
    x.strokeStyle = P.bd ? mix(P.bd, '#ffffff', .25) : '#8a4a32'; x.lineWidth = 2.4; x.beginPath();
    if (mood === 1 || mood === 4) x.arc(18, 10, 6, .25, 1.45); else if (mood === 2 || mood === 3) x.arc(18, 20, 6, -1.35, -.35); else { x.moveTo(13, 15); x.lineTo(22, 14); }
    x.stroke();
    if (!P.bd) { x.globalAlpha *= .22; circ(8, 10, 6, '#e0605a'); x.globalAlpha = a.al; }
    if (P.cap === 'kufi') {
      x.beginPath(); x.moveTo(-31, -4); x.bezierCurveTo(-31, -40, 31, -40, 31, -6); x.quadraticCurveTo(0, -10, -31, -4); x.fillStyle = P.capc; x.fill();
      x.strokeStyle = rgba('#000000', .08); x.lineWidth = 3; x.beginPath(); x.moveTo(-30, -10); x.quadraticCurveTo(0, -15, 30, -12); x.stroke();
    } else {
      x.beginPath(); x.moveTo(26, -8); x.bezierCurveTo(30, -44, -34, -46, -34, -6); x.quadraticCurveTo(-38, 30, -46, 54); x.lineTo(-20, 50); x.quadraticCurveTo(-24, 20, -22, 6); x.quadraticCurveTo(0, -12, 26, -8); x.fillStyle = P.capc; x.fill();
      x.globalAlpha *= .5; x.beginPath(); x.moveTo(-34, -4); x.quadraticCurveTo(-40, 30, -46, 54); x.lineTo(-36, 54); x.quadraticCurveTo(-30, 24, -26, -2); x.fillStyle = '#d8d2c6'; x.fill(); x.globalAlpha = a.al;
      if (P.agal) { x.strokeStyle = '#1d1a18'; x.lineWidth = 5; x.beginPath(); x.ellipse(-4, -22, 31, 7, -.12, Math.PI * .95, TAU * 1.02); x.stroke(); }
    }
  }
  x.restore();
  // كتاب، صندوق
  if (p.book > .5) { const bx = lerp(h1[0], S2[0] + Math.sin(tor) * 60, .5) + 30, by = h1[1] - 8; book(bx, by, .8); }
  if (p.box > .5) { rr(-52, -338, 104, 66, 8, '#b98a52'); rr(-52, -312, 104, 9, 2, '#8e6638'); rr(-52, -338, 104, 10, 6, '#c99a62'); }
  // ذراع قريبة
  const h2 = limb(S2[0], S2[1], p.ra[0], p.ra[1], L1, L2, 23, P.w ? P.th : mix(P.th, '#ffffff', .1), tor + swing, P.w ? null : P.sh);
  hand(h2, sk, hk(p.finger > .5 ? 'finger' : ''), 0);
  x.restore();
  return { s };
}

// ===== الأدوات =====
function book(px, py, s = 1) {
  x.save(); x.translate(px, py); x.scale(s, s);
  blob([[-48, -6], [0, 5], [48, -6], [48, 22], [0, 33], [-48, 22]], '#1d5444');
  blob([[-43, -11], [-2, 0], [-2, 27], [-43, 16]], '#fbf3e1'); blob([[43, -11], [2, 0], [2, 27], [43, 16]], '#efe2c6');
  x.strokeStyle = 'rgba(120,90,50,.35)'; x.lineWidth = 2; for (let i = 0; i < 3; i++) { x.beginPath(); x.moveTo(-36, -2 + i * 7); x.lineTo(-8, 5 + i * 7); x.stroke(); x.beginPath(); x.moveTo(8, 5 + i * 7); x.lineTo(36, -2 + i * 7); x.stroke(); }
  rr(-2, -1, 4, 30, 2, '#c9a24e'); x.restore();
}
function coin(px, py, r = 22) {
  circ(px, py + 3, r, '#9a6c18'); const g = x.createRadialGradient(px - r * .4, py - r * .4, 1, px, py, r); g.addColorStop(0, '#fff0b8'); g.addColorStop(.5, C.gold); g.addColorStop(1, '#b8861f'); circ(px, py, r, g);
  x.strokeStyle = 'rgba(140,95,20,.6)'; x.lineWidth = 2; x.beginPath(); x.arc(px, py, r * .66, 0, TAU); x.stroke(); star8(px, py, r * .28, 'rgba(160,110,25,.55)');
}
function lantern(px, py, s = 1, t = 0) {
  x.save(); x.translate(px, py); x.rotate(Math.sin(t * 1.3 + px) * .045); x.scale(s, s);
  const fl = .85 + Math.sin(t * 9 + px) * .06 + Math.sin(t * 13.7) * .04;
  x.save(); x.globalCompositeOperation = 'lighter'; glow(0, 0, 90, '#ffb54a', .35 * fl); x.restore();
  x.strokeStyle = '#7a5a22'; x.lineWidth = 2; x.beginPath(); x.moveTo(0, -80); x.lineTo(0, -32); x.stroke();
  blob([[-8, -34], [8, -34], [14, -26], [-14, -26]], '#9a7426');
  x.beginPath(); x.moveTo(-14, -26); x.quadraticCurveTo(-22, -2, -14, 18); x.lineTo(14, 18); x.quadraticCurveTo(22, -2, 14, -26); x.closePath(); x.fillStyle = '#a77d2a'; x.fill();
  x.beginPath(); x.moveTo(-9, -20); x.quadraticCurveTo(-15, -2, -9, 13); x.lineTo(9, 13); x.quadraticCurveTo(15, -2, 9, -20); x.closePath(); const g = x.createRadialGradient(0, -2, 1, 0, -2, 18); g.addColorStop(0, '#fffbe0'); g.addColorStop(1, '#ffc35a'); x.fillStyle = g; x.globalAlpha *= fl; x.fill(); x.globalAlpha /= fl;
  x.strokeStyle = 'rgba(120,80,20,.6)'; x.lineWidth = 1.5; x.beginPath(); x.moveTo(0, -20); x.lineTo(0, 13); x.stroke();
  blob([[-16, 18], [16, 18], [8, 28], [-8, 28]], '#8a6420'); circ(0, 32, 3, '#8a6420'); x.restore();
}
function cloudShape(cx, cy, s, col = '#ffffff', sh = 'rgba(160,170,190,.35)') {
  x.save(); x.translate(cx, cy); x.scale(s, s);
  const pts = [[-70, 10, 30], [-36, -10, 40], [6, -26, 48], [48, -8, 38], [78, 10, 26]];
  x.fillStyle = sh; x.beginPath(); pts.forEach(([a, b, r]) => { x.moveTo(a + r, b + 8); x.arc(a, b + 8, r, 0, TAU); }); x.fill();
  x.fillStyle = col; x.beginPath(); pts.forEach(([a, b, r]) => { x.moveTo(a + r, b); x.arc(a, b, r, 0, TAU); }); x.rect(-70, 10, 148, 20); x.fill();
  x.restore();
}
function mini(px, py, s, kind, col, sk, t, ph) { // شخص صغير بسيط للحشود
  x.save(); x.translate(px, py + Math.sin(t * 2 + ph) * 1.5); x.scale(s, s);
  x.beginPath(); x.moveTo(-24, 0); x.quadraticCurveTo(-26, -60, -18, -86); x.quadraticCurveTo(0, -94, 18, -86); x.quadraticCurveTo(26, -60, 24, 0); x.closePath(); x.fillStyle = col; x.fill();
  x.globalAlpha *= .25; blob([[-24, 0], [-22, -70], [-16, -86], [-6, -88], [-8, 0]], '#000'); x.globalAlpha /= .25;
  if (kind === 2) { circ(0, -106, 22, mix(col, '#000000', .25)); ell(5, -104, 12, 15, sk); }
  else { circ(0, -106, 19, sk); x.beginPath(); x.moveTo(-19, -106); x.bezierCurveTo(-19, -130, 19, -130, 19, -107); x.fillStyle = kind === 1 ? '#f2efe8' : '#ffffff'; x.fill(); if (kind === 1) { ell(-14, -96, 8, 16, '#f2efe8'); } }
  x.restore();
}
const PROPS = {
  coin: (p) => coin(p.x, p.y, 22 * p.s),
  coins: (p) => { for (let i = 0; i < 6; i++) coin(p.x - 30 + (i % 3) * 30 + (i > 2 ? 15 : 0), p.y - (i > 2 ? 22 : 0), 17 * p.s); },
  bag: (p) => { x.save(); x.translate(p.x, p.y); x.scale(p.s, p.s); smooth([[-36, 0], [36, 0], [30, -46], [12, -62], [-12, -62], [-30, -46]], hgrad([[0, '#7d5530'], [.6, '#a87644'], [1, '#bb8a55']], -36, 36)); rr(-15, -72, 30, 14, 6, '#6e4a28'); coin(0, -28, 13); x.restore(); },
  book: (p) => book(p.x, p.y, p.s),
  stand: (p) => { x.save(); x.translate(p.x, p.y); x.scale(p.s, p.s); x.strokeStyle = '#6e4a2a'; x.lineWidth = 10; x.lineCap = 'round'; x.beginPath(); x.moveTo(-40, 0); x.lineTo(40, -62); x.moveTo(40, 0); x.lineTo(-40, -62); x.stroke(); x.strokeStyle = '#8a6036'; x.lineWidth = 4; x.beginPath(); x.moveTo(-38, -4); x.lineTo(38, -62); x.stroke(); book(0, -80, 1.05); x.restore(); },
  house: (p) => { x.save(); x.translate(p.x, p.y); x.scale(p.s, p.s); rr(-120, -180, 240, 180, 6, hgrad([[0, '#d9c19a'], [1, '#efdcb9']], -120, 120)); blob([[-134, -176], [134, -176], [122, -204], [-122, -204]], '#c09c6c'); arch(-55, 0, 60, 120, '#5e4426'); arch(55, -60, 50, 70, '#ffe4a0'); x.save(); x.globalCompositeOperation = 'lighter'; glow(55, -90, 70, '#ffc060', .25); x.restore(); x.restore(); },
  mosque: (p, t) => {
    x.save(); x.translate(p.x, p.y); x.scale(p.s, p.s); const f = p.c || '#1d4a40', fl = mix(f, '#ffffff', .12), fd = mix(f, '#000000', .25);
    for (const mx of [-205, 205]) { rr(mx - 16, -360, 32, 360, 4, hgrad([[0, fd], [.5, fl], [1, f]], mx - 16, mx + 16)); rr(mx - 24, -300, 48, 12, 4, fl); rr(mx - 20, -380, 40, 22, 6, f); x.beginPath(); x.moveTo(mx - 20, -380); x.quadraticCurveTo(mx, -440, mx, -450); x.quadraticCurveTo(mx, -440, mx + 20, -380); x.fillStyle = fl; x.fill(); rr(mx - 2, -462, 4, 14, 2, C.gold); arch(mx, -320, 12, 26, '#ffd98a'); }
    rr(-165, -170, 330, 170, 4, hgrad([[0, fd], [.5, f], [1, fl]], -165, 165));
    x.beginPath(); x.moveTo(-105, -170); x.bezierCurveTo(-110, -290, 110, -290, 105, -170); x.closePath(); x.fillStyle = hgrad([[0, fd], [.55, fl], [1, f]], -105, 105); x.fill();
    rr(-110, -178, 220, 12, 4, fl); rr(-3, -320, 6, 40, 2, C.gold); x.save(); x.translate(0, -328); x.beginPath(); x.arc(0, 0, 9, R(40), R(320)); x.strokeStyle = C.gold; x.lineWidth = 4; x.stroke(); x.restore();
    const fl2 = .9 + Math.sin((t || 0) * 3) * .05; x.save(); x.globalCompositeOperation = 'lighter'; glow(0, -60, 200, '#ffb850', .22 * fl2); x.restore();
    for (let i = -2; i <= 2; i++) arch(i * 60, -12, 34, i ? 64 : 100, i ? '#f7cf78' : '#ffe3a0');
    for (let i = -2; i <= 2; i++) if (i) arch(i * 60, -112, 20, 26, '#f2c46a');
    x.restore();
  },
  tap: (p) => { x.save(); x.translate(p.x, p.y); x.scale(p.s, p.s); rr(-20, -260, 40, 260, 4, '#1f4d44'); rr(-12, -180, 34, 12, 6, '#c8c8c8'); rr(16, -180, 8, 22, 3, '#c8c8c8'); x.restore(); },
  palm: (p, t) => {
    x.save(); x.translate(p.x, p.y); x.scale(p.s, p.s);
    for (let i = 0; i < 12; i++) { const q = i / 12, px = Math.sin(q * 1.6) * 14 * q, py = -q * 205; rr(px - 9 + q * 2, py - 18, 18 - q * 3, 20, 6, i % 2 ? '#8a6a43' : '#7a5b37'); }
    const sw = Math.sin((t || 0) * 1.2 + p.x) * .05;
    x.save(); x.translate(10, -208);
    for (let i = 0; i < 9; i++) {
      const a = R(-170 + i * 40) + sw * (i % 2 ? 1 : -1); x.save(); x.rotate(a);
      x.beginPath(); x.moveTo(0, 0); x.quadraticCurveTo(50, -22, 104, 18); x.quadraticCurveTo(52, 2, 0, 6); x.fillStyle = i % 2 ? '#3f7d4f' : '#4f9460'; x.fill();
      x.strokeStyle = 'rgba(20,60,30,.35)'; x.lineWidth = 2; x.beginPath(); x.moveTo(0, 2); x.quadraticCurveTo(50, -10, 102, 16); x.stroke(); x.restore();
    }
    for (let i = 0; i < 5; i++) circ(-8 + i * 5, 10 + (i % 2) * 6, 6, '#a0522d'); x.restore(); x.restore();
  },
  plant: (p, t) => {
    x.save(); x.translate(p.x, p.y); x.scale(p.s, p.s);
    for (let i = 0; i < 7; i++) { x.save(); x.translate(0, -44); x.rotate(R(-66 + i * 22) + Math.sin((t || 0) * 1.4 + i) * .04); x.beginPath(); x.moveTo(0, 0); x.quadraticCurveTo(-14, -34, 0, -62 - (i % 2) * 12); x.quadraticCurveTo(14, -34, 0, 0); x.fillStyle = i % 2 ? '#4f8a55' : '#5f9e60'; x.fill(); x.strokeStyle = 'rgba(30,60,30,.3)'; x.lineWidth = 1.5; x.beginPath(); x.moveTo(0, -4); x.lineTo(0, -56); x.stroke(); x.restore(); }
    x.beginPath(); x.moveTo(-26, -44); x.lineTo(26, -44); x.lineTo(20, 0); x.lineTo(-20, 0); x.closePath(); x.fillStyle = hgrad([[0, '#94532f'], [.6, '#c47a4c'], [1, '#d08a5a']], -26, 26); x.fill(); rr(-30, -50, 60, 10, 4, '#a85f38');
    x.restore();
  },
  lantern: (p, t) => lantern(p.x, p.y, p.s, t),
  kaaba: (p) => { x.save(); x.translate(p.x, p.y); x.scale(p.s, p.s); rr(-90, -170, 180, 170, 4, hgrad([[0, '#0c0c0c'], [1, '#262626']], -90, 90)); rr(-90, -138, 180, 18, 0, C.gold); rr(30, -100, 34, 100, 3, '#4a3812'); x.restore(); },
  scales: (p, t) => {
    x.save(); x.translate(p.x, p.y); x.scale(p.s, p.s); const a = Math.sin(t * 1.2) * .04 + (p.tilt || 0);
    const gg = hgrad([[0, '#a7781f'], [.5, '#f3cf72'], [1, '#b8862a']], -8, 8);
    x.save(); x.globalCompositeOperation = 'lighter'; glow(0, -150, 160, '#ffcf70', .12); x.restore();
    x.beginPath(); x.moveTo(-46, 0); x.quadraticCurveTo(0, -24, 46, 0); x.closePath(); x.fillStyle = '#b8862a'; x.fill(); rr(-7, -175, 14, 160, 5, gg); circ(0, -178, 11, '#f3cf72');
    x.translate(0, -170); x.rotate(a); rr(-118, -5, 236, 10, 5, hgrad([[0, '#b8862a'], [.5, '#f6d888'], [1, '#b8862a']], -118, 118));
    for (const sx of [-108, 108]) {
      const la = -a; x.save(); x.translate(sx, 0); x.rotate(la);
      x.strokeStyle = 'rgba(170,120,40,.9)'; x.lineWidth = 2; x.beginPath(); x.moveTo(0, 0); x.lineTo(-34, 74); x.moveTo(0, 0); x.lineTo(34, 74); x.moveTo(0, 0); x.lineTo(0, 74); x.stroke();
      x.beginPath(); x.ellipse(0, 76, 44, 13, 0, 0, Math.PI); x.fillStyle = hgrad([[0, '#b8862a'], [.5, '#f6d888'], [1, '#a7781f']], -44, 44); x.fill(); ell(0, 76, 44, 5, '#c99a3a'); x.restore();
    }
    x.restore();
  },
  heart: (p, t) => { const k = 1 + Math.sin(t * 6) * .04; x.save(); x.globalCompositeOperation = 'lighter'; glow(p.x, p.y, 90 * p.s, '#ff6a6a', .25); x.restore(); heartShape(p.x, p.y + Math.sin(t * 3) * 4, 2.6 * p.s * k, p.c || '#d9534f'); x.globalAlpha *= .5; heartShape(p.x - 12 * p.s, p.y - 14 * p.s + Math.sin(t * 3) * 4, .7 * p.s * k, '#ffffff'); x.globalAlpha *= 2; },
  sun: (p, t) => { x.save(); x.globalCompositeOperation = 'lighter'; glow(p.x, p.y, 220 * p.s, '#ffcf70', .45); x.restore(); const g = x.createRadialGradient(p.x - 12 * p.s, p.y - 12 * p.s, 2, p.x, p.y, 48 * p.s); g.addColorStop(0, '#fff6d2'); g.addColorStop(1, '#ffc65a'); circ(p.x, p.y, 46 * p.s, g); },
  moon: (p) => crescent(p.x, p.y, 40 * p.s),
  cloud: (p, t) => { const dx = Math.sin(t * .3 + p.x) * 12; cloudShape(p.x + dx, p.y, p.s * .8, p.c || '#ffffff', p.c ? rgba('#000000', .15) : 'rgba(160,170,190,.35)'); },
  door: (p) => { x.save(); x.translate(p.x, p.y); x.scale(p.s, p.s); const g = x.createLinearGradient(0, -300, 0, 0); g.addColorStop(0, '#fffbe6'); g.addColorStop(1, '#f2c96a'); arch(0, 0, 130, 260, '#7a5a26'); arch(0, -8, 108, 240, g); x.restore(); },
  plate: (p) => { x.save(); x.translate(p.x, p.y); x.scale(p.s, p.s); ell(0, 2, 64, 18, 'rgba(0,0,0,.12)'); ell(0, 0, 62, 17, '#e9dcc2'); ell(0, -2, 48, 12, '#d6c3a0'); x.strokeStyle = '#3f7d6f'; x.lineWidth = 2; x.beginPath(); x.ellipse(0, 0, 56, 15, 0, 0, TAU); x.stroke(); for (let i = 0; i < 3; i++) { ell(-26 + i * 26, -12, 22, 13, '#c98a3e'); ell(-30 + i * 26, -16, 8, 4, 'rgba(255,230,180,.6)'); } x.restore(); },
  jug: (p) => { x.save(); x.translate(p.x, p.y); x.scale(p.s, p.s); x.strokeStyle = '#9a5a38'; x.lineWidth = 7; x.beginPath(); x.arc(30, -46, 16, -1.4, 1.4); x.stroke(); smooth([[-24, 0], [24, 0], [32, -38], [14, -66], [-14, -66], [-32, -38]], hgrad([[0, '#8e4f2e'], [.6, '#c47a4c'], [1, '#d48e5c']], -32, 32)); rr(-13, -84, 26, 18, 5, '#a8613c'); blob([[-13, -82], [-24, -90], [-12, -76]], '#a8613c'); x.strokeStyle = 'rgba(255,230,190,.5)'; x.lineWidth = 3; x.beginPath(); x.moveTo(-20, -30); x.quadraticCurveTo(0, -24, 20, -30); x.stroke(); x.restore(); },
  stone: (p) => { x.save(); x.translate(p.x, p.y); x.scale(p.s, p.s); blob([[-44, 0], [44, 0], [38, -26], [12, -42], [-24, -36]], '#8d8577'); blob([[-44, 0], [-6, 0], [-12, -30], [-24, -36]], '#6f695b'); blob([[12, -42], [38, -26], [14, -24], [-4, -34]], '#a39b8c'); ell(52, -3, 9, 5, '#7c7568'); ell(-54, -2, 7, 4, '#8d8577'); x.restore(); },
  sign: (p) => { x.save(); x.translate(p.x, p.y); x.scale(p.s, p.s); rr(-6, -200, 12, 200, 3, '#7a5230'); blob([[-90, -190], [70, -190], [96, -168], [70, -146], [-90, -146]], '#3f7d4f'); blob([[90, -130], [-70, -130], [-96, -108], [-70, -86], [90, -86]], '#a14a3a'); x.restore(); },
  shield: (p) => { x.save(); x.translate(p.x, p.y); x.scale(p.s, p.s); x.save(); x.globalCompositeOperation = 'lighter'; glow(0, -10, 130, '#ffd070', .18); x.restore(); x.beginPath(); x.moveTo(0, -80); x.quadraticCurveTo(60, -70, 66, -56); x.quadraticCurveTo(66, 20, 0, 60); x.quadraticCurveTo(-66, 20, -66, -56); x.quadraticCurveTo(-60, -70, 0, -80); x.fillStyle = hgrad([[0, '#1f5443'], [.5, '#3a8a6c'], [1, '#24614e']], -66, 66); x.fill(); x.strokeStyle = C.gold; x.lineWidth = 6; x.stroke(); star8(0, -8, 22, C.gold); circ(0, -8, 9, '#2f6b57'); x.restore(); },
  fire: (p, t) => { x.save(); x.translate(p.x, p.y); x.scale(p.s, p.s); x.save(); x.globalCompositeOperation = 'lighter'; glow(0, -30, 110, '#ff7a2a', .35); x.restore(); for (let i = 0; i < 3; i++) { const h = 84 - i * 22 + Math.sin(t * 9 + i) * 8; x.beginPath(); x.moveTo(-40 + i * 12, 0); x.quadraticCurveTo(-30 + i * 10, -h * .5, Math.sin(t * 7 + i) * 6, -h); x.quadraticCurveTo(30 - i * 10, -h * .5, 40 - i * 12, 0); x.closePath(); x.fillStyle = ['#e2572b', '#f08a2c', '#ffd25e'][i]; x.fill(); } x.restore(); },
  water: (p, t) => { x.save(); x.translate(p.x, p.y); x.scale(p.s, p.s); for (let i = 0; i < 3; i++) { const y = ((t * 220 + i * 40) % 120); ell(0, y - 60, 6, 10, '#7cc3e8'); } x.restore(); },
  bubble: (p, t) => { x.save(); x.translate(p.x, p.y + Math.sin(t * 2) * 4); x.scale(p.s, p.s); x.fillStyle = 'rgba(0,0,0,.12)'; x.beginPath(); x.roundRect(-82, -54, 164, 92, 34); x.fill(); x.beginPath(); x.roundRect(-84, -62, 168, 92, 34); x.moveTo(-24, 26); x.lineTo(-40, 56); x.lineTo(4, 28); x.fillStyle = '#ffffff'; x.fill(); for (let i = -1; i <= 1; i++) circ(i * 34, -16, 10 + Math.max(0, Math.sin(t * 5 - i)) * 2, p.c || '#3f7d4f'); x.restore(); },
  hourglass: (p, t) => { x.save(); x.translate(p.x, p.y); x.scale(p.s, p.s); x.save(); x.globalCompositeOperation = 'lighter'; glow(0, -70, 90, '#ffd28a', .15); x.restore(); rr(-52, -144, 104, 14, 5, '#6e4a28'); rr(-52, -10, 104, 14, 5, '#6e4a28'); rr(-44, -132, 8, 124, 3, '#8a6036'); rr(36, -132, 8, 124, 3, '#8a6036'); blob([[-36, -130], [36, -130], [6, -70], [36, -10], [-36, -10], [-6, -70]], 'rgba(220,240,250,.45)'); const k = (t * .08) % 1; blob([[-27 + k * 24, -120 + k * 46], [27 - k * 24, -120 + k * 46], [3, -72], [-3, -72]], '#e9c47a'); blob([[-33 * k, -10 - 30 * k], [33 * k, -10 - 30 * k], [36, -10], [-36, -10]], '#e9c47a'); rr(-1, -72, 2, 62, 1, '#e9c47a'); x.restore(); },
  pen: (p) => { x.save(); x.translate(p.x, p.y); x.rotate(-.6); x.scale(p.s, p.s); rr(-8, -90, 16, 90, 4, '#6b4a2b'); blob([[-8, 0], [8, 0], [0, 22]], '#2a1d15'); x.restore(); },
  scroll: (p) => { x.save(); x.translate(p.x, p.y); x.scale(p.s, p.s); x.save(); x.globalCompositeOperation = 'lighter'; glow(0, -80, 200, '#ffd88a', .12); x.restore(); rr(-108, -150, 216, 150, 4, vgrad([[0, '#f6e7c4'], [1, '#e8d2a2']], -150, 0)); for (const yy of [-162, -10]) rr(-124, yy, 248, 22, 11, vgrad([[0, '#d9b47a'], [.5, '#b48848'], [1, '#8e6630']], yy, yy + 22)); x.strokeStyle = 'rgba(110,80,40,.45)'; x.lineWidth = 3; x.lineCap = 'round'; for (let i = 0; i < 5; i++) { x.beginPath(); const w = 150 - (i % 2) * 40; for (let k = 0; k <= w; k += 6) x.lineTo(84 - k, -120 + i * 22 + Math.sin(k * .3 + i) * 2); x.stroke(); } x.restore(); },
  gift: (p) => { x.save(); x.translate(p.x, p.y); x.scale(p.s, p.s); rr(-42, -62, 84, 62, 6, hgrad([[0, '#2c6646'], [1, '#4a9a66']], -42, 42)); rr(-6, -62, 12, 62, 2, C.gold); rr(-48, -76, 96, 18, 5, '#2f6b57'); rr(-6, -76, 12, 18, 2, C.gold); ell(-14, -84, 14, 9, C.gold, .4); ell(14, -84, 14, 9, C.gold, -.4); x.restore(); },
  cart: (p) => { x.save(); x.translate(p.x, p.y); x.scale(p.s, p.s); rr(-100, -110, 200, 70, 6, '#9a6b3c'); for (const w of [-60, 60]) { circ(w, -30, 30, '#6b4a2b'); circ(w, -30, 12, '#c9a46a'); } rr(90, -100, 80, 10, 4, '#6b4a2b'); x.restore(); },
  camel: (p, t) => {
    x.save(); x.translate(p.x, p.y); x.scale(p.s * (p.tilt < 0 ? -1 : 1), p.s); const f = '#cf9f62', d = '#a97a42', sw = Math.sin(t * 1.3 + p.x);
    for (const [l, c] of [[-56, d], [42, d], [-34, f], [64, f]]) { x.strokeStyle = c; x.lineWidth = 13; x.lineCap = 'round'; x.beginPath(); x.moveTo(l, -96); x.lineTo(l + 2, -50); x.lineTo(l - 2, -6); x.stroke(); ell(l - 1, -3, 10, 5, mix(c, '#000000', .2)); }
    x.strokeStyle = d; x.lineWidth = 4; x.beginPath(); x.moveTo(-74, -112); x.quadraticCurveTo(-92 + sw * 4, -80, -86 + sw * 6, -62); x.stroke();
    smooth([[-78, -96], [-74, -128], [-34, -166], [6, -134], [44, -146], [84, -112], [80, -86], [0, -82]], hgrad([[0, d], [.5, f], [1, mix(f, '#ffffff', .15)]], -80, 90));
    rr(-28, -150, 56, 34, 10, '#9e3b33'); rr(-28, -122, 56, 6, 3, C.gold); for (let i = 0; i < 4; i++) circ(-22 + i * 15, -112, 3, C.gold);
    x.save(); x.translate(78, -112); x.rotate(Math.sin(t * .9 + p.x) * .05); x.beginPath(); x.moveTo(-6, 10); x.quadraticCurveTo(16, -30, 30, -86); x.lineTo(48, -84); x.quadraticCurveTo(32, -30, 14, 16); x.closePath(); x.fillStyle = f; x.fill();
    smooth([[24, -88], [40, -102], [70, -96], [74, -82], [44, -76]], f); ell(36, -100, 5, 8, d, -.4); circ(52, -93, 2.8, '#2a1d15'); x.restore(); x.restore();
  },
  tree: (p, t) => {
    x.save(); x.translate(p.x, p.y); x.scale(p.s, p.s); const sw = Math.sin((t || 0) * 1.1 + p.x) * 2;
    x.beginPath(); x.moveTo(-16, 0); x.quadraticCurveTo(-8, -70, -14, -120); x.lineTo(14, -120); x.quadraticCurveTo(6, -70, 16, 0); x.closePath(); x.fillStyle = hgrad([[0, '#5e4229'], [1, '#8a6440']], -16, 16); x.fill();
    x.strokeStyle = '#6e4e30'; x.lineWidth = 8; x.lineCap = 'round'; x.beginPath(); x.moveTo(0, -100); x.lineTo(-40, -140); x.moveTo(0, -110); x.lineTo(38, -150); x.stroke();
    const bl = [[-56, -146, 46], [52, -150, 48], [0, -186, 62], [-30, -200, 42], [34, -208, 40], [0, -140, 44]];
    bl.forEach(([a, b, r]) => circ(a + sw, b + 6, r, '#356b45')); bl.forEach(([a, b, r]) => circ(a + sw - 4, b, r * .94, '#4f8f58')); bl.forEach(([a, b, r]) => circ(a + sw - 12, b - 12, r * .5, '#6aab6a'));
    for (const [a, b] of [[-34, -160], [28, -146], [0, -128], [44, -190], [-20, -206], [12, -178]]) { circ(a + sw, b, 8, '#d9534f'); circ(a + sw - 2, b - 3, 2.5, 'rgba(255,255,255,.6)'); }
    x.restore();
  },
  sheep: () => { },
  bread: (p) => { x.save(); x.translate(p.x, p.y); x.scale(p.s, p.s); ell(0, -18, 46, 20, hgrad([[0, '#b97a30'], [.6, '#e0aa58'], [1, '#d99c48']], -46, 46)); x.strokeStyle = '#a06a28'; x.lineWidth = 3; for (let i = -1; i <= 1; i++) { x.beginPath(); x.moveTo(i * 18 - 6, -28); x.lineTo(i * 18 + 6, -10); x.stroke(); } x.restore(); },
  rug: (p) => { x.save(); x.translate(p.x, p.y); x.scale(p.s, p.s); ell(0, 0, 150, 26, '#8e2f2f'); x.strokeStyle = C.gold; x.lineWidth = 3; x.beginPath(); x.ellipse(0, 0, 130, 18, 0, 0, TAU); x.stroke(); x.restore(); },
  mat: (p) => { x.save(); x.translate(p.x, p.y); x.scale(p.s, p.s); blob([[-78, 2], [78, 2], [62, -22], [-62, -22]], '#245a48'); blob([[-70, -1], [70, -1], [57, -19], [-57, -19]], '#2f7a5e'); x.strokeStyle = C.gold; x.lineWidth = 2.5; x.beginPath(); x.moveTo(-40, -4); x.lineTo(-30, -15); x.quadraticCurveTo(0, -24, 30, -15); x.lineTo(40, -4); x.stroke(); x.strokeStyle = 'rgba(233,189,95,.6)'; x.lineWidth = 1.5; for (let i = -6; i <= 6; i++) { x.beginPath(); x.moveTo(i * 12, 2); x.lineTo(i * 12, 7); x.stroke(); } x.restore(); },
  key: (p) => { x.save(); x.translate(p.x, p.y); x.scale(p.s, p.s); x.strokeStyle = C.gold; x.lineWidth = 10; x.beginPath(); x.arc(-40, 0, 22, 0, TAU); x.moveTo(-18, 0); x.lineTo(50, 0); x.moveTo(36, 0); x.lineTo(36, 18); x.moveTo(50, 0); x.lineTo(50, 22); x.stroke(); x.restore(); },
  steps: (p) => { x.save(); x.translate(p.x, p.y); x.scale(p.s, p.s); for (let i = 0; i < 5; i++) { rr(-150 + i * 60, -i * 40 - 40, 300 - i * 60, 40, 3, i % 2 ? '#d8c39c' : '#e6d3b3'); rr(-150 + i * 60, -i * 40 - 40, 300 - i * 60, 6, 3, '#f2e4c8'); } x.restore(); },
  mountain: (p) => { x.save(); x.translate(p.x, p.y); x.scale(p.s, p.s); blob([[-230, 0], [-20, -270], [40, -200], [230, 0]], '#7a8596'); blob([[-20, -270], [40, -200], [230, 0], [30, 0], [10, -150]], '#5f697a'); blob([[-74, -200], [-20, -270], [30, -210], [6, -196], [-12, -214], [-40, -188]], '#f2f2f2'); blob([[-150, 0], [-90, -110], [-40, -60], [10, 0]], 'rgba(255,255,255,.08)'); x.restore(); },
  lock: (p) => { x.save(); x.translate(p.x, p.y); x.scale(p.s, p.s); x.strokeStyle = '#9aa3ad'; x.lineWidth = 12; x.beginPath(); x.arc(0, -60, 30, Math.PI, 0); x.stroke(); rr(-46, -60, 92, 70, 10, hgrad([[0, '#a7781f'], [.5, '#f0c868'], [1, '#b8862a']], -46, 46)); circ(0, -30, 9, '#5a4210'); x.restore(); },
  tongue: () => { },
  people: (p, t) => { const K = p.tilt || 5; for (let r = 1; r >= 0; r--) for (let i = 0; i < K; i++) { if (r && i % 2) continue; const px = p.x + (i - K / 2 + .5) * 70 * p.s + r * 35 * p.s, py = p.y - r * 26 * p.s; const kind = (i * 7 + r) % 5 === 2 ? 2 : (i % 3 === 1 ? 1 : 0); const cols = ['#e9e3d5', '#2f6b57', '#d8cfbd', '#3d6e8f', '#8f6a80']; const col = kind === 2 ? '#7a5a70' : cols[(i + r) % 4]; x.save(); x.globalAlpha *= r ? .8 : 1; mini(px, py, p.s * (r ? .88 : 1), kind, r ? mix(col, '#9aa0b0', .3) : col, ['#dba57a', '#c48f63', '#e3b08a'][i % 3], t, i + r * 3); x.restore(); } },
  rows: (p, t) => { for (let r = 0; r < 2; r++) for (let i = 0; i < 6; i++) { x.save(); x.translate(p.x + (i - 2.5) * 95 + r * 30, p.y - r * 60); x.scale(.55 - r * .08, .55 - r * .08); blob([[-30, 0], [30, 0], [28, -120], [-28, -120]], '#f3efe6'); circ(0, -146, 28, '#ffffff'); x.restore(); } },
};
function crescent(cx, cy, r) {
  const c = bake('moon' + Math.round(r), () => { circ(r * 1.6, r * 1.6, r, '#fbeec0'); x.globalCompositeOperation = 'destination-out'; circ(r * 1.6 + r * .42, r * 1.6 - r * .25, r * .9, '#000'); }, r * 3.2, r * 3.2, 0, 0);
  x.save(); x.globalCompositeOperation = 'lighter'; glow(cx, cy, r * 4, '#fff1c0', .22); x.restore(); x.drawImage(c, cx - r * 1.6, cy - r * 1.6);
}

// ===== عناصر القصص (قرآن وسنة) — ما نرسم أي نبي، بس أماكن ورموز =====
function waves(y, col, amp, sp, t, ph, foam) {
  x.beginPath(); x.moveTo(-M, H); x.lineTo(-M, y);
  for (let i = -M; i <= W + M; i += 14) x.lineTo(i, y + Math.sin(i / 46 + t * sp + ph) * amp + Math.sin(i / 19 + t * sp * 1.7) * amp * .3);
  x.lineTo(W + M, H); x.closePath(); x.fillStyle = col; x.fill();
  if (foam) { x.strokeStyle = foam; x.lineWidth = 3; x.beginPath(); for (let i = -M; i <= W + M; i += 14) { const yy = y + Math.sin(i / 46 + t * sp + ph) * amp + Math.sin(i / 19 + t * sp * 1.7) * amp * .3; i === -M ? x.moveTo(i, yy) : x.lineTo(i, yy); } x.stroke(); }
}
Object.assign(PROPS, {
  whale: (p, t) => {
    x.save(); x.translate(p.x, p.y + Math.sin(t * 1.2) * 8); x.scale(p.s * (p.tilt < 0 ? -1 : 1), p.s);
    x.save(); x.translate(-165, -5); x.rotate(Math.sin(t * 2.2) * .22); x.beginPath(); x.moveTo(0, 0); x.quadraticCurveTo(-40, -20, -76, -56); x.quadraticCurveTo(-60, -6, -52, 0); x.quadraticCurveTo(-60, 6, -76, 50); x.quadraticCurveTo(-40, 16, 0, 0); x.fillStyle = '#2e5876'; x.fill(); x.restore();
    x.beginPath(); x.moveTo(-170, 0); x.bezierCurveTo(-160, -112, 90, -124, 152, -30); x.quadraticCurveTo(172, 10, 120, 30); x.bezierCurveTo(40, 60, -120, 50, -170, 0); x.fillStyle = vgrad([[0, '#4f7fa2'], [.6, '#3a6888'], [1, '#2e5876']], -110, 40); x.fill();
    x.beginPath(); x.moveTo(-60, 30); x.bezierCurveTo(0, 50, 90, 40, 130, 20); x.lineTo(122, 33); x.bezierCurveTo(40, 60, -40, 52, -60, 30); x.fillStyle = '#b6d2e0'; x.fill();
    x.strokeStyle = 'rgba(80,120,150,.6)'; x.lineWidth = 2; for (let i = 0; i < 5; i++) { x.beginPath(); x.moveTo(-40 + i * 30, 38 + i * .5); x.lineTo(-30 + i * 30, 46 - i); x.stroke(); }
    x.save(); x.translate(10, 20); x.rotate(.5 + Math.sin(t * 1.5) * .15); ell(30, 0, 34, 11, '#2e5876'); x.restore();
    for (let i = 0; i < 9; i++) circ(-90 + rnd(i) * 160, -60 + rnd(i + 4) * 50, 3 + rnd(i + 8) * 4, 'rgba(220,240,250,.18)');
    circ(98, -40, 7.5, '#10202e'); circ(100, -43, 2.4, '#fff'); x.strokeStyle = '#24465e'; x.lineWidth = 4; x.lineCap = 'round'; x.beginPath(); x.arc(122, 4, 22, .3, 1.15); x.stroke(); x.restore();
  },
  ship: (p, t) => {
    x.save(); x.translate(p.x, p.y + Math.sin(t * 1.4) * 6); x.rotate(Math.sin(t * 1.1) * .04); x.scale(p.s, p.s);
    rr(-7, -240, 14, 200, 4, '#5d3b20');
    x.beginPath(); x.moveTo(8, -228); x.quadraticCurveTo(110 + Math.sin(t * 2) * 6, -150, 112, -72); x.lineTo(8, -72); x.closePath(); x.fillStyle = hgrad([[0, '#d9ccb0'], [1, '#f6eedb']], 8, 112); x.fill();
    x.beginPath(); x.moveTo(-8, -206); x.quadraticCurveTo(-84 + Math.sin(t * 2) * 4, -150, -90, -82); x.lineTo(-8, -82); x.closePath(); x.fillStyle = hgrad([[0, '#ece2c8'], [1, '#d4c4a2']], -90, -8); x.fill();
    blob([[7, -240], [46, -232 + Math.sin(t * 5) * 3], [7, -224]], '#a14a3a');
    x.beginPath(); x.moveTo(-160, -42); x.lineTo(160, -42); x.quadraticCurveTo(140, 10, 110, 22); x.lineTo(-110, 22); x.quadraticCurveTo(-140, 10, -160, -42); x.fillStyle = vgrad([[0, '#9a6b3c'], [1, '#5e3a1e']], -42, 22); x.fill();
    x.strokeStyle = 'rgba(60,35,15,.45)'; x.lineWidth = 2.5; for (let i = 0; i < 3; i++) { x.beginPath(); x.moveTo(-150 + i * 12, -24 + i * 15); x.lineTo(150 - i * 12, -24 + i * 15); x.stroke(); } rr(-160, -46, 320, 8, 3, '#b07c46'); x.restore();
  },
  ark: (p, t) => {
    x.save(); x.translate(p.x, p.y + Math.sin(t * 1.2) * 7); x.rotate(Math.sin(t) * .03); x.scale(p.s, p.s);
    x.beginPath(); x.moveTo(-210, -74); x.lineTo(210, -74); x.quadraticCurveTo(190, 0, 160, 20); x.lineTo(-160, 20); x.quadraticCurveTo(-190, 0, -210, -74); x.fillStyle = vgrad([[0, '#7e532d'], [1, '#4a2e16']], -74, 20); x.fill();
    for (let i = 0; i < 4; i++) rr(-196 + i * 8, -60 + i * 20, 392 - i * 16, 3, 2, 'rgba(40,22,10,.5)');
    rr(-124, -176, 248, 104, 8, hgrad([[0, '#6e4a2a'], [1, '#9a6b40']], -124, 124)); blob([[-146, -172], [146, -172], [0, -236]], '#5d3b20'); blob([[0, -236], [146, -172], [100, -172]], '#4a2e18');
    for (let i = -1; i <= 1; i++) arch(i * 72, -98, 34, 50, '#ffd98a'); x.restore();
  },
  cave: (p) => { x.save(); x.translate(p.x, p.y); x.scale(p.s, p.s); smooth([[-350, 0], [-300, -260], [-170, -420], [40, -460], [230, -380], [350, -220], [370, 0]], '#6f5d4a'); smooth([[-300, 0], [-260, -230], [-150, -380], [20, -410], [190, -340], [300, -200], [320, 0]], vgrad([[0, '#a08a70'], [1, '#7d6a55']], -410, 0)); x.strokeStyle = 'rgba(60,45,30,.25)'; x.lineWidth = 4; for (let i = 0; i < 5; i++) { x.beginPath(); x.moveTo(-260 + i * 20, -60 - i * 60); x.quadraticCurveTo(0, -90 - i * 64, 280 - i * 25, -50 - i * 55); x.stroke(); } x.beginPath(); x.moveTo(-130, 0); x.quadraticCurveTo(-140, -270, 0, -290); x.quadraticCurveTo(140, -270, 130, 0); x.closePath(); x.fillStyle = vgrad([[0, '#140f0a'], [1, '#2e2219']], -290, 0); x.fill(); x.restore(); },
  rock: (p) => { x.save(); x.translate(p.x, p.y); x.scale(p.s, p.s); ell(0, -110, 140, 115, vgrad([[0, '#9a8c78'], [1, '#6f6352']], -225, 0)); ell(-40, -150, 60, 36, 'rgba(255,255,255,.1)', -.4); x.restore(); },
  ant: (p, t) => { x.save(); x.translate(p.x + (p.tilt || 0) * t * 20, p.y); x.scale(p.s, p.s); const c = '#3a2a20'; for (const [a, r] of [[-26, 13], [0, 10], [26, 16]]) circ(a, -14, r, c); x.strokeStyle = c; x.lineWidth = 3; for (let i = -1; i <= 1; i++) { const k = Math.sin(t * 14 + i) * 5; x.beginPath(); x.moveTo(i * 8, -14); x.lineTo(i * 14 + k, 0); x.moveTo(i * 8, -14); x.lineTo(i * 14 - k, -30); x.stroke(); } x.beginPath(); x.moveTo(30, -26); x.lineTo(44, -44); x.moveTo(34, -26); x.lineTo(52, -38); x.stroke(); circ(30, -18, 3, 'rgba(255,255,255,.35)'); x.restore(); },
  ants: (p, t) => { for (let i = 0; i < (p.tilt || 7); i++) PROPS.ant({ x: ((p.x + i * 90 + t * 40) % (W + 100)) - 50, y: p.y - (i % 2) * 14, s: .55 * p.s }, t + i); },
  stars11: (p, t) => { for (let i = 0; i < 11; i++) { const a = R(-160 + i * 14), r = 250; const bow = (p.tilt || 0) * Math.sin(t * 1.5) * .5; x.save(); x.translate(p.x + Math.cos(a) * r, p.y + Math.sin(a) * r * .55 + 40); x.globalCompositeOperation = 'lighter'; glow(0, 0, 40, '#ffe39a', .3); x.globalCompositeOperation = 'source-over'; x.rotate(t * .4 + i); twinkle(0, 0, 20 + bow * 4, '#ffe9a8'); x.restore(); } },
  gourd: (p, t) => { x.save(); x.translate(p.x, p.y); x.scale(p.s, p.s); x.strokeStyle = '#3f7d4f'; x.lineWidth = 8; x.beginPath(); x.moveTo(-160, 0); x.quadraticCurveTo(-100, -230, 0, -240); x.quadraticCurveTo(100, -230, 160, 0); x.stroke(); for (let i = 0; i < 9; i++) { const q = i / 8, ax = -160 + q * 320, ay = -Math.sin(q * Math.PI) * 235; x.save(); x.translate(ax, ay); x.rotate(Math.sin(t + i) * .1); heartShape(0, 30, 2, i % 2 ? '#4f9460' : '#5fa870'); x.restore(); } for (const q of [.25, .7]) { const ax = -160 + q * 320, ay = -Math.sin(q * Math.PI) * 235; ell(ax, ay + 50, 18, 26, '#b9c96a'); } x.restore(); },
  seawall: (p, t) => {
    x.save(); x.translate(p.x, p.y); x.scale(p.s * (p.tilt < 0 ? -1 : 1), p.s);
    x.beginPath(); x.moveTo(0, 0); x.lineTo(0, -600); for (let i = 0; i <= 10; i++) x.lineTo(i * 26, -600 + Math.sin(t * 2 + i) * 10 + i * 4); x.lineTo(240, 0); x.closePath();
    x.fillStyle = hgrad([[0, '#9fd2ea'], [.12, '#4f94bf'], [.6, '#2c6b96'], [1, '#1b4a6e']], 0, 240); x.fill();
    x.save(); x.clip(); x.fillStyle = vgrad([[0, 'rgba(255,255,255,.25)'], [.5, 'rgba(255,255,255,0)']], -600, 0); x.fillRect(0, -620, 260, 620);
    x.strokeStyle = 'rgba(255,255,255,.22)'; x.lineWidth = 3; for (let k = 0; k < 9; k++) { const yy = -((t * 30 + k * 70) % 620); x.beginPath(); x.moveTo(10, yy); x.quadraticCurveTo(120, yy - 20 + Math.sin(t * 2 + k) * 10, 230, yy); x.stroke(); }
    for (let k = 0; k < 10; k++) circ(30 + rnd(k) * 190, -((t * 40 + rnd(k + 3) * 600) % 600), 3 + rnd(k + 5) * 4, 'rgba(230,248,255,.35)'); x.restore();
    x.strokeStyle = 'rgba(240,252,255,.9)'; x.lineWidth = 6; x.beginPath(); x.moveTo(2, 0); x.lineTo(2, -600); x.stroke(); x.restore();
  },
  staff: (p, t) => { x.save(); x.translate(p.x, p.y); x.rotate(.15); x.scale(p.s, p.s); x.save(); x.globalCompositeOperation = 'lighter'; glow(0, -150, 140, '#ffe2a0', .18 + Math.sin((t || 0) * 2) * .04); x.restore(); rr(-7, -262, 14, 262, 7, hgrad([[0, '#5e3d20'], [.5, '#9a6b40'], [1, '#6e4a2a']], -7, 7)); x.strokeStyle = '#7a5230'; x.lineWidth = 13; x.lineCap = 'round'; x.beginPath(); x.arc(-22, -262, 22, 0, Math.PI, true); x.stroke(); x.restore(); },
  flowers: (p, t) => { for (let i = 0; i < 11; i++) { const fx = p.x + (i - 5) * 40 * p.s, fy = p.y - (i % 3) * 18 - 10, sw = Math.sin(t * 1.5 + i) * 4; x.strokeStyle = '#4f8a55'; x.lineWidth = 4; x.beginPath(); x.moveTo(fx, fy + 44); x.quadraticCurveTo(fx, fy + 20, fx + sw, fy); x.stroke(); ell(fx - 8, fy + 28, 9, 4, '#5f9e60', -.5); for (let k = 0; k < 5; k++) { x.save(); x.translate(fx + sw, fy); x.rotate(R(k * 72) + t * .3); ell(0, -11, 7.5, 12, ['#f2b8c6', '#ffffff', '#f6dd9b', '#c9b6ee'][i % 4]); x.restore(); } circ(fx + sw, fy, 6, '#e9bd5f'); } },
  dog: (p, t) => {
    x.save(); x.translate(p.x, p.y); x.scale(p.s * (p.tilt < 0 ? -1 : 1), p.s); const c = '#c09058', d = '#9a6c3a', pant = Math.sin(t * 12) * 3, drink = p.tilt === 2;
    for (const [l, cc] of [[-52, d], [34, d], [-34, c], [52, c]]) { x.strokeStyle = cc; x.lineWidth = 12; x.lineCap = 'round'; x.beginPath(); x.moveTo(l, -66); x.lineTo(l + 2, -6); x.stroke(); ell(l + 4, -4, 9, 5, mix(cc, '#000000', .2)); }
    x.save(); x.translate(-66, -84); x.rotate(-.7 + Math.sin(t * 7) * .3); x.beginPath(); x.moveTo(0, 0); x.quadraticCurveTo(-20, -10, -34, -30); x.strokeStyle = c; x.lineWidth = 9; x.stroke(); x.restore();
    smooth([[-72, -70], [-60, -98], [0, -100], [60, -98], [74, -72], [40, -54], [-40, -54]], hgrad([[0, d], [.5, c], [1, mix(c, '#ffffff', .15)]], -72, 74));
    x.save(); x.translate(62, -92); x.rotate(drink ? .6 : 0);
    smooth([[-10, 10], [-4, -22], [20, -26], [44, -16], [52, 0], [30, 8]], c); ell(46, -2, 8, 6, '#2a1d15'); ell(12, -22, 9, 18, d, .5); circ(24, -14, 3.5, '#2a1d15'); circ(25, -15, 1, '#fff');
    if (!drink) { ell(40, 12 + pant, 6, 10, '#e07a7a'); }
    x.restore(); x.restore();
  },
  cat: (p, t) => { x.save(); x.translate(p.x, p.y); x.scale(p.s, p.s); const c = '#a3a9b0', d = '#7f868e'; x.strokeStyle = d; x.lineWidth = 9; x.lineCap = 'round'; x.beginPath(); x.moveTo(-40, -20); x.quadraticCurveTo(-84, -30 + Math.sin(t * 3) * 10, -70, -84); x.stroke(); ell(0, -40, 46, 38, hgrad([[0, d], [1, c]], -46, 46)); circ(30, -86, 28, c); blob([[12, -106], [16, -132], [30, -110]], c); blob([[36, -110], [50, -132], [54, -104]], c); blob([[16, -110], [18, -124], [26, -110]], '#e8a0a0'); circ(22, -90, 4, '#2a1d15'); circ(42, -90, 4, '#2a1d15'); ell(32, -80, 3, 2, '#d08080'); x.restore(); },
  cage: (p) => { x.save(); x.translate(p.x, p.y); x.scale(p.s, p.s); x.strokeStyle = '#5b5b5b'; x.lineWidth = 6; for (let i = 0; i <= 6; i++) { x.beginPath(); x.moveTo(-90 + i * 30, 0); x.lineTo(-90 + i * 30, -170); x.stroke(); } rr(-100, -180, 200, 14, 4, '#5b5b5b'); rr(-100, -8, 200, 12, 4, '#5b5b5b'); x.restore(); },
  well: (p) => { x.save(); x.translate(p.x, p.y); x.scale(p.s, p.s); rr(-80, -236, 10, 150, 3, '#6b4a2b'); rr(70, -236, 10, 150, 3, '#6b4a2b'); blob([[-100, -228], [100, -228], [80, -260], [-80, -260]], '#8e3b2e'); rr(-90, -236, 180, 10, 4, '#5a3b20'); x.strokeStyle = '#9a8566'; x.lineWidth = 3; x.beginPath(); x.moveTo(0, -226); x.lineTo(0, -140); x.stroke(); rr(-12, -146, 24, 22, 4, '#7a5230'); rr(-92, -92, 184, 92, 12, hgrad([[0, '#8d7860'], [1, '#bba489']], -92, 92)); for (let r = 0; r < 3; r++) for (let i = 0; i < 4; i++) rr(-88 + i * 45 + (r % 2) * 20, -86 + r * 29, 40, 25, 5, r % 2 ? 'rgba(255,255,255,.1)' : 'rgba(0,0,0,.08)'); ell(0, -92, 92, 18, '#a8927a'); ell(0, -90, 78, 13, vgrad([[0, '#1e3442'], [1, '#3c6a80']], -103, -77)); x.restore(); },
  shoe: (p) => { x.save(); x.translate(p.x, p.y); x.scale(p.s, p.s); blob([[-40, 0], [40, 0], [44, -16], [10, -24], [-10, -60], [-36, -60], [-40, -20]], hgrad([[0, '#5a3d24'], [1, '#86603a']], -40, 44)); ell(-22, -60, 16, 5, '#7cc3e8'); ell(-24, -61, 7, 2, 'rgba(255,255,255,.7)'); x.restore(); },
  village: (p, t) => { x.save(); x.translate(p.x, p.y); x.scale(p.s, p.s); for (const [dx, h, c] of [[-100, 120, '#e3cba4'], [0, 168, '#d9bf96'], [100, 112, '#ead6b2']]) { rr(dx - 48, -h, 96, h, 4, hgrad([[0, mix(c, '#000000', .1)], [1, c]], dx - 48, dx + 48)); rr(dx - 52, -h - 8, 104, 10, 3, mix(c, '#000000', .15)); arch(dx, 0, 28, 52, '#6a4c2c'); arch(dx - 22, -h + 50, 18, 24, '#ffdf96'); arch(dx + 22, -h + 50, 18, 24, '#ffdf96'); } x.restore(); },
  throne: (p) => { x.save(); x.translate(p.x, p.y); x.scale(p.s, p.s); x.save(); x.globalCompositeOperation = 'lighter'; glow(0, -60, 170, '#ffd88a', .14); x.restore(); rr(-134, -116, 32, 108, 14, hgrad([[0, '#a7781f'], [.5, '#f3cf72'], [1, '#b8862a']], -134, -102)); rr(102, -116, 32, 108, 14, hgrad([[0, '#a7781f'], [.5, '#f3cf72'], [1, '#b8862a']], 102, 134)); rr(-122, -64, 244, 52, 18, vgrad([[0, '#3d8a6c'], [1, '#24574a']], -64, -12)); rr(-112, -22, 224, 22, 6, '#1e4a3e'); for (let i = 0; i < 5; i++) circ(-80 + i * 40, -40, 5, C.gold); ell(-60, -70, 36, 14, '#e6d0a8'); ell(60, -70, 36, 14, '#e6d0a8'); x.restore(); },
  cup: (p, t) => { x.save(); x.translate(p.x, p.y); x.scale(p.s, p.s); x.save(); x.globalCompositeOperation = 'lighter'; glow(0, -50, 70, '#ffe6a0', .18); x.restore(); blob([[-28, -74], [28, -74], [16, -28], [-16, -28]], hgrad([[0, 'rgba(210,235,245,.55)'], [.5, 'rgba(255,255,255,.85)'], [1, 'rgba(190,220,235,.55)']], -28, 28)); blob([[-23, -62], [23, -62], [15, -32], [-15, -32]], 'rgba(240,200,120,.6)'); rr(-4, -28, 8, 22, 2, C.gold2); ell(0, -4, 22, 5, C.gold2); ell(0, -74, 28, 7, 'rgba(255,255,255,.9)'); x.restore(); },
  pearls: (p, t) => { for (let i = 0; i < 7; i++) { const a = R(i * 51) + t * .3; const px = p.x + Math.cos(a) * 60 * p.s, py = p.y + Math.sin(a) * 30 * p.s; x.save(); x.globalCompositeOperation = 'lighter'; glow(px, py, 34 * p.s, '#e8e0ff', .25); x.restore(); const g = x.createRadialGradient(px - 5, py - 5, 1, px, py, 15 * p.s); g.addColorStop(0, '#ffffff'); g.addColorStop(.7, '#e8e2f2'); g.addColorStop(1, '#b8b0d0'); x.fillStyle = g; x.beginPath(); x.arc(px, py, 14 * p.s, 0, TAU); x.fill(); } },
  river: (p, t) => { x.save(); x.beginPath(); x.moveTo(-M, p.y); for (let i = -M; i <= W + M; i += 20) x.lineTo(i, p.y + Math.sin(i / 70 + t) * 6); x.lineTo(W + M, p.y + 50); x.lineTo(-M, p.y + 50); x.closePath(); x.fillStyle = vgrad([[0, '#8fd0ec'], [1, '#5aa6cf']], p.y, p.y + 50); x.fill(); x.strokeStyle = 'rgba(255,255,255,.7)'; x.lineWidth = 3; for (let i = 0; i < 7; i++) { const sx = ((i * 140 + t * 50) % (W + 80)) - 40; x.beginPath(); x.moveTo(sx, p.y + 22 + (i % 2) * 10); x.lineTo(sx + 40, p.y + 22 + (i % 2) * 10); x.stroke(); } x.restore(); },
  wool: (p, t) => { for (let i = 0; i < 6; i++) { const q = (t * .15 + i / 6) % 1; cloudShape(p.x + (i - 2.5) * 110, p.y - q * 300 - (i % 2) * 40, .45, '#f3ece0', 'rgba(0,0,0,.08)'); } },
  gate: (p, t) => { x.save(); x.translate(p.x, p.y); x.scale(p.s, p.s); rr(-170, -420, 340, 420, 10, hgrad([[0, mix(p.c || '#c9a46a', '#000000', .2)], [.5, p.c || '#c9a46a'], [1, mix(p.c || '#c9a46a', '#000000', .1)]], -170, 170)); arch(0, 0, 220, 340, '#3a2a14'); const o = Math.min(1, (p.tilt || 0)); const g = x.createLinearGradient(0, -360, 0, 0); g.addColorStop(0, '#fffbe6'); g.addColorStop(1, '#f6d77e'); x.save(); x.globalAlpha *= o; arch(0, 0, 220, 340, g); x.globalCompositeOperation = 'lighter'; glow(0, -150, 260, '#ffe2a0', .35); x.restore(); x.restore(); },
  sarir: (p) => PROPS.throne(p),
  lamp: (p, t) => lantern(p.x, p.y, p.s * 1.4, t),
  boulder: (p) => PROPS.rock(p),
  milk: (p) => { x.save(); x.translate(p.x, p.y); x.scale(p.s, p.s); x.beginPath(); x.ellipse(0, -20, 40, 22, 0, 0, Math.PI); x.fillStyle = '#c9a46a'; x.fill(); ell(0, -20, 40, 10, '#fbf6ec'); x.restore(); },
  herd: (p, t) => { for (let i = 0; i < 4; i++) PROPS.camel({ x: p.x + i * 70, y: p.y - (i % 2) * 10, s: .45 * p.s, tilt: -1 }, t + i); },
  birds: (p, t) => { x.strokeStyle = p.c || '#2a2a2a'; x.lineWidth = 4; x.lineCap = 'round'; for (let i = 0; i < 8; i++) { const bx = ((p.x + i * 95 + t * 60) % (W + 100)) - 50, by = p.y + Math.sin(i * 2) * 50 + Math.sin(t * 2 + i) * 8, f = Math.sin(t * 9 + i) * 10; x.beginPath(); x.moveTo(bx - 18, by - f); x.quadraticCurveTo(bx - 8, by - 6, bx, by); x.quadraticCurveTo(bx + 8, by - 6, bx + 18, by - f); x.stroke(); } },
  sunmoon: (p, t) => { PROPS.sun({ x: p.x - 150, y: p.y, s: .7 }, t); crescent(p.x + 150, p.y, 40); },
});
// عرض ظل الأداة على الأرض (للي واگفة على الأرض)
const SHADOW = { plant: 34, scales: 60, stone: 50, mosque: 190, palm: 40, camel: 90, village: 160, tree: 70, jug: 30, bag: 36, stand: 46, house: 130, well: 100, dog: 70, cat: 46, throne: 140, cup: 24, hourglass: 50, gift: 46, lock: 46, sign: 30, mountain: 220, cart: 100, bread: 44, kaaba: 100, shoe: 40, staff: 20, gate: 180, cave: 300, rock: 130, boulder: 130, plate: 60, book: 50, scroll: 120, shield: 50 };

// ===== الخلفيات (طبقات بعمق) =====
const STAR = Array.from({ length: 160 }, (_, i) => [rnd(i) * (W + 2 * M) - M, rnd(i + 99) * 820, .6 + rnd(i + 3) * 1.6, .6 + rnd(i + 7) * 1.4]);
function stars(t, n, col = '#ffffff', ymax = 820) { x.fillStyle = col; for (let i = 0; i < n; i++) { const s = STAR[i]; if (s[1] > ymax) continue; x.globalAlpha = .3 + .7 * Math.abs(Math.sin(t * s[3] + i)); x.fillRect(s[0] - s[2] / 2, s[1] - s[2] / 2, s[2], s[2]); if (s[2] > 2.0) twinkle(s[0], s[1], s[2] * 2.6, col, .5); } x.globalAlpha = 1; }
function motes(t, n, col, y0 = 400, y1 = 1150, up = 14, sz = 2.2) { x.save(); x.globalCompositeOperation = 'lighter'; for (let i = 0; i < n; i++) { const yy = y1 - ((t * up * (.6 + rnd(i + 5)) + rnd(i + 1) * (y1 - y0)) % (y1 - y0)); const xx = rnd(i + 2) * (W + 80) - 40 + Math.sin(t * .7 + i) * 18; x.globalAlpha = (.25 + .5 * rnd(i + 3)) * Math.sin(clamp((yy - y0) / (y1 - y0)) * Math.PI); circ(xx, yy, sz * (.5 + rnd(i + 4)), col); } x.restore(); }
function hillPath(y, amp, seed, f1 = 140, f2 = 60) { x.beginPath(); x.moveTo(-M, H); for (let i = -M; i <= W + M; i += 10) x.lineTo(i, y - amp * (Math.sin(i / f1 + seed) * .6 + Math.sin(i / f2 + seed * 2) * .2)); x.lineTo(W + M, H); x.closePath(); }
function hills(col, y, amp, seed, f1, f2) { hillPath(y, amp, seed, f1, f2); x.fillStyle = col; x.fill(); }
function dunes(y, amp, seed, light, dark) { // كثبان بخط قمة مضيء وجهة ظل
  const pts = []; for (let i = -M; i <= W + M; i += 8) pts.push([i, y - amp * (Math.sin(i / 170 + seed) * .7 + Math.sin(i / 73 + seed * 3) * .25)]);
  x.beginPath(); x.moveTo(-M, H); pts.forEach(p => x.lineTo(p[0], p[1])); x.lineTo(W + M, H); x.closePath(); x.fillStyle = vgrad([[0, light], [1, dark]], y - amp, y + 260); x.fill();
  x.save(); x.clip(); x.globalAlpha = .18; x.fillStyle = '#5a2e10'; for (let k = 0; k < pts.length - 1; k++) { const s = pts[k + 1][1] - pts[k][1]; if (s > 0) x.fillRect(pts[k][0], pts[k][1], 8.5, 220); } x.restore();
  x.strokeStyle = rgba('#fff1d0', .45); x.lineWidth = 2; x.beginPath(); pts.forEach((p, i) => i ? x.lineTo(p[0], p[1]) : x.moveTo(p[0], p[1])); x.stroke();
}
function skyline(y, col, seed, win) { // مدينة بعيدة: قباب ومآذن
  x.fillStyle = col; x.beginPath(); x.moveTo(-M, H);
  let px = -M; const blocks = [];
  while (px < W + M) { const w = 40 + rnd(px + seed) * 70, h = 30 + rnd(px * 1.3 + seed) * 70; blocks.push([px, w, h]); px += w; }
  x.fill(); blocks.forEach(([bx, w, h], i) => {
    x.fillStyle = col; x.fillRect(bx, y - h, w + 1, H - y + h);
    if (rnd(i + seed) > .55) { x.beginPath(); x.ellipse(bx + w / 2, y - h, w * .38, w * .42, 0, Math.PI, TAU); x.fill(); x.fillRect(bx + w / 2 - 1.5, y - h - w * .42 - 12, 3, 12); }
    if (rnd(i * 3 + seed) > .72) { const mx = bx + w * .85; x.fillRect(mx - 5, y - h - 90, 10, 90); x.fillRect(mx - 8, y - h - 60, 16, 5); x.beginPath(); x.moveTo(mx - 6, y - h - 90); x.lineTo(mx, y - h - 108); x.lineTo(mx + 6, y - h - 90); x.fill(); }
    if (win) { x.fillStyle = win; for (let k = 0; k < 3; k++) if (rnd(i * 7 + k + seed) > .5) arch(bx + 10 + k * (w - 20) / 2.5, y - h + 26 + (k % 2) * 16, 6, 10, win); }
  });
  x.fillRect(-M, y, W + 2 * M, H - y);
}
function tilesFloor(top, c1, c2, line, vp = 360) { x.fillStyle = vgrad([[0, c1], [1, c2]], top, H); x.fillRect(-M, top, W + 2 * M, H - top); x.strokeStyle = line; x.lineWidth = 1.5; for (let i = -14; i < 22; i++) { x.beginPath(); x.moveTo(vp + i * 60, top); x.lineTo(vp + i * 260, H); x.stroke(); } for (let j = 1; j < 8; j++) { const y = top + Math.pow(j / 8, 1.7) * (H - top); x.beginPath(); x.moveTo(-M, y); x.lineTo(W + M, y); x.stroke(); } }
function godrays(cx, cy, n, len, spread, col, a, t, w = 40) { x.save(); x.globalCompositeOperation = 'lighter'; x.translate(cx, cy); for (let i = 0; i < n; i++) { const an = -spread / 2 + spread * (i + .5) / n + Math.sin(t * .25 + i * 1.7) * .02; const aa = a * (.55 + .45 * Math.sin(t * .6 + i * 2.3)); x.save(); x.rotate(an); const g = x.createLinearGradient(0, 0, 0, len); g.addColorStop(0, rgba(col, aa)); g.addColorStop(1, rgba(col, 0)); x.fillStyle = g; const ww = w * (.6 + rnd(i) * .8); x.beginPath(); x.moveTo(-ww * .2, 0); x.lineTo(ww * .2, 0); x.lineTo(ww, len); x.lineTo(-ww, len); x.fill(); x.restore(); } x.restore(); }
function palmSil(px, py, s, col) { x.save(); x.translate(px, py); x.scale(s, s); x.strokeStyle = col; x.lineWidth = 12; x.lineCap = 'round'; x.beginPath(); x.moveTo(0, 0); x.quadraticCurveTo(12, -100, 4, -200); x.stroke(); x.fillStyle = col; for (let i = 0; i < 8; i++) { x.save(); x.translate(4, -200); x.rotate(R(-170 + i * 45)); x.beginPath(); x.moveTo(0, 0); x.quadraticCurveTo(46, -22, 96, 16); x.quadraticCurveTo(46, 2, 0, 6); x.fill(); x.restore(); } x.restore(); }
function fog(t, y, col, a, sp = 8) { x.save(); for (let i = 0; i < 4; i++) { const fx = ((t * sp * (1 + i * .3) + i * 260) % (W + 600)) - 300; const g = x.createRadialGradient(fx, y + i * 30, 0, fx, y + i * 30, 300); g.addColorStop(0, rgba(col, a)); g.addColorStop(1, rgba(col, 0)); x.fillStyle = g; x.save(); x.translate(0, y + i * 30); x.scale(1, .25); x.translate(0, -(y + i * 30)); x.fillRect(fx - 300, y + i * 30 - 300, 600, 600); x.restore(); } x.restore(); }

const BG = {
  day: (t) => {
    L(.04, 'day0', () => { x.fillStyle = vgrad([[0, '#f6e5c6'], [.45, '#fae0b4'], [.8, '#f6cf98'], [1, '#efc086']]); x.fillRect(-M, 0, W + 2 * M, H); glow(540, 640, 420, '#fff2c8', .8); });
    if (!SKYP) A(.04, () => PROPS.sun({ x: 545, y: 655, s: .85 }, t));
    A(.12, () => { for (let i = 0; i < 4; i++) cloudShape(((i * 230 + t * 6) % (W + 300)) - 150, 560 + (i % 2) * 70, .55 + (i % 3) * .1, 'rgba(255,250,240,.75)', 'rgba(230,190,150,.25)'); });
    L(.2, 'day1', () => { skyline(GY - 170, '#ecca9a', 3); x.fillStyle = 'rgba(250,224,180,.35)'; x.fillRect(-M, 0, W + 2 * M, H); });
    L(.45, 'day2', () => { hills('#e3b47c', GY - 95, 34, 1.3); for (const [px, s] of [[40, .7], [640, .85], [700, .6]]) palmSil(px, GY - 92, s, '#cf9e66'); });
    L(1, 'day3', () => { tilesFloor(GY - 40, '#e8cda0', '#d7b083', 'rgba(150,100,50,.12)'); x.fillStyle = 'rgba(255,240,210,.5)'; x.fillRect(-M, GY - 42, W + 2 * M, 3); });
    A(1, () => motes(t, 16, '#fff1c8', 450, 1100, 10));
  },
  night: (t) => {
    L(.03, 'night0', () => { x.fillStyle = vgrad([[0, '#060b22'], [.45, '#0f1b40'], [.82, '#1f3060'], [1, '#2b3c6c']]); x.fillRect(-M, 0, W + 2 * M, H); glow(360, GY - 120, 520, '#4a5c9a', .35); });
    A(.03, () => { stars(t, 110, '#ffffff', GY - 260); if (!SKYP) crescent(578, 590, 38); });
    L(.18, 'night1', () => skyline(GY - 150, '#16234a', 7, 'rgba(255,200,110,.5)'));
    L(.42, 'night2', () => { x.save(); x.translate(160, GY - 60); x.scale(.62, .62); PROPS.mosque({ x: 0, y: 0, s: 1, c: '#13284a' }, 0); x.restore(); hills('#101c3a', GY - 50, 14, 4); });
    L(1, 'night3', () => { tilesFloor(GY - 40, '#1a2548', '#0b122b', 'rgba(140,170,255,.07)'); glow(360, GY + 40, 300, '#7f90d0', .12); });
    A(1, () => motes(t, 10, '#ffcf7a', 600, 1100, 8, 1.8));
  },
  mosque: (t) => {
    L(.04, 'mos0', () => {
      x.fillStyle = vgrad([[0, '#0b2a28'], [.6, '#12403a'], [1, '#0c2e2a']]); x.fillRect(-M, 0, W + 2 * M, H);
      x.strokeStyle = 'rgba(233,189,95,.07)'; x.lineWidth = 1.5; for (let r = 0; r < 9; r++) for (let c = -1; c < 7; c++) { const p = new Path2D(); starPoly(p, c * 120 + (r % 2) * 60, r * 110, 44, 8, 3); x.stroke(p); }
      const mg = vgrad([[0, '#fff3c8'], [1, '#e9b45a']], GY - 520, GY - 40); arch(360, GY - 40, 230, 430, '#0a2422'); arch(360, GY - 46, 196, 400, mg); glow(360, GY - 260, 330, '#ffd27a', .35);
      x.strokeStyle = 'rgba(200,150,60,.5)'; x.lineWidth = 3; x.beginPath(); archPath(x, 360, GY - 46, 160, 360); x.stroke();
    });
    L(.25, 'mos1', () => { for (const cx of [100, 620]) { arch(cx, GY - 30, 150, 380, '#1d5249'); arch(cx, GY - 30, 116, 350, '#0e322e'); glow(cx, GY - 280, 90, '#ffd27a', .1); } });
    A(.3, () => godrays(150, 380, 6, 1100, .5, '#ffe2a0', .1, t, 70));
    A(.5, () => { for (const [lx, ly] of [[200, 560], [520, 560], [360, 500]]) lantern(lx, ly, .95, t + lx); });
    L(.62, 'mos2', () => {
      for (const cx of [-40, 760]) { rr(cx - 60, 0, 120, GY, 0, hgrad([[0, '#0a2522'], [.5, '#164a42'], [1, '#0a2522']], cx - 60, cx + 60)); rr(cx - 72, 520, 144, 22, 6, '#c9a14a'); }
    });
    L(1, 'mos3', () => { x.fillStyle = vgrad([[0, '#6e2230'], [1, '#3e1018']], GY - 40, H); x.fillRect(-M, GY - 40, W + 2 * M, H); x.strokeStyle = 'rgba(233,189,95,.28)'; x.lineWidth = 2; for (let j = 0; j < 5; j++) { const y = GY - 40 + Math.pow(j / 5, 1.5) * 200 + 6; x.beginPath(); x.moveTo(-M, y); x.lineTo(W + M, y); x.stroke(); } glow(360, GY + 20, 320, '#ffcf7a', .18); });
    A(.5, () => motes(t, 22, '#ffe6b0', 380, 1100, 6, 2));
  },
  desert: (t) => {
    L(.03, 'des0', () => { x.fillStyle = vgrad([[0, '#f8e6c2'], [.5, '#f9d39c'], [.85, '#f2b878'], [1, '#e9a868']]); x.fillRect(-M, 0, W + 2 * M, H); glow(190, 700, 460, '#fff0c0', .85); });
    if (!SKYP) A(.03, () => PROPS.sun({ x: 190, y: 705, s: 1 }, t));
    L(.15, 'des1', () => { dunes(GY - 150, 50, 2, '#f0c690', '#e7b07a'); x.fillStyle = 'rgba(250,215,160,.35)'; x.fillRect(-M, 0, W + 2 * M, H); });
    L(.4, 'des2', () => dunes(GY - 80, 46, 5, '#eab070', '#d89558'));
    L(1, 'des3', () => { x.fillStyle = vgrad([[0, '#e2a464'], [1, '#c98a4e']], GY - 40, H); x.fillRect(-M, GY - 40, W + 2 * M, H); x.strokeStyle = 'rgba(255,230,190,.25)'; x.lineWidth = 2; for (let j = 0; j < 9; j++) { x.beginPath(); for (let i = -M; i <= W + M; i += 12) x.lineTo(i, GY - 20 + j * 18 + Math.sin(i / 40 + j) * 3); x.stroke(); } });
    A(1, () => motes(t, 14, '#fff0c8', 700, 1150, 4, 1.6));
  },
  dark: (t) => {
    L(.04, 'dark0', () => { x.fillStyle = vgrad([[0, '#0a0d1c'], [.6, '#161b30'], [1, '#20263c']]); x.fillRect(-M, 0, W + 2 * M, H); });
    A(.04, () => stars(t, 40, '#9aa3c8', 700));
    A(.2, () => { x.save(); x.globalCompositeOperation = 'lighter'; const g = x.createLinearGradient(0, 300, 0, GY); g.addColorStop(0, 'rgba(160,175,230,0)'); g.addColorStop(1, 'rgba(160,175,230,.13)'); x.fillStyle = g; x.beginPath(); x.moveTo(320, 300); x.lineTo(400, 300); x.lineTo(560, GY); x.lineTo(160, GY); x.closePath(); x.fill(); x.restore(); });
    A(.35, () => fog(t, GY - 200, '#6a74a0', .12, 10));
    L(1, 'dark3', () => { x.fillStyle = vgrad([[0, '#1a2033'], [1, '#0b0e1a']], GY - 40, H); x.fillRect(-M, GY - 40, W + 2 * M, H); glow(360, GY + 10, 260, '#8f9ad0', .14); });
  },
  light: (t) => {
    L(.03, 'li0', () => { x.fillStyle = vgrad([[0, '#2a1c10'], [.35, '#6a4a24'], [.75, '#e6c27a'], [1, '#f8e6b8']]); x.fillRect(-M, 0, W + 2 * M, H); glow(360, GY - 260, 640, '#fff4d0', .8); });
    A(.08, () => godrays(360, GY - 300, 14, 900, TAU, '#fff2c8', .09, t, 80));
    L(.35, 'li1', () => { for (let i = 0; i < 5; i++) { x.save(); x.globalAlpha = .9 - Math.abs(i - 2) * .15; PROPS.door({ x: 120 + i * 120, y: GY - 110, s: .6 + (i === 2 ? .15 : 0) }); x.restore(); } });
    L(1, 'li2', () => { x.fillStyle = vgrad([[0, '#f8e8bf'], [1, '#e9cf98']], GY - 50, H); x.fillRect(-M, GY - 50, W + 2 * M, H); for (let i = 0; i < 7; i++) cloudShape(-40 + i * 130, GY - 30 + (i % 2) * 20, .9, '#fff8e6', 'rgba(220,180,110,.3)'); });
    A(1, () => motes(t, 26, '#fff4cc', 300, 1150, 16, 2.4));
  },
  home: (t) => {
    L(.04, 'home0', () => {
      x.fillStyle = vgrad([[0, '#2c1e17'], [.5, '#4a3226'], [1, '#5c4030']]); x.fillRect(-M, 0, W + 2 * M, H);
      x.fillStyle = 'rgba(255,255,255,.025)'; for (let i = 0; i < 400; i++) x.fillRect(rnd(i) * (W + 2 * M) - M, rnd(i + 50) * H, 3, 3);
      const p = new Path2D(); archPath(p, 130, 900, 150, 300); x.save(); x.clip(p); x.fillStyle = vgrad([[0, '#0c1636'], [1, '#2a3c6c']], 560, 900); x.fillRect(40, 520, 200, 400); for (let i = 0; i < 18; i++) circ(60 + rnd(i) * 150, 600 + rnd(i + 3) * 260, 1.4, '#fff'); x.restore(); crescent(150, 640, 18);
      x.strokeStyle = '#a07a50'; x.lineWidth = 10; x.beginPath(); archPath(x, 130, 900, 150, 300); x.stroke(); rr(40, 896, 180, 14, 4, '#8a6644');
      rr(470, 720, 220, 12, 4, '#7a5636'); for (let i = 0; i < 7; i++) rr(486 + i * 26, 650 + (i % 3) * 6, 20, 70 - (i % 3) * 6, 3, ['#2f6b57', '#8e2f2f', '#c9962e', '#3d6e8f'][i % 4]); PROPS.jug({ x: 640, y: 710, s: .6 });
    });
    A(.3, () => { x.save(); x.globalCompositeOperation = 'lighter'; glow(380, 640, 460, '#ffb04a', .28 + Math.sin(t * 7) * .015); x.restore(); lantern(380, 600, 1.2, t); });
    L(1, 'home2', () => { x.fillStyle = vgrad([[0, '#6a4a32'], [1, '#3e2a1c']], GY - 40, H); x.fillRect(-M, GY - 40, W + 2 * M, H); x.strokeStyle = 'rgba(0,0,0,.18)'; x.lineWidth = 2; for (let j = 0; j < 6; j++) { const y = GY - 40 + Math.pow(j / 6, 1.6) * 200; x.beginPath(); x.moveTo(-M, y); x.lineTo(W + M, y); x.stroke(); } x.save(); x.translate(360, GY + 30); x.scale(1.5, 1.5); ell(0, 0, 150, 26, '#7a2430'); x.strokeStyle = C.gold; x.lineWidth = 2.5; x.beginPath(); x.ellipse(0, 0, 132, 19, 0, 0, TAU); x.stroke(); x.strokeStyle = 'rgba(233,189,95,.5)'; x.beginPath(); x.ellipse(0, 0, 100, 13, 0, 0, TAU); x.stroke(); x.restore(); for (const cx of [60, 660]) { ell(cx, GY - 30, 70, 26, '#2f6b57'); ell(cx, GY - 38, 60, 16, '#3a8068'); } });
    A(1, () => motes(t, 12, '#ffd9a0', 500, 1100, 5, 1.8));
  },
  garden: (t) => {
    L(.03, 'gar0', () => { x.fillStyle = vgrad([[0, '#4fa6c8'], [.35, '#a6d9d6'], [.62, '#f3efc8'], [1, '#fbe6b0']]); x.fillRect(-M, 0, W + 2 * M, H); glow(360, 700, 480, '#fff3c4', .7); });
    A(.06, () => godrays(360, 640, 12, 760, TAU, '#fff6d0', .07, t, 50));
    L(.12, 'gar1', () => { x.save(); x.globalAlpha = .55; for (const [px, s2] of [[120, .5], [600, .42]]) { x.save(); x.translate(px, GY - 210); x.scale(s2, s2); PROPS.mosque({ x: 0, y: 0, s: 1, c: '#e9f2e6' }, 0); x.restore(); } x.restore(); hills('#a8d6b4', GY - 200, 46, 2.2, 180, 70); x.fillStyle = 'rgba(236,246,230,.35)'; x.fillRect(-M, 0, W + 2 * M, H); });
    L(.3, 'gar2', () => { hills('#7fbf82', GY - 135, 42, 4, 150, 55); for (let i = 0; i < 7; i++) PROPS.tree({ x: -40 + i * 130, y: GY - 112 + (i % 2) * 12, s: .42 + (i % 3) * .07 }, 0); x.fillStyle = 'rgba(220,240,220,.18)'; x.fillRect(-M, 0, W + 2 * M, H); });
    L(.55, 'gar2b', () => { hills('#5fa864', GY - 72, 22, 6, 120, 50); for (const px of [-30, 760]) PROPS.palm({ x: px, y: GY - 60, s: 1.15 }, 0); });
    A(.7, () => { PROPS.river({ y: GY - 62 }, t); x.save(); x.globalCompositeOperation = 'lighter'; for (let i = 0; i < 12; i++) { x.globalAlpha = .6 * Math.abs(Math.sin(t * 2.2 + i * 1.3)); twinkle(rnd(i) * W, GY - 50 + rnd(i + 2) * 30, 6, '#ffffff'); } x.restore(); });
    L(1, 'gar3', () => { x.fillStyle = vgrad([[0, '#7cbd6c'], [1, '#3f8446']], GY - 18, H); x.fillRect(-M, GY - 18, W + 2 * M, H); x.strokeStyle = 'rgba(30,80,30,.35)'; x.lineWidth = 2; for (let i = 0; i < 110; i++) { const gx = rnd(i) * (W + 2 * M) - M, gy = GY - 14 + rnd(i + 9) * 170; x.beginPath(); x.moveTo(gx, gy); x.quadraticCurveTo(gx + 3, gy - 8, gx + 6, gy - 14); x.stroke(); } });
    A(1, () => { PROPS.flowers({ x: 40, y: GY + 40, s: .6 }, t); PROPS.flowers({ x: 690, y: GY + 50, s: .6 }, t + 2); motes(t, 24, '#fffbe0', 380, 1100, 12, 2.6); });
  },
  market: (t) => {
    BG.day(t);
    L(.6, 'mkt', () => { for (let i = 0; i < 3; i++) { const sx = 110 + i * 250; rr(sx - 92, GY - 260, 184, 220, 6, hgrad([[0, '#c9a77a'], [1, '#e2c69c']], sx - 92, sx + 92)); rr(sx - 80, GY - 150, 160, 110, 4, '#6e4a2a'); for (let k = 0; k < 6; k++) { x.beginPath(); x.moveTo(sx - 106 + k * 35.3, GY - 290); x.lineTo(sx - 70.7 + k * 35.3, GY - 290); x.quadraticCurveTo(sx - 82 + k * 35.3, GY - 240, sx - 88 + k * 35.3, GY - 236); x.closePath(); x.fillStyle = k % 2 ? '#a14a3a' : '#f6ead2'; x.fill(); } for (let k = 0; k < 4; k++) ell(sx - 54 + k * 36, GY - 150, 14, 10, ['#d9534f', '#e9bd5f', '#7cb96e', '#c98a3e'][k]); } });
  },
  dawn: (t) => {
    L(.03, 'dawn0', () => { x.fillStyle = vgrad([[0, '#151c46'], [.4, '#3d3a6e'], [.72, '#c8807a'], [.9, '#f2b67e'], [1, '#f6c98c']]); x.fillRect(-M, 0, W + 2 * M, H); glow(360, GY - 120, 500, '#ffd4a0', .55); });
    A(.03, () => { x.save(); x.globalAlpha = .55; stars(t, 50, '#ffffff', 600); x.restore(); });
    L(.18, 'dawn1', () => { hills('#5a4c7a', GY - 160, 70, 1.4, 200, 80); x.fillStyle = 'rgba(240,170,140,.25)'; x.fillRect(-M, 0, W + 2 * M, H); });
    L(.45, 'dawn2', () => { skyline(GY - 70, '#2e2d55', 5, 'rgba(255,210,140,.5)'); });
    L(1, 'dawn3', () => { tilesFloor(GY - 40, '#2b2c50', '#151634', 'rgba(255,190,150,.08)'); });
    A(1, () => motes(t, 10, '#ffd8b0', 600, 1100, 6, 1.6));
  },
  scroll: (t) => {
    L(.04, 'scr0', () => { x.fillStyle = vgrad([[0, '#0c1734'], [.6, '#101f42'], [1, '#08102a']]); x.fillRect(-M, 0, W + 2 * M, H); glow(360, 820, 520, '#3a5aa0', .3); x.strokeStyle = 'rgba(233,189,95,.08)'; x.lineWidth = 1.5; for (let r = 0; r < 12; r++) for (let c = -1; c < 8; c++) { const p = new Path2D(); starPoly(p, c * 110 + (r % 2) * 55, r * 110, 40, 8, 3); x.stroke(p); } });
    A(.1, () => { stars(t, 40, '#f3d48a', 900); x.save(); x.translate(360, 820); x.rotate(t * .05); x.globalAlpha = .1; for (let i = 0; i < 3; i++) { const p = new Path2D(); starPoly(p, 0, 0, 300 - i * 70, 8, 3); x.strokeStyle = C.gold; x.lineWidth = 2; x.stroke(p); } x.restore(); });
    L(1, 'scr1', () => { x.fillStyle = vgrad([[0, '#0e1a38'], [1, '#060c22']], GY - 40, H); x.fillRect(-M, GY - 40, W + 2 * M, H); glow(360, GY, 300, '#e9bd5f', .12); });
    A(1, () => motes(t, 16, '#f3d48a', 400, 1100, 8, 1.8));
  },
  space: (t) => {
    L(.02, 'sp0', () => { x.fillStyle = vgrad([[0, '#03040c'], [1, '#0d1230']]); x.fillRect(-M, 0, W + 2 * M, H); glow(200, 500, 380, '#5a3a8a', .35); glow(560, 900, 420, '#1f6a8a', .3); glow(420, 650, 260, '#a05a8a', .15); });
    A(.05, () => stars(t, 160, '#ffffff', H));
  },
  sky: (t) => {
    L(.03, 'sky0', () => { x.fillStyle = vgrad([[0, '#86bde2'], [.55, '#cfe6f2'], [1, '#eef5f0']]); x.fillRect(-M, 0, W + 2 * M, H); glow(520, 560, 380, '#ffffff', .6); });
    A(.15, () => { for (let i = 0; i < 5; i++) cloudShape(((i * 190 + t * 9) % (W + 300)) - 150, 540 + (i % 3) * 90, .7 + (i % 2) * .25); });
    L(.35, 'sky1', () => hills('#a8d09c', GY - 110, 50, 1, 180, 70));
    L(.6, 'sky2', () => hills('#8fc184', GY - 60, 30, 3));
    L(1, 'sky3', () => { x.fillStyle = vgrad([[0, '#86ba7c'], [1, '#5f9a58']], GY - 40, H); x.fillRect(-M, GY - 40, W + 2 * M, H); });
  },
  sea: (t) => {
    L(.03, 'sea0', () => { x.fillStyle = vgrad([[0, '#7fb6dc'], [.55, '#cfe5f0'], [.7, '#f4efe0']], 0, H); x.fillRect(-M, 0, W + 2 * M, H); glow(560, 600, 340, '#fff3d0', .7); });
    A(.03, () => { if (!SKYP) PROPS.sun({ x: 560, y: 610, s: .7 }, t); cloudShape(((t * 7) % 900) - 150, 560, .7); cloudShape(((t * 5 + 500) % 900) - 150, 650, .5); });
    A(.2, () => { waves(GY - 190, '#6fa8cc', 4, .6, t, 0); x.save(); x.globalCompositeOperation = 'lighter'; for (let i = 0; i < 14; i++) { const gx = 470 + Math.sin(i * 3.1) * 120, gy = GY - 180 + i * 6; x.globalAlpha = .35 * Math.abs(Math.sin(t * 2 + i)); x.fillStyle = '#fff6d8'; x.fillRect(gx, gy, 18 + rnd(i) * 30, 2); } x.restore(); });
    A(.5, () => waves(GY - 130, '#4f8fbb', 10, 1.2, t, 0, 'rgba(255,255,255,.35)'));
    A(.75, () => waves(GY - 70, '#3a78a6', 14, 1.6, t, 2, 'rgba(255,255,255,.45)'));
    A(1, () => waves(GY - 10, '#2a6290', 18, 2, t, 4, 'rgba(255,255,255,.55)'));
  },
  storm: (t) => {
    const fl = ((t * .9) % 4.3) < .12 ? 1 : ((t * .9 + 1.7) % 6.1) < .08 ? .7 : 0;
    L(.03, 'st0', () => { x.fillStyle = vgrad([[0, '#141b26'], [.6, '#2e3a4c'], [1, '#46566a']]); x.fillRect(-M, 0, W + 2 * M, H); });
    A(.1, () => { for (let i = 0; i < 6; i++) cloudShape(((i * 170 + t * 14) % (W + 300)) - 150, 470 + (i % 3) * 60, 1.2, '#3a4658', 'rgba(10,15,25,.4)'); if (fl) { x.save(); x.globalAlpha = fl; x.strokeStyle = '#eef4ff'; x.lineWidth = 4; x.shadowColor = '#cfe0ff'; x.shadowBlur = 20; x.beginPath(); x.moveTo(520, 520); x.lineTo(490, 640); x.lineTo(530, 660); x.lineTo(480, 820); x.stroke(); x.restore(); } });
    A(.4, () => waves(GY - 200, '#2a465c', 38, 1.5, t, 0, 'rgba(220,235,245,.25)'));
    A(.75, () => waves(GY - 110, '#1d3a50', 46, 2, t, 3, 'rgba(230,240,250,.4)'));
    A(1, () => { x.strokeStyle = 'rgba(200,220,240,.38)'; x.lineWidth = 2; x.beginPath(); for (let i = 0; i < 70; i++) { const rx = (rnd(i) * (W + 100) + t * 160) % (W + 100) - 50, ry = (rnd(i + 5) * 1100 + t * 1100) % 1100 + 200; x.moveTo(rx, ry); x.lineTo(rx - 7, ry + 26); } x.stroke(); if (fl) { x.fillStyle = `rgba(220,230,255,${.25 * fl})`; x.fillRect(-M, 0, W + 2 * M, H); } });
  },
  deep: (t) => {
    L(.03, 'dp0', () => { x.fillStyle = vgrad([[0, '#2a6d96'], [.35, '#16466c'], [.8, '#0a2440'], [1, '#05121f']]); x.fillRect(-M, 0, W + 2 * M, H); });
    A(.1, () => godrays(360, 120, 9, 1100, .9, '#b8e6ff', .1, t, 60));
    A(.5, () => { x.save(); x.globalCompositeOperation = 'lighter'; for (let i = 0; i < 26; i++) { const q = (t * .1 + rnd(i)) % 1; x.globalAlpha = .45 * Math.sin(q * Math.PI); circ(rnd(i + 3) * W + Math.sin(t + i) * 10, H - q * 1000, 2 + rnd(i) * 6, 'rgba(180,225,255,.6)'); } x.restore(); });
    L(1, 'dp1', () => { hills('#082034', GY - 20, 30, 2); hills('#061828', GY + 20, 20, 5); });
  },
  hell: (t) => {
    L(.03, 'hell0', () => { x.fillStyle = vgrad([[0, '#0e0505'], [.6, '#2a0b07'], [1, '#4a1508']]); x.fillRect(-M, 0, W + 2 * M, H); glow(360, GY, 520, '#ff5a1a', .35); });
    A(.3, () => fog(t, GY - 260, '#3a1208', .4, 12));
    A(1, () => { for (let i = 0; i < 7; i++) PROPS.fire({ x: 50 + i * 105, y: GY + 20, s: 1.2 + Math.sin(t * 2 + i) * .15 }, t + i); motes(t, 40, '#ff9a4a', 300, 1150, 40, 2.2); });
  },
  valley: (t) => {
    BG.day(t);
    L(.5, 'val', () => { blob([[-M, GY - 40], [-M, 560], [60, 600], [130, 760], [200, 900], [180, GY - 40]], '#c99a62'); blob([[W + M, GY - 40], [W + M, 600], [640, 640], [580, 800], [520, GY - 40]], '#bf8f58'); blob([[-M, 560], [60, 600], [90, 680], [-M, 700]], 'rgba(255,240,210,.2)'); });
    L(1, 'val2', () => { x.fillStyle = vgrad([[0, '#c99a62'], [1, '#a87a46']], GY - 30, H); x.fillRect(-M, GY - 30, W + 2 * M, H); for (let i = 0; i < 8; i++) ell(60 + i * 90, GY + 20 - (i % 2) * 20, 26, 12, '#7a5a3c'); });
  },
  cavein: (t) => {
    L(.03, 'cv0', () => { x.fillStyle = vgrad([[0, '#140f0b'], [1, '#2a2018']]); x.fillRect(-M, 0, W + 2 * M, H); glow(360, 480, 460, '#ffcf8a', .3); const p = new Path2D(); archPath(p, 360, 640, 220, 200); x.fillStyle = vgrad([[0, '#ffe8b0'], [1, '#f2b866']], 380, 640); x.fill(p); });
    A(.2, () => godrays(360, 520, 5, 900, .6, '#ffe2a0', .12, t, 70));
    L(.45, 'cv1', () => { smooth([[-M, 0], [W + M, 0], [W + M, 1300], [560, 1300], [600, 900], [540, 620], [470, 470], [360, 420], [240, 470], [170, 620], [120, 900], [160, 1300], [-M, 1300]], vgrad([[0, '#3a2c20'], [1, '#241a12']])); });
    L(1, 'cv2', () => { x.fillStyle = vgrad([[0, '#3a2d22'], [1, '#1c150f']], GY - 40, H); x.fillRect(-M, GY - 40, W + 2 * M, H); glow(360, GY - 20, 260, '#ffcf8a', .14); });
    A(.5, () => motes(t, 20, '#ffe2b0', 420, 1100, 5, 1.8));
  },
};
// خلفيات فاتحة: النص يصير غامق فوگها
const LIGHT = { day: 1, desert: 1, market: 1, sky: 1, sea: 1, garden: 1, valley: 1 };

// ===== المؤثرات =====
const FX = {
  coins: (f, p, t) => { const [a, b] = f.arg.split('>').map(Number); for (let i = 0; i < 3; i++) { const q = eIO((p * 1.4 - i * .15)); if (q <= 0 || q >= 1) continue; const cx = lerp(a, b, q), cy = 760 - Math.sin(q * Math.PI) * 160; x.save(); x.globalCompositeOperation = 'lighter'; glow(cx, cy, 40, '#ffd070', .3); x.restore(); coin(cx, cy, 18); } },
  hearts: (f, p, t) => { for (let i = 0; i < 7; i++) { const q = (p * 1.6 + i * .14) % 1; const a = Math.sin(q * Math.PI); x.globalAlpha = a; const hx = f.x + Math.sin(i * 2 + q * 6) * 70, hy = f.y - q * 300, s = .8 + rnd(i) * .6; heartShape(hx, hy, s * (.8 + .2 * eOut(q * 4)), i % 3 ? '#e0605a' : '#f08a7a'); x.globalAlpha = a * .6; heartShape(hx - 4 * s, hy - 5 * s, s * .3, '#ffffff'); } x.globalAlpha = 1; },
  sparkle: (f, p, t) => { for (let i = 0; i < 12; i++) { const q = (t * .6 + rnd(i)) % 1; const a = Math.sin(q * Math.PI); twinkle(f.x + (rnd(i + 1) - .5) * 280, f.y + (rnd(i + 2) - .5) * 220 - q * 50, (7 + rnd(i) * 9) * (.6 + .4 * a), '#ffe9a8', a); } },
  rays: (f, p, t) => { x.save(); x.globalAlpha = Math.min(1, p * 3); f.y > 600 ? godrays(f.x, f.y, 16, 700, TAU, '#ffe9b0', .12, t, 50) : godrays(f.x || 360, f.y || 380, 9, 1000, 1.2, '#ffe9b0', .16, t, 70); x.restore(); },
  glow: (f, p, t) => { const r = 170 + Math.sin(t * 2.4) * 12; x.save(); x.globalCompositeOperation = 'lighter'; glow(f.x, f.y, r, '#ffd890', .45 * Math.min(1, p * 4)); x.restore(); },
  x: (f, p) => { const k = eOut(p * 3), d = eOut(p * 3 - .3); x.save(); x.translate(f.x, f.y); x.scale(.8 + .2 * k, .8 + .2 * k); x.globalAlpha *= k; circ(0, 0, 62, 'rgba(120,20,20,.25)'); x.strokeStyle = '#e04848'; x.lineWidth = 15; x.lineCap = 'round'; x.beginPath(); x.moveTo(-40, -40); x.lineTo(-40 + 80 * clamp(d * 2), -40 + 80 * clamp(d * 2)); if (d > .5) { x.moveTo(40, -40); x.lineTo(40 - 80 * clamp(d * 2 - 1), -40 + 80 * clamp(d * 2 - 1)); } x.stroke(); x.restore(); },
  check: (f, p) => { const k = back(p * 3), d = eOut(p * 3 - .25); x.save(); x.translate(f.x, f.y); x.scale(k, k); x.save(); x.globalCompositeOperation = 'lighter'; glow(0, 0, 110, '#7ee09a', .3); x.restore(); circ(0, 0, 58, '#3f9a5c'); x.strokeStyle = 'rgba(255,255,255,.35)'; x.lineWidth = 3; x.beginPath(); x.arc(0, 0, 66 + d * 12, 0, TAU); x.globalAlpha *= 1 - d; x.stroke(); x.globalAlpha = 1; x.strokeStyle = '#fff'; x.lineWidth = 13; x.lineCap = 'round'; x.lineJoin = 'round'; x.setLineDash([90 * d, 200]); x.beginPath(); x.moveTo(-26, 2); x.lineTo(-6, 22); x.lineTo(28, -20); x.stroke(); x.setLineDash([]); x.restore(); },
  drops: (f, p, t) => { for (let i = 0; i < 6; i++) { const q = (t * 1.6 + i / 6) % 1; x.globalAlpha = 1 - q; ell(f.x + (rnd(i) - .5) * 20, f.y + q * 120, 5, 9, '#86c9ec'); } x.globalAlpha = 1; },
  num: (f, p) => { const k = back(p * 3); x.save(); x.translate(f.x, f.y); x.scale(k, k); x.rotate((1 - k) * .5); star8(0, 0, 66, C.gold2); star8(0, 0, 60, C.gold); circ(0, 0, 44, '#fff3d0'); x.fillStyle = C.navy; x.font = '700 52px UI'; x.textAlign = 'center'; x.textBaseline = 'middle'; x.fillText(f.arg, 0, 4); x.restore(); },
  grow: (f, p) => { const k = eIO(p * 1.2); for (let i = 0; i < 10; i++) { const q = Math.min(1, k * 10 - i); if (q <= 0) break; coin(f.x + ((i % 5) - 2) * 44, f.y - Math.floor(i / 5) * 40, 18 * back(q)); } },
  fade: () => { },
  shake: () => { },
  fall: (f, p, t) => { for (let i = 0; i < 18; i++) { const q = (t * .5 + rnd(i)) % 1; x.globalAlpha = 1 - q; const sx = rnd(i + 1) * W, sy = 160 + q * 900; x.strokeStyle = '#ffe39a'; x.lineWidth = 3; x.beginPath(); x.moveTo(sx, sy); x.lineTo(sx - 30, sy - 60); x.stroke(); twinkle(sx, sy, 9, '#ffe39a'); } x.globalAlpha = 1; },
  crack: (f, p) => { const k = eIO(p * 2); x.save(); x.strokeStyle = '#fff6d6'; x.lineWidth = 6; x.shadowColor = '#fff1b0'; x.shadowBlur = 20; x.beginPath(); const pts = [[360, 380], [330, 470], [390, 560], [340, 660], [380, 760]]; x.moveTo(pts[0][0], pts[0][1]); for (let i = 1; i < pts.length * k; i++) x.lineTo(pts[i][0], pts[i][1]); x.stroke(); x.restore(); },
  moths: (f, p, t) => { for (let i = 0; i < 26; i++) { const mx = (rnd(i) * W + Math.sin(t * 1.5 + i) * 60), my = 450 + rnd(i + 9) * 550 + Math.cos(t * 2 + i) * 40, fl = Math.abs(Math.sin(t * 12 + i)); x.save(); x.translate(mx, my); x.fillStyle = ['#f2d27a', '#e8e0d0', '#c9b79a'][i % 3]; x.beginPath(); x.ellipse(-8, 0, 10 * fl + 2, 7, -.4, 0, TAU); x.ellipse(8, 0, 10 * fl + 2, 7, .4, 0, TAU); x.fill(); x.restore(); } },
  rain: (f, p, t) => { x.strokeStyle = 'rgba(180,210,240,.55)'; x.lineWidth = 2; x.beginPath(); for (let i = 0; i < 60; i++) { const rx = (rnd(i) * W + t * 120) % W, ry = (rnd(i + 5) * 900 + t * 1100) % 1100 + 200; x.moveTo(rx, ry); x.lineTo(rx - 6, ry + 24); } x.stroke(); },
  bow: (f, p, t) => { const k = Math.sin(t * 1.6) * .5 + .5; x.save(); x.globalAlpha = .5 + .5 * k; FX.glow(f, 1, t); x.restore(); },
  span: (f, p) => { const k = eIO(p * 2); x.strokeStyle = C.gold; x.lineWidth = 6; x.setLineDash([14, 10]); x.beginPath(); x.moveTo(f.x - 200, f.y); x.lineTo(f.x - 200 + 400 * k, f.y); x.stroke(); x.setLineDash([]); },
};

// ===== تجهيز المشاهد =====
function parseActor(s) { // "man@250:give<" أو "man#b@250>480:walk"
  const m = s.match(/^(\w+)(?:#(\w+))?@(-?\d+)(?:>(-?\d+))?(?:,(\d+))?:(\w+)(<)?(?:\*([\d.]+))?$/);
  if (!m) throw new Error('actor ' + s);
  return { type: m[1], id: m[1] + (m[2] || ''), x: +m[3], to: m[4] != null ? +m[4] : null, y: m[5] ? +m[5] : GY, pose: m[6], dir: m[7] ? -1 : 1, s: m[8] ? +m[8] : 1 };
}
function parseProp(s) { // "coin@360,700*1.2" ، و ^ بالبداية يعني گدّام الأشخاص
  const front = s[0] === '^'; if (front) s = s.slice(1);
  const m = s.match(/^(\w+)@(-?\d+),(-?\d+)(?:\*([\d.]+))?(?:=([\w#.-]+))?$/);
  if (!m) throw new Error('prop ' + s);
  const o = { type: m[1], x: +m[2], y: +m[3] + (GY - 1085), s: m[4] ? +m[4] : 1, k: s, front }; if (m[5]) { if (m[5][0] === '#') o.c = m[5]; else o.tilt = +m[5]; } return o;
}
function parseFx(s) { // "coins:250>480" "hearts@360,700" "num:3@200,600"
  const m = s.match(/^(\w+)(?::([^@]+))?(?:@(-?\d+),(-?\d+))?$/); if (!m) throw new Error('fx ' + s);
  return { type: m[1], arg: m[2], x: m[3] ? +m[3] : 360, y: (m[4] ? +m[4] : 700) + (GY - 1085) };
}
const shots = D.beats.map(b => ({ t: b.t, bg: BG[b.bg] ? b.bg : 'night', actors: (b.a || []).map(parseActor), props: (b.p || []).map(parseProp), fx: (b.f || []).map(parseFx) }));
const seedOf = id => [...id].reduce((s, c) => s + c.charCodeAt(0), 0);
const KEYSEED = seedOf(D.title || '') + (D.n || 0);
// حركة كاميرا لكل لقطة: تقريب، تحريك يمين/يسار، إبعاد، صعود. اللقطات بنفس المكان تكمل من وين وگفت الكاميرا
const MOVES = [{ z: .06 }, { x: -24 }, { x: 24 }, { z: -.05 }, { y: -14, z: .03 }];
shots.forEach((S, i) => {
  const P = shots[i - 1], end = (shots[i + 1] ? shots[i + 1].t : D.total) - S.t;
  const m = MOVES[(Math.floor(rnd(i * 7.3 + KEYSEED) * 997) + i) % MOVES.length], k = clamp(end / 3.5, .35, 1);
  let st;
  if (P && P.bg === S.bg) st = P.cam1; else st = { x: -(m.x || 0) / 2 * k, y: -(m.y || 0) / 2 * k, z: (m.z || 0) < 0 ? .06 : .01 };
  let e = { x: clamp(st.x + (m.x || 0) * k, -28, 28), y: clamp(st.y + (m.y || 0) * k, -18, 18), z: clamp(st.z + (m.z || 0) * k, 0, .1) };
  if (Math.abs(e.x - st.x) + Math.abs(e.y - st.y) + Math.abs(e.z - st.z) * 300 < 6) e = { x: clamp(st.x - (m.x || 0) * k, -28, 28), y: st.y, z: clamp(st.z - (m.z || .04) * k, 0, .1) };
  S.cam0 = st; S.cam1 = e; S.dur = Math.max(.6, end);
  S.tr = P && P.bg !== S.bg ? SE.tr[(i + KEYSEED) % SE.tr.length] : null;
});
function camOf(S, t) { const q = sine((t - S.t) / S.dur); return { x: lerp(S.cam0.x, S.cam1.x, q), y: lerp(S.cam0.y, S.cam1.y, q), z: lerp(S.cam0.z, S.cam1.z, q) }; }
function poseMix(a, b, p) {
  const A = POSE[a] || POSE.stand, B = POSE[b] || POSE.stand, o = {};
  for (const k of ['tor', 'head', 'low']) o[k] = lerp(A[k] || 0, B[k] || 0, p);
  o.la = [lerp(A.la[0], B.la[0], p), lerp(A.la[1], B.la[1], p)]; o.ra = [lerp(A.ra[0], B.ra[0], p), lerp(A.ra[1], B.ra[1], p)];
  o.l1 = clamp(lerp(A.legs === 1 ? 1 : 0, B.legs === 1 ? 1 : 0, p)); o.l2 = clamp(lerp(A.legs === 2 ? 1 : 0, B.legs === 2 ? 1 : 0, p));
  for (const k of ['finger', 'palm', 'book', 'box', 'walk', 'fist']) o[k] = p < .5 ? (A[k] || 0) : (B[k] || 0);
  o.name = p < .5 ? a : b;
  return o;
}
const TD = .8; // مدة الانتقال بين مكانين
function scene(i, t) { // ترسم لقطة كاملة بكاميرتها
  const S = shots[i], P = shots[i - 1], sameBg = P && P.bg === S.bg, dt = t - S.t;
  CAM = camOf(S, t); SKYP = S.props.some(q => q.type === 'sun' || q.type === 'sunmoon' || q.type === 'moon');
  const sh = S.fx.some(f => f.type === 'shake') ? Math.sin(t * 38) * 7 * Math.max(0, 1 - dt / 4) : 0;
  CAM.x += sh; CAM.y += sh * .5;
  BG[S.bg](t);
  x.save(); applyCam(1); drawThings(S, t, dt, !sameBg, sameBg ? P : null); x.restore();
}
function drawShot(i, t) {
  const S = shots[i], dt = t - S.t;
  if (!S.tr || dt >= TD) { scene(i, t); return; }
  const p = dt / TD, e = eIO(p);
  if (S.tr === 'slide') {
    const dir = AR ? -1 : 1;
    x.save(); x.translate(-dir * W * e * .35, 0); scene(i - 1, t); x.restore();
    x.save(); x.translate(dir * W * (1 - e), 0); x.shadowColor = 'rgba(0,0,0,.4)'; scene(i, t); x.restore();
    x.save(); x.fillStyle = 'rgba(0,0,0,.35)'; x.globalAlpha = Math.sin(p * Math.PI) * .6; x.fillRect(dir > 0 ? W * (1 - e) - 30 : W * e - 0, 0, 30, H); x.restore();
    return;
  }
  if (S.tr === 'flash') {
    scene(i - 1, t); x.save(); x.globalAlpha = eIO(p * 1.4 - .2); scene(i, t); x.restore();
    x.save(); x.globalCompositeOperation = 'lighter'; x.globalAlpha = Math.sin(p * Math.PI) * .55; x.fillStyle = rgba('#fff0c8', 1); x.fillRect(0, 0, W, H); x.restore(); return;
  }
  scene(i - 1, t);
  const path = new Path2D();
  if (S.tr === 'iris') path.arc(360, 820, 1150 * e + 1, 0, TAU);
  else archPath(path, 360, H + 60, 40 + 1500 * e, 60 + 1900 * e);
  x.save(); x.clip(path); scene(i, t); x.restore();
  x.save(); x.globalAlpha = 1 - p; x.strokeStyle = SE.acc; x.lineWidth = 5; x.shadowColor = SE.acc; x.shadowBlur = 24; x.stroke(path); x.restore();
}
function drawThings(S, t, dt, fresh, P) {
  // الأدوات
  // نفس الأداة باللقطة السابقة (نفس النوع) تتحرك لمكانها الجديد بدل ما تختفي وتطلع
  const mo = new Map();
  if (P) { const used = new Set(); S.props.forEach(q => { if (P.props.some(r => r.k === q.k)) return; const r = P.props.find(r => r.type === q.type && !used.has(r) && !S.props.some(z => z.k === r.k)); if (r) { used.add(r); mo.set(q, r); } }); }
  const moved = new Set(mo.values());
  const old = P ? P.props.filter(q => !S.props.some(r => r.k === q.k) && !moved.has(q)) : [];
  old.forEach(q => { if (dt < .35) { const k = 1 - eIn(dt / .35); x.save(); x.globalAlpha = k; x.translate(q.x, q.y); x.scale(.85 + .15 * k, .85 + .15 * k); x.translate(-q.x, -q.y); PROPS[q.type] && PROPS[q.type](q, t); x.restore(); } });
  const drawProps = front => S.props.forEach((q0, j) => {
    let q = q0;
    if (!!q.front !== front || !PROPS[q.type]) return;
    const fr = mo.get(q0);
    if (fr) { const m = eIO(dt / .9); q = Object.assign({}, q0, { x: lerp(fr.x, q0.x, m), y: lerp(fr.y, q0.y, m), s: lerp(fr.s, q0.s, m), tilt: q0.tilt != null && fr.tilt != null ? lerp(fr.tilt, q0.tilt, m) : q0.tilt }); }
    const had = fr || (P && P.props.some(r => r.k === q.k));
    const st = (fresh ? .25 : .12) + j * .1, k = had ? 1 : back((dt - st) / .6), al = had ? 1 : eOut((dt - st) / .4);
    if (k <= 0) return;
    if (SHADOW[q.type] && q.y > GY - 70 && !front) { x.save(); x.globalAlpha = .2 * al; x.translate(q.x, q.y + 2); x.scale(1, .16); const r = SHADOW[q.type] * q.s; const g = x.createRadialGradient(0, 0, 0, 0, 0, r); g.addColorStop(0, 'rgba(25,15,8,1)'); g.addColorStop(1, 'rgba(25,15,8,0)'); x.fillStyle = g; x.fillRect(-r, -r, 2 * r, 2 * r); x.restore(); }
    x.save(); x.translate(q.x, q.y + (1 - al) * 26); x.scale(k, k); x.translate(-q.x, -q.y); x.globalAlpha = al; PROPS[q.type](q, t); x.restore();
  });
  drawProps(false);
  // الأشخاص
  const out = P ? P.actors.filter(q => !S.actors.some(r => r.id === q.id)) : [];
  out.forEach(q => { if (dt < .4) person(actorAt(q, q, 99, t, 1 - eIn(dt / .4)), t); });
  S.actors.forEach((a, j) => {
    const pa = P && P.actors.find(r => r.id === a.id);
    const ap = pa ? 1 : eOut((dt - (fresh ? .2 : 0) - j * .12) / .5);
    if (ap <= 0) return;
    const A = actorAt(a, pa, dt, t, ap); if (!pa) A.y += (1 - ap) * 30;
    person(A, t);
  });
  drawProps(true);
  // المؤثرات
  S.fx.forEach(f => { if (!FX[f.type]) return; const p = Math.max(0, dt - .4) / 2.2; if (dt > .4) { x.save(); FX[f.type](f, Math.min(p, 1), t); x.restore(); } });
}
function actorAt(a, pa, dt, t, al) {
  // يمشي من مكانه القديم للجديد، والوقفة تتحول بنعومة ويا ارتداد خفيف
  const start = pa ? (pa.to != null ? pa.to : pa.x) : a.x, end = a.to != null ? a.to : a.x;
  const dist = Math.abs(end - start), moves = dist > 4, dur = moves ? dist / 230 : 0;
  const walking = moves && dt < dur, q = moves ? sine(dt / dur) * .15 + clamp(dt / dur) * .85 : 1;
  const prev = pa ? pa.pose : a.pose;
  let ps;
  if (walking) ps = poseMix(prev, 'walk', eOut(dt / .3));
  else if (moves) ps = poseMix('walk', a.pose, spr((dt - dur) / .7));
  else ps = poseMix(prev, a.pose, spr(dt / .7));
  const dir = walking ? (end > start ? 1 : -1) : a.dir;
  return { type: a.type, x: lerp(start, end, q), y: a.y, dir, s: a.s, pose: ps, wph: (start + (end - start) * q) / 13, al, seed: seedOf(a.id) };
}

// ===== النص =====
const segW = D.segs.map(s => s.split(/ +/));
const nA = s => strip(s).replace(/[أإآٱ]/g, 'ا').replace(/ى/g, 'ي').replace(/ة/g, 'ه');
const HL = (D.hl || []).map(nA);
function isHL(w) { const sw = nA(w).replace(/[^ء-يa-zA-Z]/g, '').toLowerCase(); return sw && HL.some(h => sw.includes(h.toLowerCase())); }
const AYA = /^﴿([^﴾]+)﴾$/;
const FONT = AR ? (D.quran ? ['400', 'Amiri', 60, 1.62] : ['700', 'UI', 54, 1.6]) : ['700', 'Inter', 48, 1.32];
const LAYOUT = [];
function layoutSeg(i) {
  if (LAYOUT[i]) return LAYOUT[i];
  const words = segW[i]; let fs = FONT[2], res;
  for (; fs >= 30; fs -= 2) {
    const font = `${FONT[0]} ${fs}px ${FONT[1]}`; x.font = font; x.direction = AR ? 'rtl' : 'ltr';
    const sp = x.measureText(' ').width * (AR ? 1.15 : 1), maxW = 620, lines = [[]]; let lw = 0;
    words.forEach(w => { const ww = AYA.test(w) ? fs * 1.05 : x.measureText(w).width; if (lw + ww > maxW && lines[lines.length - 1].length) { lines.push([]); lw = 0; } lines[lines.length - 1].push([w, ww]); lw += ww + sp; });
    const lh = fs * FONT[3]; res = { lines, sp, fs, font, lh };
    if (lines.length <= (AR ? 3 : 4) && lines.length * lh <= 330) break;
  }
  return LAYOUT[i] = res;
}
let curLight = 0;
function ayaMark(cx, cy, r, num, col, a) {
  x.save(); x.globalAlpha = a; x.translate(cx, cy);
  const p = new Path2D(); starPoly(p, 0, 0, r, 8, 3); x.strokeStyle = col; x.lineWidth = 2; x.stroke(p);
  x.beginPath(); x.arc(0, 0, r * .62, 0, TAU); x.stroke(); x.fillStyle = rgba(curLight > .5 ? '#ffffff' : '#000000', .15); x.fill();
  x.fillStyle = col; x.font = `700 ${Math.round(r * .78)}px Amiri`; x.textAlign = 'center'; x.textBaseline = 'middle'; x.direction = 'rtl'; x.fillText(num, 0, r * .08); x.restore();
}
function drawText(t) {
  let i = -1; D.times.forEach((tm, k) => { if (t >= tm[0] - .3) i = k; });
  if (i < 0) return;
  const tm = D.times[i], words = segW[i], Lh = layoutSeg(i);
  const nl = Lh.lines.length, blockH = nl * Lh.lh, cy = 300, top = cy - blockH / 2 + Lh.lh * .68;
  const segDur = tm[1] - tm[0], fadeOut = i < D.times.length - 1 ? D.times[i + 1][0] - .3 : D.total - 3.1;
  const outA = 1 - eIn((t - (fadeOut - .3)) / .3), outY = -eIn((t - (fadeOut - .3)) / .3) * 14;
  const lk = curLight, ink = mix('#f8f0de', '#1c2830', lk), hc = mix(SE.acc, SE.accL, lk);
  // خلفية ناعمة ورا النص حتى ينقرا فوق أي مشهد
  const inA = eOut((t - tm[0] + .3) / .4) * outA;
  if (inA > 0) {
    const maxW = Math.max(...Lh.lines.map(l => l.reduce((s, w) => s + w[1], 0) + Lh.sp * (l.length - 1)));
    x.save(); x.translate(360, cy); x.scale((maxW / 2 + 130) / 100, (blockH / 2 + 90) / 100);
    const g = x.createRadialGradient(0, 0, 0, 0, 0, 100); const sc = lk > .5 ? '#fff8ec' : '#050a18'; g.addColorStop(0, rgba(sc, (lk > .5 ? .5 : .34) * inA)); g.addColorStop(.55, rgba(sc, (lk > .5 ? .3 : .2) * inA)); g.addColorStop(1, rgba(sc, 0)); x.fillStyle = g; x.fillRect(-100, -100, 200, 200); x.restore();
  }
  let n = 0;
  Lh.lines.forEach((line, li) => {
    const lw = line.reduce((s, w) => s + w[1], 0) + Lh.sp * (line.length - 1);
    let cx = AR ? (W + lw) / 2 : (W - lw) / 2;
    line.forEach(([w, ww]) => {
      const appear = tm[0] - .25 + (n / Math.max(1, words.length)) * segDur * .85; n++;
      const q = eOut((t - appear) / .5);
      if (q > 0 && outA > 0) {
        const px = AR ? cx - ww : cx, py = top + li * Lh.lh + (1 - q) * 22 + outY, hl = isHL(w), am = w.match(AYA);
        x.save(); x.globalAlpha = q * outA;
        if (am) ayaMark(px + ww / 2, py - Lh.fs * .3, Lh.fs * .52, am[1], hc, q * outA);
        else {
          x.font = Lh.font; x.textBaseline = 'alphabetic'; x.direction = AR ? 'rtl' : 'ltr'; x.textAlign = 'left';
          const fresh = clamp(1 - (t - appear) / .9);
          if (hl) {
            const u = eOut((t - appear - .25) / .6);
            x.save(); x.globalCompositeOperation = lk > .5 ? 'source-over' : 'lighter'; x.translate(px + ww / 2, py - Lh.fs * .3); x.scale((ww / 2 + 26) / 50, (Lh.fs * .6) / 50); const g = x.createRadialGradient(0, 0, 0, 0, 0, 50); g.addColorStop(0, rgba(lk > .5 ? '#ffe6a8' : SE.acc, .28 * u)); g.addColorStop(1, rgba(SE.acc, 0)); x.fillStyle = g; x.fillRect(-50, -50, 100, 100); x.restore();
            const uy = py + Lh.fs * (AR ? .42 : .2), uw = ww * u;
            x.fillStyle = hc; x.beginPath(); x.roundRect(AR ? px + ww - uw : px, uy, uw, Math.max(3, Lh.fs * .07), 3); x.fill();
          }
          x.fillStyle = hl ? hc : ink;
          if (lk < .5) { x.shadowColor = 'rgba(0,0,0,.55)'; x.shadowBlur = 14; x.shadowOffsetY = 2; }
          if (fresh > 0 && lk < .5) { x.shadowColor = rgba(SE.acc, .7 * fresh); x.shadowBlur = 22; }
          x.fillText(w, px, py);
        }
        x.restore();
      }
      cx += AR ? -(ww + Lh.sp) : (ww + Lh.sp);
    });
  });
}
function header(t) {
  const lk = curLight, a = eOut((t - 2.2) / .6);
  if (a <= 0) return;
  x.save(); x.globalAlpha = a; x.translate(0, (1 - a) * -16);
  const bx = AR ? W - 210 : 30, by = 34;
  x.fillStyle = lk > .5 ? 'rgba(24,60,52,.9)' : 'rgba(255,255,255,.1)'; x.beginPath(); x.roundRect(bx, by, 180, 54, 27); x.fill();
  x.strokeStyle = lk > .5 ? 'rgba(233,189,95,.5)' : 'rgba(233,189,95,.45)'; x.lineWidth = 1.5; x.stroke();
  if (icon.complete) x.drawImage(icon, AR ? bx + 130 : bx + 6, by + 5, 44, 44);
  x.fillStyle = SE.acc; x.font = AR ? '700 27px UI' : '700 25px Inter'; x.direction = AR ? 'rtl' : 'ltr'; x.textAlign = AR ? 'right' : 'left'; x.textBaseline = 'middle';
  x.fillText(AR ? 'أوّاب' : 'Awwab', AR ? bx + 122 : bx + 58, by + 28);
  x.fillStyle = lk > .5 ? 'rgba(30,40,46,.75)' : 'rgba(240,236,224,.8)'; x.font = AR ? '500 21px UI' : '500 18px Inter'; x.textAlign = AR ? 'left' : 'right';
  x.fillText(D.label, AR ? 30 : W - 30, by + 28, 400); x.restore();
}
function footer(t) {
  const lk = curLight, y = H - 70, a = eOut((t - 2.4) / .6) * (1 - eIn((t - (D.total - 3.1)) / .4));
  if (a <= 0) return;
  x.save(); x.globalAlpha = a;
  x.fillStyle = lk > .5 ? 'rgba(30,40,46,.72)' : 'rgba(240,236,224,.78)'; x.font = AR ? '500 21px UI' : '500 18px Inter'; x.direction = AR ? 'rtl' : 'ltr'; x.textAlign = 'center'; x.textBaseline = 'alphabetic';
  if (lk < .5) { x.shadowColor = 'rgba(0,0,0,.6)'; x.shadowBlur = 8; }
  x.fillText(D.src, W / 2, y, W - 80); x.shadowBlur = 0;
  const bw = W - 80, pr = clamp(t / D.total), by = H - 34;
  rr(40, by, bw, 4, 2, lk > .5 ? 'rgba(30,40,46,.14)' : 'rgba(255,255,255,.16)');
  const g = hgrad([[0, mix(SE.acc, '#ffffff', .2)], [1, SE.acc]], 40, 40 + bw); const px = AR ? 40 + bw * (1 - pr) : 40, pw = bw * pr;
  rr(px, by, pw, 4, 2, lk > .5 ? SE.accL : g); const hx = AR ? px : px + pw; x.save(); x.globalCompositeOperation = lk > .5 ? 'source-over' : 'lighter'; glow(hx, by + 2, 14, SE.acc, .7); x.restore(); circ(hx, by + 2, 4, lk > .5 ? SE.accL : '#fff3d0');
  x.restore();
}
// ===== المقدمة والخاتمة =====
function rosette(cx, cy, r, prog, col, lw) { // نجمة ثمانية تنرسم بالتدريج
  const parts = [[r, 8, 3], [r * .72, 8, 2], [r * .5, 16, 5]];
  parts.forEach(([rr2, n, k], j) => {
    const p = new Path2D(); starPoly(p, cx, cy, rr2, n, k, j === 1 ? Math.PI / 8 : 0);
    const len = n * 2 * rr2 * Math.sin(Math.PI * k / n) + 10, q = clamp(prog * 1.5 - j * .25);
    if (q <= 0) return; x.setLineDash([len * q, len]); x.strokeStyle = col; x.lineWidth = lw; x.stroke(p);
  });
  const q = clamp(prog * 1.3); x.setLineDash([]); x.beginPath(); x.arc(cx, cy, r * 1.08, -Math.PI / 2, -Math.PI / 2 + TAU * q); x.lineWidth = lw * .7; x.stroke();
  x.beginPath(); x.arc(cx, cy, r * 1.16, Math.PI / 2, Math.PI / 2 + TAU * q); x.globalAlpha *= .5; x.stroke(); x.globalAlpha *= 2;
}
function brandBg(t) {
  const c = bake('brand', () => { const g = x.createRadialGradient(360, 560, 40, 360, 640, 900); g.addColorStop(0, mix(SE.deep[0], '#ffffff', .06)); g.addColorStop(.5, SE.deep[0]); g.addColorStop(1, SE.deep[1]); x.fillStyle = g; x.fillRect(-M, 0, W + 2 * M, H); x.strokeStyle = rgba(SE.acc, .06); x.lineWidth = 1.2; for (let r = -1; r < 13; r++) for (let c2 = -1; c2 < 8; c2++) { const p = new Path2D(); starPoly(p, c2 * 110 + (r % 2) * 55, r * 110, 42, 8, 3); x.stroke(p); } });
  x.drawImage(c, -M + Math.sin(t * .3) * 6, 0); stars(t, 50, '#fff6dc', H);
}
function brand(t, k, title) { // المشهد المشترك للمقدمة والخاتمة. k = تقدّم الرسم
  brandBg(t);
  x.save(); x.globalCompositeOperation = 'lighter'; glow(360, 520, 360, SE.acc, .22 * eOut(k * 1.5)); x.restore();
  x.save(); x.translate(360, 520); x.rotate(t * .06); rosette(0, 0, 190, k, rgba(SE.acc, .85), 2.5); x.restore();
  const ik = spr(clamp((k - .05) * 1.6)) * .3 + .7;
  if (icon.complete) { x.save(); x.translate(360, 520); x.scale(ik, ik); x.shadowColor = rgba(SE.acc, .6); x.shadowBlur = 40; x.drawImage(icon, -78, -78, 156, 156); x.restore(); }
}
function intro(t) {
  if (t >= 2.65) return;
  const out = clamp((t - 2.0) / .62);
  x.save();
  if (out > 0) { const p = new Path2D(); p.rect(0, 0, W, H); archPath(p, 360, H + 60, 40 + 1500 * eIO(out), 60 + 1900 * eIO(out)); x.clip(p, 'evenodd'); }
  brand(t, clamp(.5 + t / 2), 1);
  // العنوان كلمة كلمة
  const ws = D.title.split(' '); let fs = AR ? 62 : 56; const ff = AR ? 'UI' : 'Inter';
  x.font = `700 ${fs}px ${ff}`; x.direction = AR ? 'rtl' : 'ltr'; while (x.measureText(D.title).width > 620 && fs > 30) { fs -= 2; x.font = `700 ${fs}px ${ff}`; }
  const sp = x.measureText(' ').width, wl = ws.map(w => x.measureText(w).width), tw = wl.reduce((a, b) => a + b, 0) + sp * (ws.length - 1);
  let cx = AR ? (W + tw) / 2 : (W - tw) / 2;
  ws.forEach((w, j) => { const q = eOut((t - .45 - j * .1) / .55); x.save(); x.globalAlpha = q; x.fillStyle = '#fbf3df'; x.textAlign = 'left'; x.textBaseline = 'alphabetic'; x.shadowColor = 'rgba(0,0,0,.5)'; x.shadowBlur = 16; x.fillText(w, AR ? cx - wl[j] : cx, 790 + (1 - q) * 26); x.restore(); cx += AR ? -(wl[j] + sp) : (wl[j] + sp); });
  const lq = eOut((t - .9) / .6); x.globalAlpha = lq; x.fillStyle = SE.acc; x.font = AR ? '500 27px UI' : '600 22px Inter'; x.textAlign = 'center'; if (!AR) x.letterSpacing = '3px';
  x.fillText(AR ? D.label : D.label.toUpperCase(), 360, 850); x.letterSpacing = '0px';
  x.fillStyle = rgba(SE.acc, .7); x.fillRect(360 - 60 * lq, 878, 120 * lq, 2);
  x.restore();
  if (out > 0 && out < 1) { const p = new Path2D(); archPath(p, 360, H + 60, 40 + 1500 * eIO(out), 60 + 1900 * eIO(out)); x.save(); x.globalAlpha = 1 - out; x.strokeStyle = SE.acc; x.lineWidth = 5; x.shadowColor = SE.acc; x.shadowBlur = 26; x.stroke(p); x.restore(); }
}
function outro(t) {
  const s = D.total - 3.0; if (t < s) return; const q = clamp((t - s) / .7), k = t - s;
  const p = new Path2D(); p.arc(360, 560, 1200 * eIO(q) + 1, 0, TAU);
  x.save(); x.clip(p); brand(t, clamp((k - .2) / 1.4), 0);
  const a = eOut((k - .7) / .6); x.globalAlpha = a; x.fillStyle = '#fbf3df'; x.textAlign = 'center'; x.font = AR ? '700 64px UI' : '700 60px Inter'; x.direction = AR ? 'rtl' : 'ltr'; x.shadowColor = 'rgba(0,0,0,.5)'; x.shadowBlur = 16; x.fillText(AR ? 'أوّاب' : 'Awwab', 360, 800 + (1 - a) * 20);
  const b = eOut((k - 1.0) / .6); x.globalAlpha = b; x.fillStyle = SE.acc; x.font = AR ? '500 30px UI' : '500 27px Inter'; x.fillText(AR ? 'طريق العودة إلى الله' : 'The way back to Allah', 360, 858 + (1 - b) * 14);
  x.restore();
  if (q < 1) { x.save(); x.globalAlpha = 1 - q; x.strokeStyle = SE.acc; x.lineWidth = 5; x.shadowColor = SE.acc; x.shadowBlur = 26; x.stroke(p); x.restore(); }
}
// ===== اللمسة الأخيرة: تظليل الأطراف، لون السلسلة، حبيبات الفلم =====
function finish(t) {
  const v = bake('vig', () => { const g = x.createRadialGradient(360, 700, 260, 360, 640, 860); g.addColorStop(0, 'rgba(0,0,0,0)'); g.addColorStop(.7, 'rgba(10,6,4,.18)'); g.addColorStop(1, 'rgba(10,6,4,.55)'); x.fillStyle = g; x.fillRect(0, 0, W, H); }, W, H, 0, 0);
  x.drawImage(v, 0, 0);
  x.save(); x.globalCompositeOperation = 'soft-light'; x.globalAlpha = SE.ta * 3; x.fillStyle = vgrad([[0, SE.tint], [1, '#ffd9a0']]); x.fillRect(0, 0, W, H); x.restore();
}
const GRAIN = [0, 1, 2].map(k => bake('grain' + k, () => { const id = x.createImageData(360, 640), d = id.data; for (let i = 0; i < d.length; i += 4) { const v = rnd(i * .37 + k * 9973 + 1); d[i] = d[i + 1] = d[i + 2] = v > .5 ? 255 : 0; d[i + 3] = Math.abs(v - .5) * 34; } x.putImageData(id, 0, 0); }, 360, 640, 0, 0));
function grain(t) { x.save(); x.globalAlpha = .8; x.drawImage(GRAIN[Math.floor(t * 12) % 3], 0, 0, W, H); x.restore(); }

window.R = function (t) {
  x.setTransform(1, 0, 0, 1, 0, 0); x.globalAlpha = 1; x.globalCompositeOperation = 'source-over'; x.clearRect(0, 0, W, H);
  let i = 0; shots.forEach((s, k) => { if (t >= s.t) i = k; });
  const S = shots[i], P = shots[i - 1];
  // فاتح/غامق للنص: يتبدل بنعومة ويا الانتقال
  const L1 = LIGHT[S.bg] ? 1 : 0, L0 = P ? (LIGHT[P.bg] ? 1 : 0) : L1;
  curLight = lerp(L0, L1, eIO((t - S.t) / TD));
  drawShot(i, t); finish(t);
  header(t); drawText(t); footer(t); intro(t); outro(t); grain(t);
};
})();
