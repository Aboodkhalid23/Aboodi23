// محرك موشن گرافيك أوّاب: يرسم كل شي بالكود (شخصيات، أماكن، أدوات، مؤثرات) على canvas
// الصفحة تستدعي window.R(t) لكل إطار. البيانات بـ window.D: {lang,n,segs,times,total,beats,hl,label,src}
// قاعدة شرعية: ما نرسم نبي ولا صحابي ولا ملَك. الشخصيات بس "مسلم عادي" يطبق معنى الحديث
(function () {
const W = 720, H = 1280, GY = 1085, SC_TOP = 470, SC_BOT = 1150;
const cv = document.getElementById('c'), x = cv.getContext('2d');
const D = window.D, AR = D.lang === 'ar';
const ease = p => p < 0 ? 0 : p > 1 ? 1 : p < .5 ? 2 * p * p : 1 - Math.pow(-2 * p + 2, 2) / 2;
const back = p => { p = Math.min(1, Math.max(0, p)); const c = 1.7; return 1 + (c + 1) * Math.pow(p - 1, 3) + c * Math.pow(p - 1, 2); };
const lerp = (a, b, p) => a + (b - a) * p;
const rnd = s => { const v = Math.sin(s * 127.1) * 43758.5453; return v - Math.floor(v); };
const strip = s => s.replace(/[ً-ٰٟـ]/g, '');
const R = (a) => a * Math.PI / 180;
const icon = new Image(); icon.src = D.icon || 'icon-192.png';

// ===== الألوان =====
const C = { gold: '#e9bd5f', gold2: '#c9962e', ink: '#f3ecd8', navy: '#0b1026', teal: '#1f4d44', green: '#2f6b57', cream: '#f4ead8', sand: '#e6d3b3', brown: '#7a5a3c', rose: '#b98b8b' };
const PEOPLE = {
  man: { th: '#f6f3ec', sh: '#d8d1c2', sk: '#e0a878', bd: '#3b2a20', cap: '#ffffff' },
  man2: { th: '#2f6b57', sh: '#24574a', sk: '#c98e5e', bd: '#2a1d15', cap: '#ffffff' },
  poor: { th: '#8a7b66', sh: '#6d604f', sk: '#c48f63', bd: '#8d8d8d', cap: '#a89a84', patch: '#6a5c4a' },
  elder: { th: '#ebe5d6', sh: '#cfc6b3', sk: '#dba57a', bd: '#f1f1f1', cap: '#ffffff', cane: 1 },
  child: { th: '#f6f3ec', sh: '#d8d1c2', sk: '#e7b386', bd: null, cap: '#ffffff', s: .64 },
  boy2: { th: '#3d6e8f', sh: '#2f5872', sk: '#dca577', bd: null, cap: '#ffffff', s: .64 },
  woman: { th: '#9c7088', sh: '#7f5a6e', sk: '#e3b08a', hij: '#5f4458', w: 1 },
  woman2: { th: '#b39b6e', sh: '#977f55', sk: '#d9a27a', hij: '#6d5a3a', w: 1 },
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
  sujud: { tor: 118, la: [-35, 30], ra: [-28, 30], legs: 2, low: 1 },
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

// ===== رسم الأشخاص =====
function rot(px, py, a) { const c = Math.cos(a), s = Math.sin(a); return [px * c - py * s, px * s + py * c]; }
function blob(pts, fill) { x.beginPath(); pts.forEach((p, i) => i ? x.lineTo(p[0], p[1]) : x.moveTo(p[0], p[1])); x.closePath(); x.fillStyle = fill; x.fill(); }
function circ(cx, cy, r, f) { x.beginPath(); x.arc(cx, cy, r, 0, 7); x.fillStyle = f; x.fill(); }
function rr(px, py, w, h, r, f) { x.beginPath(); x.roundRect(px, py, w, h, r); x.fillStyle = f; x.fill(); }
function limb(ax, ay, a1, a2, L1, L2, w, col, tor) {
  // الزوايا من الأسفل، والموجب لگدّام
  const t1 = R(a1) + tor, t2 = t1 + R(a2);
  const ex = ax + Math.sin(t1) * L1, ey = ay + Math.cos(t1) * L1;
  const hx = ex + Math.sin(t2) * L2, hy = ey + Math.cos(t2) * L2;
  x.lineCap = 'round'; x.lineJoin = 'round'; x.strokeStyle = col; x.lineWidth = w;
  x.beginPath(); x.moveTo(ax, ay); x.lineTo(ex, ey); x.lineTo(hx, hy); x.stroke();
  return [hx, hy, t2];
}
function person(a, t) {
  const P = PEOPLE[a.type] || PEOPLE.man, p = a.pose, s = (a.s || 1) * (P.s || 1) * 1.32;
  x.save(); x.translate(a.x, a.y); x.scale(s * a.dir, s);
  const breathe = Math.sin(t * 2.2 + a.seed) * 1.6;
  // ظل
  x.save(); x.globalAlpha = .18 * a.al; x.beginPath(); x.ellipse(0, 2, p.legs ? 70 : 52, 9, 0, 0, 7); x.fillStyle = '#000'; x.fill(); x.restore();
  x.globalAlpha = a.al;
  const walk = p.walk ? Math.sin(a.wph) : 0;
  let hipY = lerp(lerp(-135, -50, p.l1), -66, p.l2), hipX = lerp(0, -18, p.l2);
  // الجزء الأسفل
  if (p.l1 < .5 && p.l2 < .5) {
    const k = 1 - Math.max(p.l1, p.l2) * 2;
    const f1 = walk * 16, f2 = -walk * 16;
    rr(-30 + f1 - 4, -9, 34, 11, 6, '#3a2e26'); rr(-6 + f2 + 6, -9, 34, 11, 6, '#4a3b30');
    blob([[-33, hipY], [33, hipY], [44 + walk * 4, -7], [-44 + walk * 4, -7]], P.th);
    blob([[-33, hipY], [-12, hipY], [-22, -7], [-44 + walk * 4, -7]], P.sh);
    if (P.patch) rr(10, -60, 18, 16, 3, P.patch);
    x.globalAlpha = a.al;
  } else if (p.l1 >= p.l2) {
    rr(-62, -48, 136, 48, 24, P.th); rr(-62, -48, 50, 48, 22, P.sh); rr(40, -16, 30, 14, 7, '#3a2e26');
  } else {
    blob([[-48, -66], [16, -66], [50, -10], [50, 0], [-52, 0], [-56, -24]], P.th);
    blob([[-48, -66], [-20, -66], [-30, 0], [-52, 0], [-56, -24]], P.sh); rr(-70, -12, 26, 12, 6, '#3a2e26');
  }
  if (P.cane) { x.strokeStyle = '#6b4a2b'; x.lineWidth = 7; x.lineCap = 'round'; x.beginPath(); x.moveTo(78, -4); x.lineTo(70, -122); x.quadraticCurveTo(66, -140, 52, -136); x.stroke(); }
  // الجذع والرأس
  const tor = R(p.tor) + R(breathe * .15);
  const hip = [hipX, hipY + breathe * .3];
  const sh = (dx, dy) => { const r = rot(dx, dy, tor); return [hip[0] + r[0], hip[1] + r[1]]; };
  const S1 = sh(-6, -96), S2 = sh(8, -96);
  // ذراع بعيدة
  const armC = P.sh, L1 = 50, L2 = 46;
  let h1 = limb(S1[0], S1[1], p.la[0], p.la[1], L1, L2, 21, armC, tor + (p.walk ? -R(walk * 20) : 0));
  circ(h1[0], h1[1], 9.5, P.sk);
  // جسم
  x.save(); x.translate(hip[0], hip[1]); x.rotate(tor);
  x.beginPath(); x.moveTo(-35, 4); x.lineTo(-34, -88); x.quadraticCurveTo(-32, -106, -10, -108); x.lineTo(14, -108); x.quadraticCurveTo(34, -106, 35, -88); x.lineTo(36, 4); x.closePath(); x.fillStyle = P.th; x.fill();
  blob([[-35, 4], [-34, -88], [-26, -104], [-14, -106], [-14, 4]], P.sh);
  if (!P.w) { x.strokeStyle = P.sh; x.lineWidth = 3; x.beginPath(); x.moveTo(10, -104); x.lineTo(10, -60); x.stroke(); }
  // الرأس
  x.translate(4, -138); x.rotate(R(p.head || 0) + Math.sin(t * 1.3 + a.seed) * .02);
  if (P.w) {
    circ(0, 2, 38, P.hij); blob([[-36, 6], [36, 6], [44, 58], [-44, 58]], P.hij);
    x.beginPath(); x.ellipse(9, 2, 22, 26, 0, 0, 7); x.fillStyle = P.sk; x.fill();
  } else {
    circ(0, 0, 31, P.sk); circ(-24, 4, 7, P.sk);
    if (P.bd) { x.beginPath(); x.moveTo(-26, 4); x.quadraticCurveTo(-22, 46, 12, 42); x.quadraticCurveTo(36, 34, 31, 6); x.quadraticCurveTo(14, 14, -4, 12); x.closePath(); x.fillStyle = P.bd; x.fill(); }
    x.beginPath(); x.arc(0, -6, 31.5, Math.PI, 0); x.lineTo(31.5, -4); x.lineTo(-31.5, -4); x.closePath(); x.fillStyle = P.cap; x.fill();
    x.fillStyle = 'rgba(0,0,0,.06)'; x.fillRect(-31, -10, 63, 6);
    const blink = (t * 1.0 + a.seed) % 4 < .12 ? .15 : 1;
    x.save(); x.translate(15, -2); x.scale(1, blink); circ(0, 0, 3.6, '#2a1d15'); x.restore();
    x.strokeStyle = '#7a4a30'; x.lineWidth = 2.6; x.beginPath(); x.arc(17, 12, 6, .2, 1.4); x.stroke();
    x.strokeStyle = '#2a1d15'; x.lineWidth = 2.4; x.beginPath(); x.moveTo(9, -10); x.lineTo(21, -11); x.stroke();
  }
  x.restore();
  // كتاب، صندوق
  if (p.book > .5) { const bx = lerp(h1[0], S2[0] + Math.sin(tor) * 60, .5) + 30, by = h1[1] - 8; book(bx, by, .8); }
  if (p.box > .5) { rr(-50, -330, 100, 64, 8, '#b98a52'); rr(-50, -305, 100, 8, 2, '#8e6638'); }
  // ذراع قريبة
  const h2 = limb(S2[0], S2[1], p.ra[0], p.ra[1], L1, L2, 22, P.th, tor + (p.walk ? R(walk * 20) : 0));
  circ(h2[0], h2[1], 10, P.sk);
  if (p.finger > .5) { x.strokeStyle = P.sk; x.lineWidth = 6; x.lineCap = 'round'; x.beginPath(); x.moveTo(h2[0], h2[1]); const fa = p.finger > 1.5 ? R(90) : h2[2]; x.lineTo(h2[0] + Math.sin(fa) * 16, h2[1] + Math.cos(fa) * 16); x.stroke(); }
  x.restore();
  return { hx: a.x + h2[0] * s * a.dir, hy: a.y + h2[1] * s, top: a.y - 175 * s, s };
}

// ===== الأدوات =====
function book(px, py, s = 1, open = 1) {
  x.save(); x.translate(px, py); x.scale(s, s);
  blob([[-46, -6], [0, 4], [46, -6], [46, 22], [0, 32], [-46, 22]], '#1f5a48');
  blob([[-42, -10], [-2, 0], [-2, 26], [-42, 16]], '#fbf3e1'); blob([[42, -10], [2, 0], [2, 26], [42, 16]], '#f3e7cf');
  x.strokeStyle = 'rgba(120,90,50,.35)'; x.lineWidth = 2; for (let i = 0; i < 3; i++) { x.beginPath(); x.moveTo(-36, -2 + i * 7); x.lineTo(-8, 5 + i * 7); x.stroke(); x.beginPath(); x.moveTo(8, 5 + i * 7); x.lineTo(36, -2 + i * 7); x.stroke(); }
  x.restore();
}
function coin(px, py, r = 22) {
  circ(px, py + 3, r, '#a5761f'); circ(px, py, r, C.gold); circ(px, py, r * .72, '#f4d27f');
  x.strokeStyle = '#c9962e'; x.lineWidth = 2; x.beginPath(); x.arc(px, py, r * .55, 0, 7); x.stroke();
  x.fillStyle = 'rgba(255,255,255,.6)'; x.beginPath(); x.ellipse(px - r * .35, py - r * .4, r * .18, r * .1, -.6, 0, 7); x.fill();
}
function star8(px, py, r, f) { x.save(); x.translate(px, py); for (let k = 0; k < 2; k++) { x.rotate(R(45 * k)); x.fillStyle = f; x.fillRect(-r * .7, -r * .7, r * 1.4, r * 1.4); } x.restore(); }
function heartShape(px, py, s, f) { x.save(); x.translate(px, py); x.scale(s, s); x.beginPath(); x.moveTo(0, 12); x.bezierCurveTo(-26, -6, -14, -30, 0, -16); x.bezierCurveTo(14, -30, 26, -6, 0, 12); x.fillStyle = f; x.fill(); x.restore(); }
function arch(px, py, w, h, f) { x.beginPath(); x.moveTo(px - w / 2, py); x.lineTo(px - w / 2, py - h + w / 2); x.quadraticCurveTo(px - w / 2, py - h, px, py - h - w * .25); x.quadraticCurveTo(px + w / 2, py - h, px + w / 2, py - h + w / 2); x.lineTo(px + w / 2, py); x.closePath(); x.fillStyle = f; x.fill(); }
function lantern(px, py, s = 1, t = 0) {
  x.save(); x.translate(px, py); x.rotate(Math.sin(t * 1.5) * .05); x.scale(s, s);
  x.strokeStyle = '#8a6a2a'; x.lineWidth = 2; x.beginPath(); x.moveTo(0, -60); x.lineTo(0, -26); x.stroke();
  const g = x.createRadialGradient(0, 0, 2, 0, 0, 60); g.addColorStop(0, 'rgba(255,210,120,.55)'); g.addColorStop(1, 'rgba(255,210,120,0)'); x.fillStyle = g; x.beginPath(); x.arc(0, 0, 60, 0, 7); x.fill();
  blob([[-12, -26], [12, -26], [16, 18], [-16, 18]], '#b8862c'); blob([[-8, -18], [8, -18], [10, 12], [-10, 12]], '#ffe2a0');
  blob([[-16, 18], [16, 18], [0, 30]], '#8a6a2a'); x.restore();
}
const PROPS = {
  coin: (p) => coin(p.x, p.y, 22 * p.s),
  coins: (p) => { for (let i = 0; i < 6; i++) coin(p.x - 30 + (i % 3) * 30 + (i > 2 ? 15 : 0), p.y - (i > 2 ? 22 : 0), 17 * p.s); },
  bag: (p) => { x.save(); x.translate(p.x, p.y); x.scale(p.s, p.s); blob([[-34, 0], [34, 0], [26, -50], [12, -62], [-12, -62], [-26, -50]], '#9a6b3c'); rr(-14, -70, 28, 12, 5, '#7a5230'); coin(0, -30, 13); x.restore(); },
  book: (p) => book(p.x, p.y, p.s),
  stand: (p) => { x.save(); x.translate(p.x, p.y); x.scale(p.s, p.s); x.strokeStyle = '#7a5230'; x.lineWidth = 9; x.beginPath(); x.moveTo(-40, 0); x.lineTo(40, -60); x.moveTo(40, 0); x.lineTo(-40, -60); x.stroke(); book(0, -78, 1.05); x.restore(); },
  house: (p) => { x.save(); x.translate(p.x, p.y); x.scale(p.s, p.s); rr(-120, -180, 240, 180, 6, '#e8d3b0'); blob([[-135, -175], [135, -175], [120, -205], [-120, -205]], '#c9a77a'); arch(-55, 0, 60, 120, '#7a5a3c'); arch(55, -60, 50, 70, '#f6dd9b'); x.strokeStyle = '#c9a77a'; x.lineWidth = 4; x.beginPath(); x.moveTo(55, -60); x.lineTo(55, -125); x.stroke(); x.restore(); },
  mosque: (p) => { x.save(); x.translate(p.x, p.y); x.scale(p.s, p.s); const f = p.c || '#1d4a40'; rr(-140, -150, 280, 150, 4, f); x.beginPath(); x.arc(0, -150, 80, Math.PI, 0); x.fillStyle = f; x.fill(); rr(-4, -258, 8, 30, 3, C.gold); x.save(); x.translate(0, -268); x.beginPath(); x.arc(0, 0, 9, R(40), R(320)); x.strokeStyle = C.gold; x.lineWidth = 4; x.stroke(); x.restore(); rr(150, -300, 34, 300, 4, f); rr(144, -310, 46, 14, 4, f); x.beginPath(); x.moveTo(146, -310); x.lineTo(167, -350); x.lineTo(188, -310); x.fillStyle = f; x.fill(); for (let i = -1; i <= 1; i++) arch(i * 70, 0, 40, i ? 70 : 100, '#f2cf7c'); x.restore(); },
  tap: (p) => { x.save(); x.translate(p.x, p.y); x.scale(p.s, p.s); rr(-20, -260, 40, 260, 4, '#1f4d44'); rr(-12, -180, 34, 12, 6, '#c8c8c8'); rr(16, -180, 8, 22, 3, '#c8c8c8'); x.restore(); },
  palm: (p) => { x.save(); x.translate(p.x, p.y); x.scale(p.s, p.s); x.strokeStyle = '#8a6a43'; x.lineWidth = 16; x.lineCap = 'round'; x.beginPath(); x.moveTo(0, 0); x.quadraticCurveTo(14, -100, 4, -200); x.stroke(); for (let i = 0; i < 6; i++) { x.save(); x.translate(4, -200); x.rotate(R(-150 + i * 60)); x.beginPath(); x.ellipse(50, 0, 56, 13, .2, 0, 7); x.fillStyle = i % 2 ? '#3f7d4f' : '#4f9460'; x.fill(); x.restore(); } x.restore(); },
  plant: (p) => { x.save(); x.translate(p.x, p.y); x.scale(p.s, p.s); blob([[-24, 0], [24, 0], [30, -40], [-30, -40]], '#b9714a'); for (let i = 0; i < 5; i++) { x.save(); x.translate(0, -40); x.rotate(R(-60 + i * 30)); x.beginPath(); x.ellipse(0, -30, 10, 30, 0, 0, 7); x.fillStyle = '#4f8a55'; x.fill(); x.restore(); } x.restore(); },
  lantern: (p, t) => lantern(p.x, p.y, p.s, t),
  kaaba: (p) => { x.save(); x.translate(p.x, p.y); x.scale(p.s, p.s); rr(-90, -170, 180, 170, 4, '#141414'); rr(-90, -138, 180, 18, 0, C.gold); rr(30, -100, 34, 100, 3, '#3a2c10'); x.restore(); },
  scales: (p, t) => { x.save(); x.translate(p.x, p.y); x.scale(p.s, p.s); const a = Math.sin(t * 1.2) * .06 + (p.tilt || 0); rr(-6, -170, 12, 170, 4, C.gold2); rr(-40, -8, 80, 10, 4, C.gold2); x.translate(0, -165); x.rotate(a); rr(-110, -5, 220, 10, 4, C.gold); for (const sx of [-100, 100]) { x.strokeStyle = C.gold2; x.lineWidth = 2; x.beginPath(); x.moveTo(sx, 0); x.lineTo(sx - 30, 70); x.moveTo(sx, 0); x.lineTo(sx + 30, 70); x.stroke(); x.beginPath(); x.ellipse(sx, 72, 40, 10, 0, 0, Math.PI); x.fillStyle = C.gold; x.fill(); } x.restore(); },
  heart: (p, t) => heartShape(p.x, p.y + Math.sin(t * 3) * 4, 2.6 * p.s * (1 + Math.sin(t * 6) * .04), p.c || '#d9534f'),
  sun: (p, t) => { const g = x.createRadialGradient(p.x, p.y, 10, p.x, p.y, 140 * p.s); g.addColorStop(0, 'rgba(255,220,130,.9)'); g.addColorStop(.35, 'rgba(255,200,100,.35)'); g.addColorStop(1, 'rgba(255,200,100,0)'); x.fillStyle = g; x.beginPath(); x.arc(p.x, p.y, 140 * p.s, 0, 7); x.fill(); circ(p.x, p.y, 46 * p.s, '#ffd27a'); },
  moon: (p) => { circ(p.x, p.y, 40 * p.s, '#f6e3a6'); circ(p.x + 16 * p.s, p.y - 10 * p.s, 36 * p.s, p.bgc || '#152048'); },
  cloud: (p, t) => { const dx = Math.sin(t * .3 + p.x) * 12; x.save(); x.globalAlpha *= .9; for (const [a, b, r] of [[-50, 0, 34], [0, -18, 44], [50, 0, 34], [0, 8, 34]]) circ(p.x + dx + a * p.s, p.y + b * p.s, r * p.s, p.c || '#ffffff'); x.restore(); },
  door: (p, t) => { x.save(); x.translate(p.x, p.y); x.scale(p.s, p.s); const g = x.createLinearGradient(0, -300, 0, 0); g.addColorStop(0, '#fff6d6'); g.addColorStop(1, '#f2c96a'); arch(0, 0, 120, 260, '#6b4a1f'); arch(0, -8, 100, 240, g); x.restore(); },
  plate: (p) => { x.save(); x.translate(p.x, p.y); x.scale(p.s, p.s); x.beginPath(); x.ellipse(0, 0, 60, 16, 0, 0, 7); x.fillStyle = '#d9c4a0'; x.fill(); for (let i = 0; i < 3; i++) { x.beginPath(); x.ellipse(-26 + i * 26, -12, 22, 13, 0, 0, 7); x.fillStyle = '#c98a3e'; x.fill(); } x.restore(); },
  jug: (p) => { x.save(); x.translate(p.x, p.y); x.scale(p.s, p.s); blob([[-24, 0], [24, 0], [30, -40], [14, -70], [-14, -70], [-30, -40]], '#b9714a'); rr(-12, -82, 24, 14, 4, '#9a5a38'); x.restore(); },
  stone: (p) => { x.save(); x.translate(p.x, p.y); x.scale(p.s, p.s); blob([[-40, 0], [40, 0], [34, -26], [10, -40], [-22, -34]], '#8d8577'); blob([[-40, 0], [-6, 0], [-14, -30], [-22, -34]], '#76705f'); x.restore(); },
  sign: (p) => { x.save(); x.translate(p.x, p.y); x.scale(p.s, p.s); rr(-6, -200, 12, 200, 3, '#7a5230'); blob([[-90, -190], [70, -190], [96, -168], [70, -146], [-90, -146]], '#3f7d4f'); blob([[90, -130], [-70, -130], [-96, -108], [-70, -86], [90, -86]], '#a14a3a'); x.restore(); },
  shield: (p, t) => { x.save(); x.translate(p.x, p.y); x.scale(p.s, p.s); x.beginPath(); x.moveTo(0, -80); x.quadraticCurveTo(60, -70, 66, -56); x.quadraticCurveTo(66, 20, 0, 60); x.quadraticCurveTo(-66, 20, -66, -56); x.quadraticCurveTo(-60, -70, 0, -80); x.fillStyle = C.green; x.fill(); x.strokeStyle = C.gold; x.lineWidth = 6; x.stroke(); x.beginPath(); x.arc(4, -6, 22, R(40), R(320)); x.stroke(); x.restore(); },
  fire: (p, t) => { x.save(); x.translate(p.x, p.y); x.scale(p.s, p.s); for (let i = 0; i < 3; i++) { const h = 80 - i * 22 + Math.sin(t * 9 + i) * 8; blob([[-40 + i * 12, 0], [40 - i * 12, 0], [0 + Math.sin(t * 7 + i) * 6, -h]], ['#e2572b', '#f08a2c', '#ffd25e'][i]); } x.restore(); },
  water: (p, t) => { x.save(); x.translate(p.x, p.y); x.scale(p.s, p.s); for (let i = 0; i < 3; i++) { const y = ((t * 220 + i * 40) % 120); x.beginPath(); x.ellipse(0, y - 60, 6, 10, 0, 0, 7); x.fillStyle = '#7cc3e8'; x.fill(); } x.restore(); },
  bubble: (p, t) => { x.save(); x.translate(p.x, p.y + Math.sin(t * 2) * 4); x.scale(p.s, p.s); rr(-80, -60, 160, 90, 30, '#ffffff'); blob([[-20, 28], [10, 28], [-30, 52]], '#ffffff'); x.fillStyle = p.c || '#3f7d4f'; for (let i = -1; i <= 1; i++) circ(i * 32, -15, 9, x.fillStyle); x.restore(); },
  hourglass: (p, t) => { x.save(); x.translate(p.x, p.y); x.scale(p.s, p.s); rr(-50, -140, 100, 12, 4, '#7a5230'); rr(-50, -8, 100, 12, 4, '#7a5230'); blob([[-40, -128], [40, -128], [6, -68], [40, -8], [-40, -8], [-6, -68]], 'rgba(220,235,245,.55)'); const k = (t * .08) % 1; blob([[-30 + k * 26, -118 + k * 46], [30 - k * 26, -118 + k * 46], [3, -70], [-3, -70]], '#e6c27a'); blob([[-36 * k, -8 - 34 * k], [36 * k, -8 - 34 * k], [40, -8], [-40, -8]], '#e6c27a'); x.restore(); },
  pen: (p) => { x.save(); x.translate(p.x, p.y); x.rotate(-.6); x.scale(p.s, p.s); rr(-8, -90, 16, 90, 4, '#6b4a2b'); blob([[-8, 0], [8, 0], [0, 22]], '#2a1d15'); x.restore(); },
  scroll: (p) => { x.save(); x.translate(p.x, p.y); x.scale(p.s, p.s); rr(-110, -150, 220, 150, 6, '#f3e2bd'); rr(-122, -162, 244, 22, 11, '#c9a46a'); rr(-122, -10, 244, 22, 11, '#c9a46a'); x.fillStyle = 'rgba(122,90,60,.35)'; for (let i = 0; i < 5; i++) x.fillRect(-84, -122 + i * 22, 168 - (i % 2) * 40, 5); x.restore(); },
  gift: (p) => { x.save(); x.translate(p.x, p.y); x.scale(p.s, p.s); rr(-40, -60, 80, 60, 6, '#3f7d4f'); rr(-6, -60, 12, 60, 2, C.gold); rr(-46, -72, 92, 16, 5, '#2f6b57'); circ(-10, -78, 10, C.gold); circ(10, -78, 10, C.gold); x.restore(); },
  cart: (p) => { x.save(); x.translate(p.x, p.y); x.scale(p.s, p.s); rr(-100, -110, 200, 70, 6, '#9a6b3c'); for (const w of [-60, 60]) { circ(w, -30, 30, '#6b4a2b'); circ(w, -30, 12, '#c9a46a'); } rr(90, -100, 80, 10, 4, '#6b4a2b'); x.restore(); },
  camel: (p, t) => { x.save(); x.translate(p.x, p.y); x.scale(p.s * (p.tilt < 0 ? -1 : 1), p.s); const f = '#c99a5e'; for (const l of [-50, -30, 40, 60]) rr(l, -90, 12, 90 + Math.sin(t * 5 + l) * 0, 5, '#b3854c'); x.beginPath(); x.ellipse(5, -110, 80, 34, 0, 0, 7); x.fillStyle = f; x.fill(); x.beginPath(); x.ellipse(-10, -140, 34, 26, 0, 0, 7); x.fill(); blob([[70, -120], [86, -130], [110, -200], [94, -206], [62, -140]], f); x.beginPath(); x.ellipse(116, -206, 26, 15, .2, 0, 7); x.fill(); circ(124, -212, 3, '#2a1d15'); x.restore(); },
  tree: (p) => { x.save(); x.translate(p.x, p.y); x.scale(p.s, p.s); rr(-12, -120, 24, 120, 6, '#7a5a3c'); for (const [a, b, r] of [[0, -170, 70], [-50, -130, 50], [50, -130, 50]]) circ(a, b, r, '#4f8a55'); for (const [a, b] of [[-30, -170], [26, -150], [0, -120]]) circ(a, b, 8, '#d9534f'); x.restore(); },
  sheep: () => { },
  bread: (p) => { x.save(); x.translate(p.x, p.y); x.scale(p.s, p.s); x.beginPath(); x.ellipse(0, -18, 46, 20, 0, 0, 7); x.fillStyle = '#d9a24e'; x.fill(); x.strokeStyle = '#b07a30'; x.lineWidth = 3; for (let i = -1; i <= 1; i++) { x.beginPath(); x.moveTo(i * 18 - 6, -28); x.lineTo(i * 18 + 6, -10); x.stroke(); } x.restore(); },
  rug: (p) => { x.save(); x.translate(p.x, p.y); x.scale(p.s, p.s); x.beginPath(); x.ellipse(0, 0, 150, 26, 0, 0, 7); x.fillStyle = '#8e2f2f'; x.fill(); x.strokeStyle = C.gold; x.lineWidth = 3; x.beginPath(); x.ellipse(0, 0, 130, 18, 0, 0, 7); x.stroke(); x.restore(); },
  mat: (p) => { x.save(); x.translate(p.x, p.y); x.scale(p.s, p.s); blob([[-70, 0], [70, 0], [60, -20], [-60, -20]], '#2f6b57'); x.strokeStyle = C.gold; x.lineWidth = 3; arch(0, -2, 50, 14, 'rgba(0,0,0,0)'); x.restore(); },
  key: (p) => { x.save(); x.translate(p.x, p.y); x.scale(p.s, p.s); x.strokeStyle = C.gold; x.lineWidth = 10; x.beginPath(); x.arc(-40, 0, 22, 0, 7); x.moveTo(-18, 0); x.lineTo(50, 0); x.moveTo(36, 0); x.lineTo(36, 18); x.moveTo(50, 0); x.lineTo(50, 22); x.stroke(); x.restore(); },
  steps: (p) => { x.save(); x.translate(p.x, p.y); x.scale(p.s, p.s); for (let i = 0; i < 5; i++) rr(-150 + i * 60, -i * 40 - 40, 300 - i * 60, 40, 3, i % 2 ? '#d8c39c' : '#e6d3b3'); x.restore(); },
  mountain: (p) => { x.save(); x.translate(p.x, p.y); x.scale(p.s, p.s); blob([[-200, 0], [0, -260], [200, 0]], '#6d7a8a'); blob([[-50, -190], [0, -260], [50, -190], [20, -200], [0, -180], [-20, -200]], '#f1f1f1'); x.restore(); },
  lock: (p) => { x.save(); x.translate(p.x, p.y); x.scale(p.s, p.s); x.strokeStyle = '#9aa3ad'; x.lineWidth = 12; x.beginPath(); x.arc(0, -60, 30, Math.PI, 0); x.stroke(); rr(-46, -60, 92, 70, 10, C.gold2); circ(0, -30, 9, '#5a4210'); x.restore(); },
  tongue: () => { },
  people: (p, t) => { const K = p.tilt || 5; for (let i = 0; i < K; i++) { const px = p.x + (i - K / 2 + .5) * 70 * p.s, py = p.y; x.save(); x.translate(px, py); x.scale(p.s, p.s); blob([[-28, 0], [28, 0], [24, -90], [-24, -90]], i % 2 ? '#e9e3d5' : '#2f6b57'); circ(0, -110, 22, i % 3 ? '#dba57a' : '#c48f63'); x.beginPath(); x.arc(0, -116, 22.5, Math.PI, 0); x.fillStyle = '#fff'; x.fill(); x.restore(); } },
  rows: (p, t) => { for (let r = 0; r < 2; r++) for (let i = 0; i < 6; i++) { x.save(); x.translate(p.x + (i - 2.5) * 95 + r * 30, p.y - r * 60); x.scale(.55 - r * .08, .55 - r * .08); const ph = p.ph || 0; const g = Math.max(0, Math.sin(t * .8 + ph)); blob([[-30, 0], [30, 0], [28, -120], [-28, -120]], '#f3efe6'); circ(0, -146, 28, '#ffffff'); x.restore(); } },
};

// ===== الخلفيات =====
function stars(t, n, col) { for (let i = 0; i < n; i++) { const sx = rnd(i) * W, sy = rnd(i + 99) * 700; const a = .35 + .65 * Math.abs(Math.sin(t * (.6 + rnd(i + 7)) + i)); x.globalAlpha = a; circ(sx, sy, 1 + rnd(i + 3) * 1.8, col || '#fff'); } x.globalAlpha = 1; }
function hills(col, y, amp, seed) { x.beginPath(); x.moveTo(0, H); for (let i = 0; i <= W; i += 20) x.lineTo(i, y - amp * (Math.sin(i / 140 + seed) * .6 + Math.sin(i / 60 + seed * 2) * .2)); x.lineTo(W, H); x.fillStyle = col; x.fill(); }
function tiles(top, c1, c2) { x.fillStyle = c1; x.fillRect(0, top, W, H - top); x.strokeStyle = c2; x.lineWidth = 2; for (let i = -10; i < 20; i++) { x.beginPath(); x.moveTo(360 + i * 80, top); x.lineTo(360 + i * 240, H); x.stroke(); } for (let j = 0; j < 6; j++) { const y = top + Math.pow(j / 6, 1.6) * (H - top); x.beginPath(); x.moveTo(0, y); x.lineTo(W, y); x.stroke(); } }
function grad(a, b, y0 = 0, y1 = H) { const g = x.createLinearGradient(0, y0, 0, y1); g.addColorStop(0, a); g.addColorStop(1, b); return g; }
const BG = {
  night: (t) => { x.fillStyle = grad('#0b1330', '#1b3050'); x.fillRect(0, 0, W, H); stars(t, 70); PROPS.moon({ x: 560, y: 560, s: 1.1, bgc: '#13234a' }); x.globalAlpha = .9; PROPS.mosque({ x: 200, y: GY - 120, s: .75, c: '#163a36' }); x.globalAlpha = 1; tiles(GY - 40, '#173a3a', 'rgba(255,255,255,.05)'); },
  day: (t) => { x.fillStyle = grad('#f3e3c4', '#ecd5b0'); x.fillRect(0, 0, W, H); PROPS.sun({ x: 560, y: 600, s: .9 }, t); hills('#e3c69c', GY - 140, 60, 1); hills('#d9b98c', GY - 80, 40, 3); tiles(GY - 40, '#e2c9a2', 'rgba(150,110,60,.12)'); },
  home: (t) => { x.fillStyle = '#e7d1ac'; x.fillRect(0, 0, W, H); x.fillStyle = '#dcc39a'; x.fillRect(0, 0, W, 620); for (const ax of [150, 570]) { arch(ax, 880, 150, 300, '#cdb185'); arch(ax, 870, 120, 270, '#f6e2ae'); } lantern(360, 600, 1, t); tiles(GY - 40, '#c9a77a', 'rgba(90,60,30,.12)'); PROPS.rug({ x: 360, y: GY + 25, s: 1.4 }); },
  mosque: (t) => { x.fillStyle = grad('#123d36', '#0e2f2a'); x.fillRect(0, 0, W, H); for (let i = 0; i < 4; i++) { arch(90 + i * 180, GY - 40, 140, 420, '#1a4d44'); arch(90 + i * 180, GY - 40, 112, 390, '#0f322c'); } for (let i = 0; i < 3; i++) lantern(180 + i * 180, 620, .9, t + i); tiles(GY - 40, '#7d2a2a', 'rgba(233,189,95,.18)'); },
  desert: (t) => { x.fillStyle = grad('#f6d9a8', '#f0c88a'); x.fillRect(0, 0, W, H); PROPS.sun({ x: 180, y: 640, s: 1.1 }, t); hills('#e8b878', GY - 120, 70, 2); hills('#dea868', GY - 60, 40, 5); x.fillStyle = '#d9a466'; x.fillRect(0, GY - 40, W, H); },
  dawn: (t) => { x.fillStyle = grad('#2b3a6b', '#e9a87a', 300, GY); x.fillRect(0, 0, W, H); stars(t, 30); hills('#3d4f6d', GY - 90, 50, 4); x.fillStyle = '#2f3d55'; x.fillRect(0, GY - 40, W, H); },
  market: (t) => { BG.day(t); for (let i = 0; i < 3; i++) { const sx = 120 + i * 240; rr(sx - 90, GY - 230, 180, 190, 4, '#d6b98e'); for (let k = 0; k < 6; k++) blob([[sx - 100 + k * 34, GY - 250], [sx - 66 + k * 34, GY - 250], [sx - 70 + k * 34, GY - 210], [sx - 96 + k * 34, GY - 210]], k % 2 ? '#a14a3a' : '#f3e7cf'); } },
  sky: (t) => { x.fillStyle = grad('#9fc6e6', '#e8f1f6'); x.fillRect(0, 0, W, H); for (let i = 0; i < 5; i++) PROPS.cloud({ x: 80 + i * 150, y: 560 + (i % 2) * 120, s: .9 }, t + i); hills('#9cc49a', GY - 60, 30, 1); x.fillStyle = '#8bb586'; x.fillRect(0, GY - 40, W, H); },
  light: (t) => { x.fillStyle = grad('#1b2a3a', '#d9c9a0', 300, H); x.fillRect(0, 0, W, H); for (let i = 0; i < 5; i++) PROPS.door({ x: 120 + i * 120, y: GY - 120, s: .62 }, t); const g = x.createRadialGradient(360, GY - 200, 20, 360, GY - 200, 500); g.addColorStop(0, 'rgba(255,240,200,.5)'); g.addColorStop(1, 'rgba(255,240,200,0)'); x.fillStyle = g; x.fillRect(0, 0, W, H); x.fillStyle = '#cbb98e'; x.fillRect(0, GY - 40, W, H); },
  scroll: (t) => { x.fillStyle = grad('#13223f', '#0b1026'); x.fillRect(0, 0, W, H); stars(t, 40, '#f3d48a'); for (let i = 0; i < 6; i++) { x.globalAlpha = .08; star8(360, 820, 260 - i * 40, C.gold); } x.globalAlpha = 1; x.fillStyle = '#0f1a33'; x.fillRect(0, GY - 40, W, H); },
  dark: (t) => { x.fillStyle = grad('#141a2b', '#262d40'); x.fillRect(0, 0, W, H); stars(t, 20, '#8a93b0'); x.fillStyle = '#1b2233'; x.fillRect(0, GY - 40, W, H); },
};

// ===== المؤثرات =====
const FX = {
  coins: (f, p, t) => { const [a, b] = f.arg.split('>').map(Number); for (let i = 0; i < 3; i++) { const q = ease((p * 1.4 - i * .15)); if (q <= 0 || q >= 1) continue; const cx = lerp(a, b, q), cy = 760 - Math.sin(q * Math.PI) * 160; coin(cx, cy, 18); } },
  hearts: (f, p, t) => { for (let i = 0; i < 7; i++) { const q = (p * 1.6 + i * .14) % 1; x.globalAlpha = Math.sin(q * Math.PI); heartShape(f.x + Math.sin(i * 2 + q * 6) * 70, f.y - q * 300, .9 + rnd(i) * .6, '#e0605a'); } x.globalAlpha = 1; },
  sparkle: (f, p, t) => { for (let i = 0; i < 10; i++) { const q = (t * .7 + rnd(i)) % 1; x.globalAlpha = Math.sin(q * Math.PI); star8(f.x + (rnd(i + 1) - .5) * 260, f.y + (rnd(i + 2) - .5) * 220 - q * 40, 6 + rnd(i) * 6, '#ffe39a'); } x.globalAlpha = 1; },
  rays: (f, p, t) => { x.save(); x.globalAlpha = .35 * Math.min(1, p * 3); x.translate(f.x || 360, f.y || 380); for (let i = 0; i < 9; i++) { x.rotate(R(14)); blob([[0, 0], [-40, 900], [40, 900]], 'rgba(255,233,170,.45)'); } x.restore(); },
  glow: (f, p, t) => { const r = 150 + Math.sin(t * 3) * 10; const g = x.createRadialGradient(f.x, f.y, 10, f.x, f.y, r); g.addColorStop(0, 'rgba(255,225,140,.55)'); g.addColorStop(1, 'rgba(255,225,140,0)'); x.fillStyle = g; x.beginPath(); x.arc(f.x, f.y, r, 0, 7); x.fill(); },
  x: (f, p) => { const k = back(p * 3); x.save(); x.translate(f.x, f.y); x.scale(k, k); x.strokeStyle = '#d64545'; x.lineWidth = 16; x.lineCap = 'round'; x.beginPath(); x.moveTo(-50, -50); x.lineTo(50, 50); x.moveTo(50, -50); x.lineTo(-50, 50); x.stroke(); x.restore(); },
  check: (f, p) => { const k = back(p * 3); x.save(); x.translate(f.x, f.y); x.scale(k, k); circ(0, 0, 58, '#3f9a5c'); x.strokeStyle = '#fff'; x.lineWidth = 14; x.lineCap = 'round'; x.beginPath(); x.moveTo(-26, 2); x.lineTo(-6, 22); x.lineTo(28, -20); x.stroke(); x.restore(); },
  drops: (f, p, t) => { for (let i = 0; i < 6; i++) { const q = (t * 1.6 + i / 6) % 1; x.globalAlpha = 1 - q; x.beginPath(); x.ellipse(f.x + (rnd(i) - .5) * 20, f.y + q * 120, 5, 9, 0, 0, 7); x.fillStyle = '#86c9ec'; x.fill(); } x.globalAlpha = 1; },
  num: (f, p) => { const k = back(p * 3); x.save(); x.translate(f.x, f.y); x.scale(k, k); circ(0, 0, 54, C.gold); x.fillStyle = C.navy; x.font = '700 54px UI'; x.textAlign = 'center'; x.textBaseline = 'middle'; x.fillText(f.arg, 0, 4); x.restore(); },
  grow: (f, p) => { const k = ease(p * 1.2); for (let i = 0; i < 10; i++) { const q = Math.min(1, k * 10 - i); if (q <= 0) break; coin(f.x + ((i % 5) - 2) * 44, f.y - Math.floor(i / 5) * 40, 18 * back(q)); } },
  fade: () => { },
};

// ===== تجهيز المشاهد =====
// كل لقطة: {t, bg, actors:[{id,type,x,dir,pose}], props:[{k,type,x,y,s}], fx:[{type,...,t0}]}
function parseActor(s) { // "man@250:give<" أو "man#b@250>480:walk"
  const m = s.match(/^(\w+)(?:#(\w+))?@(-?\d+)(?:>(-?\d+))?(?:,(\d+))?:(\w+)(<)?(?:\*([\d.]+))?$/);
  if (!m) throw new Error('actor ' + s);
  return { type: m[1], id: m[1] + (m[2] || ''), x: +m[3], to: m[4] != null ? +m[4] : null, y: m[5] ? +m[5] : GY, pose: m[6], dir: m[7] ? -1 : 1, s: m[8] ? +m[8] : 1 };
}
function parseProp(s) { // "coin@360,700*1.2" ، و ^ بالبداية يعني گدّام الأشخاص
  const front = s[0] === '^'; if (front) s = s.slice(1);
  const m = s.match(/^(\w+)@(-?\d+),(-?\d+)(?:\*([\d.]+))?(?:=([\w#.-]+))?$/);
  if (!m) throw new Error('prop ' + s);
  const o = { type: m[1], x: +m[2], y: +m[3], s: m[4] ? +m[4] : 1, k: s, front }; if (m[5]) { if (m[5][0] === '#') o.c = m[5]; else o.tilt = +m[5]; } return o;
}
function parseFx(s) { // "coins:250>480" "hearts@360,700" "num:3@200,600"
  const m = s.match(/^(\w+)(?::([^@]+))?(?:@(-?\d+),(-?\d+))?$/); if (!m) throw new Error('fx ' + s);
  return { type: m[1], arg: m[2], x: m[3] ? +m[3] : 360, y: m[4] ? +m[4] : 700 };
}
const shots = D.beats.map(b => ({ t: b.t, bg: b.bg, actors: (b.a || []).map(parseActor), props: (b.p || []).map(parseProp), fx: (b.f || []).map(parseFx) }));
const seedOf = id => [...id].reduce((s, c) => s + c.charCodeAt(0), 0);
function poseMix(a, b, p) {
  const A = POSE[a] || POSE.stand, B = POSE[b] || POSE.stand, o = {};
  for (const k of ['tor', 'head']) o[k] = lerp(A[k] || 0, B[k] || 0, p);
  o.la = [lerp(A.la[0], B.la[0], p), lerp(A.la[1], B.la[1], p)]; o.ra = [lerp(A.ra[0], B.ra[0], p), lerp(A.ra[1], B.ra[1], p)];
  o.l1 = lerp(A.legs === 1 ? 1 : 0, B.legs === 1 ? 1 : 0, p); o.l2 = lerp(A.legs === 2 ? 1 : 0, B.legs === 2 ? 1 : 0, p);
  for (const k of ['finger', 'palm', 'book', 'box', 'walk']) o[k] = p < .5 ? (A[k] || 0) : (B[k] || 0);
  return o;
}
function drawShot(i, t) {
  const S = shots[i], P = shots[i - 1], dt = t - S.t, sameBg = P && P.bg === S.bg;
  BG[S.bg] ? BG[S.bg](t) : BG.night(t);
  if (P && !sameBg && dt < .7) { x.save(); x.globalAlpha = 1 - ease(dt / .7); BG[P.bg](t); drawThings(P, t, t - P.t, 1, null); x.restore(); }
  drawThings(S, t, dt, sameBg ? 0 : 1, sameBg ? P : null);
}
function drawThings(S, t, dt, fresh, P) {
  const bgFade = fresh ? ease((dt - .3) / .6) : 1;
  // الأدوات
  const old = P ? P.props.filter(q => !S.props.some(r => r.k === q.k)) : [];
  old.forEach(q => { if (dt < .35) { x.save(); x.globalAlpha = 1 - dt / .35; PROPS[q.type](q, t); x.restore(); } });
  const drawProps = front => S.props.forEach((q, j) => {
    if (!!q.front !== front) return;
    const had = P && P.props.some(r => r.k === q.k);
    const k = had ? 1 : back((dt - .15 - j * .12) / .55);
    if (k <= 0) return;
    x.save(); x.translate(q.x, q.y); x.scale(k, k); x.translate(-q.x, -q.y); x.globalAlpha = Math.min(1, k) * bgFade; PROPS[q.type](q, t); x.restore();
  });
  drawProps(false);
  // الأشخاص
  const out = P ? P.actors.filter(q => !S.actors.some(r => r.id === q.id)) : [];
  out.forEach(q => { if (dt < .4) person(actorAt(q, q, 99, t, 1 - dt / .4), t); });
  S.actors.forEach(a => {
    const pa = P && P.actors.find(r => r.id === a.id);
    person(actorAt(a, pa, dt, t, pa ? 1 : ease(dt / .5) * (fresh ? Math.max(.001, bgFade) : 1)), t);
  });
  drawProps(true);
  // المؤثرات
  S.fx.forEach(f => { const p = Math.max(0, dt - .4) / 2.2; if (dt > .4) FX[f.type](f, Math.min(p, 1), t); });
}
function actorAt(a, pa, dt, t, al) {
  // يمشي من مكانه القديم للجديد، والوقفة تتحول بنعومة
  const start = pa ? (pa.to != null ? pa.to : pa.x) : a.x, end = a.to != null ? a.to : a.x;
  const dist = Math.abs(end - start), moves = dist > 4, dur = moves ? dist / 260 : 0;
  const walking = moves && dt < dur, q = moves ? ease(dt / dur) : 1;
  const prev = pa ? pa.pose : a.pose;
  let ps;
  if (walking) ps = poseMix(prev, 'walk', Math.min(1, dt / .25));
  else if (moves) ps = poseMix('walk', a.pose, ease((dt - dur) / .5));
  else ps = poseMix(prev, a.pose, ease(dt / .55));
  const dir = walking ? (end > start ? 1 : -1) : a.dir;
  return { type: a.type, x: lerp(start, end, q), y: a.y, dir, s: a.s, pose: ps, wph: t * 9, al: al, seed: seedOf(a.id) };
}

// ===== النص =====
const segW = D.segs.map(s => s.split(/\s+/));
const HL = (D.hl || []).map(strip);
function isHL(w) { const sw = strip(w).replace(/[^ء-يa-zA-Z]/g, '').toLowerCase(); return sw && HL.some(h => sw.includes(h.toLowerCase())); }
function layout(words, font, maxW) {
  x.font = font; const sp = x.measureText(' ').width, lines = [[]]; let lw = 0;
  words.forEach(w => { const ww = x.measureText(w).width; if (lw + ww > maxW && lines[lines.length - 1].length) { lines.push([]); lw = 0; } lines[lines.length - 1].push([w, ww]); lw += ww + sp; });
  return { lines, sp };
}
function drawText(t) {
  let i = -1; D.times.forEach((tm, k) => { if (t >= tm[0] - .25) i = k; });
  if (i < 0) return;
  const tm = D.times[i], words = segW[i];
  const font = AR ? '400 50px Amiri' : '700 40px Inter', lh = AR ? 86 : 56;
  const L = layout(words, font, 640);
  const blockH = L.lines.length * lh, top = 300 - blockH / 2 + lh * .7;
  const segDur = tm[1] - tm[0], fadeOut = i < D.times.length - 1 ? D.times[i + 1][0] - .25 : D.total - 3.2;
  const outA = 1 - ease((t - (fadeOut - .25)) / .25);
  let n = 0;
  // خلفية خفيفة ورا النص حتى ينقرا فوق أي مشهد
  x.save(); x.globalAlpha = .82 * outA * ease((t - tm[0] + .3) / .3); rr(24, top - lh * .95, W - 48, blockH + lh * .55, 28, 'rgba(11,16,38,.78)'); x.restore();
  L.lines.forEach((line, li) => {
    const lw = line.reduce((s, w) => s + w[1], 0) + L.sp * (line.length - 1);
    let cx = AR ? (W + lw) / 2 : (W - lw) / 2;
    line.forEach(([w, ww]) => {
      const appear = tm[0] - .2 + (n / Math.max(1, words.length)) * segDur * .85; n++;
      const q = ease((t - appear) / .35);
      if (q > 0) {
        x.save(); x.globalAlpha = q * outA; x.font = font; x.textBaseline = 'alphabetic';
        const hl = isHL(w), px = AR ? cx - ww : cx, py = top + li * lh + (1 - q) * 14;
        x.fillStyle = hl ? C.gold : C.ink; x.direction = AR ? 'rtl' : 'ltr'; x.textAlign = 'left';
        if (hl) { x.shadowColor = 'rgba(233,189,95,.45)'; x.shadowBlur = 14; }
        x.fillText(w, px, py); x.restore();
      }
      cx += AR ? -(ww + L.sp) : (ww + L.sp);
    });
  });
}
function header(t) {
  x.fillStyle = 'rgba(11,16,38,.86)'; x.fillRect(0, 0, W, 118);
  if (icon.complete) x.drawImage(icon, AR ? W - 92 : 28, 30, 62, 62);
  x.fillStyle = C.gold; x.font = AR ? '700 34px UI' : '700 32px Inter'; x.textAlign = AR ? 'right' : 'left'; x.direction = AR ? 'rtl' : 'ltr';
  x.fillText(AR ? 'أوّاب' : 'Awwab', AR ? W - 104 : 102, 64);
  x.fillStyle = '#cdd2e6'; x.font = AR ? '500 22px UI' : '500 21px Inter'; x.fillText(D.label, AR ? W - 104 : 102, 96);
  x.direction = 'ltr';
}
function footer(t) {
  x.fillStyle = 'rgba(11,16,38,.9)'; x.fillRect(0, SC_BOT, W, H - SC_BOT);
  x.fillStyle = '#a3aac8'; x.font = AR ? '500 22px UI' : '500 20px Inter'; x.textAlign = 'center'; x.direction = AR ? 'rtl' : 'ltr'; x.fillText(D.src, W / 2, SC_BOT + 52); x.direction = 'ltr';
  rr(60, SC_BOT + 84, W - 120, 6, 3, 'rgba(255,255,255,.12)'); rr(AR ? W - 60 - (W - 120) * t / D.total : 60, SC_BOT + 84, (W - 120) * Math.min(1, t / D.total), 6, 3, C.gold);
}
function intro(t) {
  const q = 1 - ease((t - 2.1) / .5); if (q <= 0) return;
  x.save(); x.globalAlpha = q; x.fillStyle = grad('#0b1026', '#152048'); x.fillRect(0, 0, W, H); stars(t, 60);
  for (let i = 0; i < 5; i++) { x.globalAlpha = q * .07; x.save(); x.translate(360, 560); x.rotate(t * .15 + i); star8(0, 0, 300 - i * 50, C.gold); x.restore(); }
  x.globalAlpha = q; const k = back(t / .8);
  if (icon.complete) { x.save(); x.translate(360, 520); x.scale(k, k); x.drawImage(icon, -95, -95, 190, 190); x.restore(); }
  x.fillStyle = C.gold; x.textAlign = 'center'; x.font = AR ? '700 64px UI' : '700 60px Inter'; x.direction = AR ? 'rtl' : 'ltr'; x.globalAlpha = q * ease((t - .4) / .5);
  x.fillText(D.title, 360, 720); x.fillStyle = '#cdd2e6'; x.font = AR ? '500 30px UI' : '500 28px Inter'; x.fillText(D.label, 360, 776); x.restore();
}
function outro(t) {
  const s = D.total - 3.0; if (t < s) return; const q = ease((t - s) / .6);
  x.save(); x.globalAlpha = q; x.fillStyle = grad('#0b1026', '#152048'); x.fillRect(0, 0, W, H); stars(t, 60);
  if (icon.complete) x.drawImage(icon, 265, 420, 190, 190);
  x.fillStyle = C.gold; x.textAlign = 'center'; x.font = AR ? '700 60px UI' : '700 58px Inter'; x.direction = AR ? 'rtl' : 'ltr'; x.fillText(AR ? 'أوّاب' : 'Awwab', 360, 690);
  x.fillStyle = '#cdd2e6'; x.font = AR ? '500 30px UI' : '500 28px Inter'; x.fillText(AR ? 'طريق العودة إلى الله' : 'The way back to Allah', 360, 745); x.restore();
}
window.R = function (t) {
  x.setTransform(1, 0, 0, 1, 0, 0); x.clearRect(0, 0, W, H);
  let i = 0; shots.forEach((s, k) => { if (t >= s.t) i = k; });
  // كاميرا: تقريب بطيء بكل لقطة
  const z = 1 + Math.min(1, (t - shots[i].t) / 8) * .035;
  x.save(); x.translate(360, 900); x.scale(z, z); x.translate(-360, -900);
  drawShot(i, t); x.restore();
  header(t); drawText(t); footer(t); intro(t); outro(t);
};
})();
