// مدرّبي: منطق التطبيق
import { EX, REST_DAY, DAY_NAMES, DAY_IMG, PROGRAMS, VID, CLIP, SUPP2, FD, IBS, SUPPS, SCHEDULE, TIPS, INFO, EASY, SUPP_LIB, BAN as BAN0, BAN2, BAN_WORDS, IBS_BAN, IBS_GOOD } from './data.js';
import { BODY } from './bodymap.js';
import { FOODS, RECIPES, CATS, GEN, DRINKS, MEAS, SECTIONS } from './food2.js';

/* ================= أيقونات ================= */
const I = {
  home: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M3 10.5 12 3l9 7.5V20a1 1 0 0 1-1 1h-5v-6H9v6H4a1 1 0 0 1-1-1z"/></svg>',
  dumb: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round"><path d="M6.5 6.5v11M17.5 6.5v11M3 9.5v5M21 9.5v5M6.5 12h11"/></svg>',
  food: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"><path d="M7 3v8M5 3v5a2 2 0 0 0 4 0V3M7 11v10M17 21V3c-2.5 1-4 3.5-4 7v3h4"/></svg>',
  pill: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="2.5" y="8.5" width="19" height="7" rx="3.5" transform="rotate(-40 12 12)"/><path d="m9.5 9.3 5 5"/></svg>',
  user: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="8" r="4"/><path d="M4 21c1-4.5 4.5-6.5 8-6.5s7 2 8 6.5"/></svg>',
  back: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.4" stroke-linecap="round"><path d="M9 5l7 7-7 7"/></svg>',
  arrow: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.6" stroke-linecap="round"><path d="M17 7 7 17M8 7h9v9"/></svg>',
  x: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.4" stroke-linecap="round"><path d="M6 6l12 12M18 6 6 18"/></svg>',
  play: '<svg viewBox="0 0 24 24" fill="currentColor"><path d="M7 4.5v15l12-7.5z"/></svg>',
  pause: '<svg viewBox="0 0 24 24" fill="currentColor"><rect x="6" y="5" width="4" height="14" rx="1.2"/><rect x="14" y="5" width="4" height="14" rx="1.2"/></svg>',
  check: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="3" stroke-linecap="round" stroke-linejoin="round"><path d="M5 12.5 10 17l9-10"/></svg>',
  fire: '<svg viewBox="0 0 24 24" fill="currentColor"><path d="M12 2s5 4.5 5 10a5 5 0 0 1-10 0c0-2.5 1.5-4 1.5-4s.5 2 2 2.5C10 7 12 2 12 2z"/></svg>',
  drop: '<svg viewBox="0 0 24 24" fill="currentColor"><path d="M12 2.5s6.5 7 6.5 11.5a6.5 6.5 0 0 1-13 0C5.5 9.5 12 2.5 12 2.5z"/></svg>',
  egg: '<svg viewBox="0 0 24 24" fill="currentColor"><path d="M12 2c3.5 0 7 6 7 11a7 7 0 0 1-14 0c0-5 3.5-11 7-11z"/></svg>',
  scale: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="3" y="3" width="18" height="18" rx="5"/><path d="M8 9a5 5 0 0 1 8 0l-3 3"/></svg>',
  info: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round"><circle cx="12" cy="12" r="9"/><path d="M12 11v6M12 7.5v.01"/></svg>',
  slow: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"><circle cx="12" cy="13" r="8"/><path d="M12 9v4l2.5 2M9 2h6"/></svg>',
  sun: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"><circle cx="12" cy="12" r="4.5"/><path d="M12 2v2.5M12 19.5V22M2 12h2.5M19.5 12H22M4.9 4.9l1.8 1.8M17.3 17.3l1.8 1.8M4.9 19.1l1.8-1.8M17.3 6.7l1.8-1.8"/></svg>',
  moon: '<svg viewBox="0 0 24 24" fill="currentColor"><path d="M20 14.5A8 8 0 1 1 9.5 4a6.5 6.5 0 0 0 10.5 10.5z"/></svg>',
  cup: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"><path d="M4 8h13v5a6 6 0 0 1-6 6h-1a6 6 0 0 1-6-6zM17 10h1.5a2.5 2.5 0 0 1 0 5H17M8 2v3M12 2v3"/></svg>',
  plate: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="9"/><circle cx="12" cy="12" r="5"/></svg>',
  bolt: '<svg viewBox="0 0 24 24" fill="currentColor"><path d="M13 2 4 14h7l-1 8 9-12h-7z"/></svg>',
  star: '<svg viewBox="0 0 24 24" fill="currentColor"><path d="m12 3 2.7 5.6 6.1.8-4.5 4.2 1.1 6.1L12 16.8l-5.4 2.9 1.1-6.1L3.2 9.4l6.1-.8z"/></svg>',
  trophy: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round"><path d="M7 4h10v5a5 5 0 0 1-10 0zM7 6H4a3 3 0 0 0 3 4M17 6h3a3 3 0 0 1-3 4M12 14v3M8 21h8M9 17h6"/></svg>',
  stop: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round"><circle cx="12" cy="12" r="9"/><path d="m6 6 12 12"/></svg>',
  gear: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="3"/><path d="M19.4 15a1.7 1.7 0 0 0 .3 1.8l.1.1a2 2 0 1 1-2.8 2.8l-.1-.1a1.7 1.7 0 0 0-1.8-.3 1.7 1.7 0 0 0-1 1.5V21a2 2 0 1 1-4 0v-.1a1.7 1.7 0 0 0-1.1-1.5 1.7 1.7 0 0 0-1.8.3l-.1.1a2 2 0 1 1-2.8-2.8l.1-.1a1.7 1.7 0 0 0 .3-1.8 1.7 1.7 0 0 0-1.5-1H3a2 2 0 1 1 0-4h.1a1.7 1.7 0 0 0 1.5-1.1 1.7 1.7 0 0 0-.3-1.8l-.1-.1a2 2 0 1 1 2.8-2.8l.1.1a1.7 1.7 0 0 0 1.8.3H9a1.7 1.7 0 0 0 1-1.5V3a2 2 0 1 1 4 0v.1a1.7 1.7 0 0 0 1 1.5 1.7 1.7 0 0 0 1.8-.3l.1-.1a2 2 0 1 1 2.8 2.8l-.1.1a1.7 1.7 0 0 0-.3 1.8V9a1.7 1.7 0 0 0 1.5 1H21a2 2 0 1 1 0 4h-.1a1.7 1.7 0 0 0-1.5 1z"/></svg>',
  warn: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"><path d="M10.3 3.9 1.8 18a2 2 0 0 0 1.7 3h17a2 2 0 0 0 1.7-3L13.7 3.9a2 2 0 0 0-3.4 0zM12 9v4M12 17h.01"/></svg>',
  watch: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"><rect x="6" y="6" width="12" height="12" rx="3.5"/><path d="M9 6l.6-3h4.8l.6 3M9 18l.6 3h4.8l.6-3M12 9.5V12l1.5 1"/></svg>',
  heart: '<svg viewBox="0 0 24 24" fill="currentColor"><path d="M12 21s-7.5-4.6-9.5-9.3C1 8 3.4 4.5 7 4.5c2 0 3.5 1 5 3 1.5-2 3-3 5-3 3.6 0 6 3.5 4.5 7.2C19.5 16.4 12 21 12 21z"/></svg>',
  steps: '<svg viewBox="0 0 24 24" fill="currentColor"><ellipse cx="8" cy="7" rx="3" ry="4.5"/><ellipse cx="16" cy="12" rx="3" ry="4.5"/><rect x="5.5" y="12.5" width="5" height="3" rx="1.5"/><rect x="13.5" y="17.5" width="5" height="3" rx="1.5"/></svg>',
  scan: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round"><path d="M4 8V5a1 1 0 0 1 1-1h3M16 4h3a1 1 0 0 1 1 1v3M20 16v3a1 1 0 0 1-1 1h-3M8 20H5a1 1 0 0 1-1-1v-3M7 8v8M10 8v8M13 8v8M16.5 8v8"/></svg>',
  chev: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.4" stroke-linecap="round"><path d="M15 5l-7 7 7 7"/></svg>',
  share: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M12 3v12M7.5 7.5 12 3l4.5 4.5M5 12v8h14v-8"/></svg>',
};
document.querySelectorAll('[data-i]').forEach(e => e.innerHTML = I[e.dataset.i]);

/* ================= أدوات ================= */
const $ = s => document.querySelector(s);
const AR = n => String(n);
const esc = s => String(s).replace(/[&<>"]/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' }[c]));
const pad = n => String(n).padStart(2, '0');
const dk = d => d.getFullYear() + '-' + pad(d.getMonth() + 1) + '-' + pad(d.getDate());
const $$ = q => [...document.querySelectorAll(q)];
const today = () => dk(new Date());
const daysBetween = (a, b) => Math.round((new Date(b + 'T12:00') - new Date(a + 'T12:00')) / 864e5);
let tT; function toast(m) { let t = $('.toast'); if (!t) { t = document.createElement('div'); t.className = 'toast'; document.body.append(t); } t.textContent = m; t.hidden = false; clearTimeout(tT); tT = setTimeout(() => t.hidden = true, 2600); }
const rng = r => r[0] === r[1] ? AR(r[0]) : AR(r[0]) + '-' + AR(r[1]);

/* ================= الحفظ ================= */
const KEY = 'coach-v4';
let S;
function def() { return { name: '', age: '', h: 168, w: 52, month: null, best: {}, last: {}, hist: [], weights: [], meals: {}, supp: {}, evals: [] }; }
try { S = Object.assign(def(), JSON.parse(localStorage.getItem(KEY) || '{}')); } catch (e) { S = def(); }
try { const o = JSON.parse(localStorage.getItem('coach-v3') || 'null'); if (o && !localStorage.getItem(KEY)) { S.age = o.age || ''; S.h = o.h || 168; S.weights = o.weights || []; } } catch (e) {}
const save = () => { try { localStorage.setItem(KEY, JSON.stringify(S)); } catch (e) {} };

/* ================= الكورس: 3 أيام تنعاد (صدر+ترايسبس، ظهر+بايسبس، أكتاف+رجل) وبعدها راحة، لمدة شهرين ================= */
const MDAYS = 56, CYC = ['A', 'B', 'C', 'R'];
const dayType = i => CYC[i % 4];
const progOf = id => PROGRAMS.find(p => p.id === id) || PROGRAMS[0];
function buildProg(pid, n, ev) {
  const T = progOf(pid), plan = {}, prevTop = id => (S.month && S.month.plan && Object.values(S.month.plan).flat().find(x => x.id === id) || {}).r?.[1];
  for (const d of ['A', 'B', 'C']) {
    plan[d] = T.days[d].map(([id, s0, r0, r1]) => {
      const e = EX[id]; let s = s0;
      if (ev) { if (ev.weak.some(m => e.m.includes(m))) s += 1; if (ev.feel === 'easy' && e.c) s += 1; if (ev.feel === 'hard') s -= 1; }
      s = Math.max(2, Math.min(5, s));
      let w = e.w0; const b = S.best[id];
      if (b && b.w) { w = b.w; const pt = prevTop(id) || r1; if (b.r >= pt) w = +(w + e.inc).toFixed(1); }
      return { id, s, r: e.sec ? [20, 40] : [r0, r1], rest: T.heavy && e.c ? 150 : e.c ? 90 : 60, w };
    });
  }
  return { v: 3, pid: T.id, n, name: T.n, goal: T.goal, start: today(), plan, done: {} };
}
if (!S.month || S.month.v !== 3) { const o = S.month && S.month.v === 2 ? S.month : null; S.month = buildProg(o ? o.pid : 'base', o ? o.n : 1); if (o) Object.assign(S.month, { start: o.start, done: o.done }); save(); }
const dDiff = (a, b) => Math.round((new Date(b + 'T12:00') - new Date(a + 'T12:00')) / 864e5);
// اليوم يتبدل لحاله كل يوم من تاريخ البداية الي انت حددته
function curDay() { if (!S.month.started) return 0; return Math.max(0, Math.min(MDAYS, dDiff(S.month.started, today()))); }
function startCourse(shift) { const d = new Date(); d.setDate(d.getDate() - (shift || 0)); S.month.started = dk(d); save(); }
const isDeload = i => i >= 48;
function setsAt(item, i) { if (S.month.n === 1 && i < 8 && !EX[item.id].sec) return Math.min(2, item.s); if (isDeload(i) && !EX[item.id].sec) return Math.max(2, item.s - 1); return item.s; }
function dayItems(i) { const t = dayType(i); return t === 'R' ? REST_DAY.map(id => ({ id, s: 1, r: EX[id].sec ? [30, 30] : [10, 10], rest: 15, w: 0 })) : S.month.plan[t]; }

/* ================= الحسابات ================= */
const curW = () => S.weights.length ? S.weights[S.weights.length - 1].w : +S.w || 52;
function targets() { const w = curW(), h = +S.h || 168, a = +S.age || 20; let k = (10 * w + 6.25 * h - 5 * a + 5) * 1.55 + 400; const adj = (S.evals.length ? S.evals[S.evals.length - 1].kcalAdj || 0 : 0) + ((S.adapt || {}).adj || 0); k = Math.round((k + adj) / 50) * 50; return { k, p: Math.round(w * 2), water: Math.round(w * .045 * 2) / 2 }; }
function optVal(o) { return o.it.reduce((s, [k, a]) => { const v = itemVal(k, a); return { k: s.k + v.k, p: s.p + v.p, c: s.c + v.c, f: s.f + v.f }; }, { k: 0, p: 0, c: 0, f: 0 }); }
function weekHist() { const now = new Date(); now.setHours(0, 0, 0, 0); const st = new Date(now); st.setDate(st.getDate() - 6); return S.hist.filter(h => new Date(h.d + 'T12:00') >= st); }
function muscleCount() { const c = {}; weekHist().forEach(h => (h.mus || []).forEach(m => c[m] = (c[m] || 0) + 1)); return c; }
function streak() { const ds = new Set(S.hist.map(h => h.d)); let n = 0; const d = new Date(); for (let i = 0; i < 60; i++) { const k = dk(d); if (ds.has(k)) n++; else if (i > 0) { const t = dayType(curDay()); if (!(i === 1 && t === 'R')) break; } d.setDate(d.getDate() - 1); } return n; }

/* ================= خريطة العضلات ================= */
function bodySvg(side, counts, big) {
  const col = m => { const n = counts[m] || 0; return n >= 2 ? 'var(--g)' : n === 1 ? 'var(--g2)' : 'var(--s3)'; };
  return `<svg viewBox="0 0 100 200" role="img" aria-label="${side === 'front' ? 'العضلات من گدام' : 'العضلات من ورا'}">${BODY[side].map(([m, ps]) => ps.map(p => `<polygon points="${p}" fill="${['head', 'neck', 'knees', 'adductor', 'abductor'].includes(m) ? '#1b1b20' : col(m)}" stroke="#3a3a42" stroke-width=".4"/>`).join('')).join('')}</svg>`;
}

/* ================= الرئيسية ================= */
const MN = { chest: 'الصدر', back: 'الظهر', shoulders: 'الكتف', biceps: 'الأمامية', triceps: 'الخلفية', quads: 'الفخذ', hamstrings: 'الفخذ الخلفي', glutes: 'المؤخرة', calves: 'السمانة', abs: 'البطن', forearms: 'الساعد', lowerback: 'أسفل الظهر' };
/* ================= التحفيز: المستوى والنقاط ================= */
const LEVELS = [[0, 'مبتدئ'], [300, 'متحمّس'], [900, 'مقاتل'], [2000, 'محارب'], [4000, 'بطل'], [7000, 'أسطورة']];
function xp() { const sets = S.hist.reduce((a, h) => a + (h.sets || 0), 0), wk = S.hist.filter(h => h.t !== 'R').length, meals = Object.values(S.eaten || {}).reduce((a, d) => a + Object.values(d).filter(Boolean).length, 0), water = Object.values(S.water || {}).reduce((a, n) => a + n, 0); return sets * 10 + wk * 50 + meals * 8 + water * 2 + (S.evals || []).length * 300; }
function level() { const x = xp(); let i = 0; LEVELS.forEach((l, k) => { if (x >= l[0]) i = k; }); const nx = LEVELS[i + 1]; return { name: LEVELS[i][1], n: i + 1, x, pct: nx ? (x - LEVELS[i][0]) / (nx[0] - LEVELS[i][0]) * 100 : 100, next: nx && nx[1] }; }
const QUOTES = ['اليوم الي ما تحب تروح بيه، هو اليوم الي يصنع الفرق 💪', 'جسمك يتذكر كل سِت تسويه', 'خطوة صغيرة كل يوم = جسم جديد بعد 6 أشهر', 'مو لازم تكون مثالي، لازم تكون موجود', 'البطل مو الي ما يتعب، البطل الي يكمّل', 'كل كيلو تزيده هو عضل يبين بالتيشيرت', 'نام زين، كُل زين، تمرّن زين. والباقي يجي وحده'];
const quote = () => QUOTES[new Date().getDate() % QUOTES.length];
function eatenPro() { const e = (S.eaten || {})[today()] || {}; return todayMeals().reduce((a, x) => e[x.m.k] ? a + optVal(x.o).p : a, 0); }
function ring3(v, col, r) { const C = 2 * Math.PI * r; return `<circle cx="70" cy="70" r="${r}" style="stroke:var(--ringbg)" stroke-width="11" fill="none"/><circle cx="70" cy="70" r="${r}" stroke="${col}" stroke-width="11" fill="none" stroke-linecap="round" stroke-dasharray="${C}" stroke-dashoffset="${C * (1 - Math.min(1, v))}"/>`; }
function installCard() {
  const sa = window.navigator.standalone || matchMedia('(display-mode: standalone)').matches;
  if (sa || S.hideInstall) return '';
  return `<div class="install"><b class="d">خلّيه تطبيق على شاشة الآيفون</b><p class="sm">افتح الرابط بسفاري ← اضغط زر المشاركة <span style="display:inline-flex;width:18px;vertical-align:-3px;color:var(--g)">${I.share}</span> ← "إضافة إلى الشاشة الرئيسية".</p><button class="btn ghost sm" data-hideinstall>سوّيتها</button></div>`;
}

/* ================= الكورس ================= */
let showPlan = false;
/* ================= الرئيسية v22 (تصميم داكن بالذهبي) ================= */
function last7(fn) { return Array.from({ length: 7 }, (_, k) => { const d = new Date(); d.setDate(d.getDate() - 6 + k); return fn(dk(d)); }); }
function spark(vals, h = 60) { const W = 140, mx = Math.max(1, ...vals), pts = vals.map((v, i) => [i * W / 6, h - 6 - v / mx * (h - 14)]); const path = pts.map((p, i) => (i ? 'L' : 'M') + p[0].toFixed(1) + ' ' + p[1].toFixed(1)).join(' '); return `<svg viewBox="0 0 ${W} ${h}" class="spark"><defs><linearGradient id="sg" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#ffb020" stop-opacity=".45"/><stop offset="1" stop-color="#ffb020" stop-opacity="0"/></linearGradient></defs><path d="${path} L${W} ${h} L0 ${h} Z" fill="url(#sg)"/><path d="${path}" fill="none" stroke="#ffb020" stroke-width="2.5" stroke-linejoin="round" stroke-linecap="round"/></svg>`; }
function bars7(vals, goal) { const mx = Math.max(goal || 1, ...vals); return `<div class="bars7">${vals.map((v, i) => `<i style="height:${Math.max(6, v / mx * 100)}%" class="${i === 6 ? 'on' : ''}"></i>`).join('')}</div>`; }
const kcalOn = d => { const e = (S.eaten || {})[d] || {}; return SLOTS.reduce((a, [s]) => e[s] ? a + optVal(pickFor(s, d)).k : a, 0); };
const proOn = d => { const e = (S.eaten || {})[d] || {}; return SLOTS.reduce((a, [s]) => e[s] ? a + optVal(pickFor(s, d)).p : a, 0); };
const WD = ['الأحد', 'الاثنين', 'الثلاثاء', 'الأربعاء', 'الخميس', 'الجمعة', 'السبت'], MO = ['كانون الثاني', 'شباط', 'آذار', 'نيسان', 'أيار', 'حزيران', 'تموز', 'آب', 'أيلول', 'تشرين الأول', 'تشرين الثاني', 'كانون الأول'];
function todoList(t) { // شنو لازم تاخذ اليوم، حسب نوع اليوم والشهر
  const m = new Date().getMonth(), winter = m >= 9 || m <= 3, train = t && t !== 'R', L = [];
  L.push(['crea', '⚡', 'كرياتين 3 غم', 'ملعقة صغيرة مسطّحة ويا الفطور، حتى يوم الراحة']);
  L.push(['prot', '🥛', train ? 'بروتين: سكوب واحد (25 غم)' : 'بروتين: سكوب إذا أكلك ناقص', train ? 'بعد التمرين خلال ساعتين' : 'ويا الفطور أو العصرونية']);
  if (winter || new Date().getDate() % 2 === 0) L.push(['vitd', '☀️', 'فيتامين د 25 مايكروغرام', 'كبسولة وحدة ويا الغدا']);
  L.push(['omega', '🐟', 'أوميغا 3: كبسولتين', 'ويا الغدا أو العشا']);
  L.push(['mag', '🌙', 'مغنيسيوم 200 مغ', 'قبل النوم بساعة']);
  L.push(['water', '💧', train ? 'مي: 10 گلاصات' : 'مي: 8 گلاصات', train ? 'گلاصين خلال التمرين' : 'وزّعها على اليوم']);
  return L;
}
function vHome() {
  const c = curDay(), M = S.month, P = progOf(M.pid), started = !!M.started, t = c < MDAYS ? dayType(c) : null, d = new Date();
  const tk = (S.tk || {})[today()] || {}, L = todoList(t), doneN = L.filter(x => tk[x[0]]).length, doneToday = !!M.done[c];
  const eaten = (S.eaten || {})[today()] || {};
  const work = !started ? `<div class="tw start"><small>${P.ic} ${P.n}</small><h2>جاهز تبدي الكورس؟</h2><p class="sm mut">اضغط أول ما تبدي أول تمرين. بعدها التطبيق يبدّل تمرينك لحاله كل يوم.</p><button class="gbtn" data-startc>💪 بديت الكورس اليوم</button></div>`
    : t === null ? `<div class="tw"><small>${P.n}</small><h2>خلصت الكورس 🎉</h2><button class="gbtn" data-eval>قيّم واختار الكورس الجاي</button></div>`
    : t === 'R' ? `<div class="tw rest"><small>اليوم ${c + 1} من ${MDAYS} • ${P.n}</small><h2>😴 اليوم راحة</h2><p class="sm mut">العضل يكبر وقت الراحة. امشي 30 دقيقة، وباچر ${DAY_NAMES[dayType(c + 1)]}.</p><button class="obtn" data-day="${c}">إطالات خفيفة 10 دقايق</button></div>`
    : `<div class="tw"><img src="img/ex3d/${DAY_IMG[t]}.jpg" alt=""><div class="twb"><small>تمرينك اليوم • يوم ${c + 1} من ${MDAYS}</small><h2>${DAY_NAMES[t]}</h2><div class="mchips">${[...new Set(M.plan[t].map(x => GRP(x.id)))].map(g => `<i>${MUSN(g)} ${M.plan[t].filter(x => GRP(x.id) === g).length}</i>`).join('')}</div><span class="xs mut num">${M.plan[t].length} تمارين • تقريباً ${M.plan[t].reduce((a, x) => a + x.s, 0) * 2 + 10} دقيقة</span>
      ${doneToday ? '<span class="done">✓ خلصته اليوم، عاشت إيدك</span>' : `<div class="row" style="gap:8px"><button class="gbtn" data-start="${c}">ابدأ التمرين</button><button class="obtn" data-pday="${t}">التمارين</button></div>`}</div></div>`;
  return `<div class="hbar"><button class="ib" data-settings aria-label="الإعدادات">${I.gear}</button><img class="wlogo d" src="img/logo-wide.webp" alt="NEXFIT"><img class="wlogo l" src="img/logo-wide-l.webp" alt="NEXFIT"><span class="coin">🔥<b class="num">${streak()}</b></span></div>
  <p class="hdate">${WD[d.getDay()]} ${d.getDate()} ${MO[d.getMonth()]}</p>
  ${installCard()}
  ${work}
  <div class="sec-h"><h2>🔔 لا تنسى اليوم</h2><span class="xs mut num">${doneN}/${L.length}</span></div>
  <div class="todo">${L.map(([k, ic, n, sub]) => `<button class="td ${tk[k] ? 'on' : ''}" data-tk="${k}"><span class="ic">${ic}</span><span class="grow"><b>${n}</b><small>${sub}</small></span><span class="ck">${I.check}</span></button>`).join('')}</div>
  <button class="pcbtn" data-protcalc><span>🧮</span><div class="grow"><b>حاسبة البروتين</b><small>شكد بروتين تحتاج اليوم وشلون تقسمه</small></div>${I.chev}</button>
  <div class="sec-h"><h2>🍽️ أكلك اليوم</h2><a class="xs" href="#food" style="color:var(--g)">كل الوجبات ‹</a></div>
  <div class="mrow">${SLOTS.map(([k, n]) => `<a href="#food" class="mc ${eaten[k] ? 'on' : ''}"><span>${eaten[k] ? '✓' : { b: '🍳', s: '🥣', l: '🍛', a: '🥤', d: '🥗' }[k]}</span><small>${n}</small></a>`).join('')}</div>`;
}
/* ================= التمارين حسب العضلة ================= */
const MUS = [['chest', 'الصدر', 'bbbench'], ['back', 'الظهر', 'pullup'], ['shoulders', 'الأكتاف', 'lateral'], ['legs', 'الرجل', 'squat'], ['biceps', 'البايسبس', 'preacher'], ['triceps', 'الترايسبس', 'skull'], ['forearms', 'الساعد', 'wristcurl'], ['abs', 'البطن', 'legraise']];
const MGROUP = id => { const m = (EX[id] || {}).m ? EX[id].m[0] : ''; return ['quads', 'hamstrings', 'glutes', 'calves'].includes(m) ? 'legs' : m === 'lowerback' ? 'back' : m; };
const GOF = m => ['quads', 'hamstrings', 'glutes', 'calves'].includes(m) ? 'legs' : m === 'lowerback' ? 'back' : m === 'traps' ? 'shoulders' : m;
const exList = g => Object.keys(EX).filter(id => EX[id].m && !REST_DAY.includes(id) && EX[id].m.some(m => GOF(m) === g));
function planOf(id) { for (const d of ['A', 'B', 'C']) { const x = (S.month.plan[d] || []).find(z => z.id === id); if (x) return x; } return null; }
const DMUS = { A: ['chest', 'triceps'], B: ['back', 'biceps'], C: ['shoulders', 'legs'] };
const GRP = id => GOF(EX[id].m[0]);
function weekSets() { const c = {}; for (const d of ['A', 'B', 'C']) for (const x of S.month.plan[d]) { const g = GRP(x.id); c[g] = (c[g] || 0) + x.s; } for (const g in c) c[g] = Math.round(c[g] * 7 / 4); return c; }
function balanceCard() {
  const c = weekSets(), L = [['chest', 'الصدر'], ['back', 'الظهر'], ['legs', 'الرجل'], ['shoulders', 'الأكتاف'], ['biceps', 'البايسبس'], ['triceps', 'الترايسبس']];
  return `<details class="card bal"><summary><b>⚖️ معادلة الكورس</b><span class="xs mut"> شكد تشتغل كل عضلة بالأسبوع</span></summary>
  <p class="xs mut" style="margin:8px 0">الدراسات تگول العضلة تكبر بـ<b>10-20 سِت بالأسبوع</b>. العضلة الكبيرة تاخذ 4 تمارين باليوم، والصغيرة 3، حتى الكل يكبر سوة.</p>
  ${L.map(([g, n]) => { const v = c[g] || 0; return `<div class="balr"><span>${n}</span><div class="bb"><i style="width:${Math.min(100, v / 24 * 100)}%"></i><em style="right:${10 / 24 * 100}%"></em><em style="right:${20 / 24 * 100}%"></em></div><b class="num" data-count="${v}">${v}</b></div>`; }).join('')}
  <p class="xs mut" style="margin-top:6px">الخطين = المنطقة الذهبية (10-20 سِت)</p></details>`;
}
const MUSN = g => (MUS.find(m => m[0] === g) || [, g])[1];
function vCourse() {
  const c = curDay(), M = S.month, P = progOf(M.pid), doneN = Object.keys(M.done).length, t = c < MDAYS ? dayType(c) : null;
  const pct = Math.round(doneN / MDAYS * 100), C2 = 2 * Math.PI * 34;
  const next = Array.from({ length: 8 }, (_, k) => c + k).filter(i => i < MDAYS).map(i => { const ty = dayType(i); return `<button class="cd ${i === c ? 'now' : ''} ${ty === 'R' ? 'rest' : ''}" data-day="${i}"><span class="xs num">يوم ${i + 1}</span><b>${ty === 'R' ? '😴' : ty === 'A' ? '🛡️' : ty === 'B' ? '🔻' : '🦵'}</b><small>${ty === 'R' ? 'راحة' : DAY_NAMES[ty]}</small></button>`; }).join('');
  return `${head('الكورس')}
  <div class="pcard2"><div class="row" style="gap:14px;align-items:center"><div class="pring"><svg viewBox="0 0 80 80"><circle cx="40" cy="40" r="34" stroke="rgba(255,255,255,.08)" stroke-width="8" fill="none"/><circle cx="40" cy="40" r="34" stroke="url(#pg)" stroke-width="8" fill="none" stroke-linecap="round" stroke-dasharray="${C2}" stroke-dashoffset="${C2 * (1 - doneN / MDAYS)}" transform="rotate(-90 40 40)"/><defs><linearGradient id="pg"><stop offset="0" stop-color="#ffc145"/><stop offset="1" stop-color="#ff8a00"/></linearGradient></defs></svg><b class="num" data-count="${pct}" data-suf="%">${pct}%</b></div>
   <div class="grow"><small>كورسك هسه • ${M.started ? 'اليوم ' + AR(Math.min(c + 1, MDAYS)) + ' من ' + MDAYS : 'ما بديت بعد'}</small><h2>${P.ic} ${P.n}</h2><p class="xs mut">${P.goal}</p></div></div>
   ${!M.started ? `<button class="gbtn" data-startc>💪 بديت الكورس اليوم</button>` : `<div class="shift"><button data-cshift="-1">‹ رجّع يوم</button><span class="xs mut">إذا فوّتت يوم أو سبقت</span><button data-cshift="1">قدّم يوم ›</button></div>`}
   ${t === null ? `<div class="donebox"><h3>خلصت الكورس 🎉</h3><p class="sm mut">قيّم نفسك، وبعدها اختار الكورس الجاي.</p><button class="gbtn" data-eval>قيّم واختار الكورس الجاي</button></div>`
   : `<div class="today"><div class="grow"><small>تمرين اليوم</small><h3>${t === 'R' ? 'راحة ومشي 30 دقيقة' : DAY_NAMES[t]}</h3>${t !== 'R' ? `<span class="xs mut num">${S.month.plan[t].length} تمارين • تقريباً ${S.month.plan[t].reduce((a, x) => a + x.s, 0) * 2 + 10} دقيقة</span>` : ''}</div><button class="gbtn" data-${t === 'R' ? 'day' : 'start'}="${c}">${t === 'R' ? 'شوف' : 'ابدأ'}</button></div>`}
  </div>
  ${t === null ? '' : `<div class="sec-h"><h2>الأيام الجاية</h2></div><div class="hs cdays">${next}</div>`}
  <div class="sec-h"><h2>أيام الكورس</h2><span class="xs mut">تنعاد لحد ما يخلص</span></div>
  <div class="col">${['A', 'B', 'C'].map((d, k) => `<button class="dayc" data-pday="${d}"><img src="img/ex3d/${DAY_IMG[d]}.jpg" alt=""><div class="grow"><small>اليوم ${['الأول', 'الثاني', 'الثالث'][k]}</small><h3>${DAY_NAMES[d]}</h3><div class="mchips">${[...new Set(S.month.plan[d].map(x => GRP(x.id)))].map(g => `<i class="num">${MUSN(g)} ${S.month.plan[d].filter(x => GRP(x.id) === g).length}</i>`).join('')}</div></div>${I.chev}</button>`).join('')}
   <div class="dayc rest"><span class="big">😴</span><div class="grow"><small>اليوم الرابع</small><h3>راحة</h3><p class="xs mut">العضل يكبر وقت الراحة. امشي 30 دقيقة وسوّي إطالات خفيفة.</p></div></div></div>
  ${balanceCard()}
  <button class="obtn wide2" data-pick>🔁 غيّر الكورس</button>
  <div class="sec-h"><h2>مكتبة التمارين</h2><span class="xs mut">كل التمارين حسب العضلة</span></div>
  <div class="mgrid3">${MUS.map(([g, n, img]) => `<button class="mus" data-mus="${g}"><img src="img/ex3d/${img}.jpg" alt="" loading="lazy"><div><b>${n}</b><small class="num">${exList(g).length} تمرين</small></div></button>`).join('')}</div>`;
}
function openPlanDay(d) {
  const L = S.month.plan[d];
  show(`<div class="row"><button class="ib" data-close aria-label="رجوع">${I.back}</button><div class="grow"><p class="xs mut">${progOf(S.month.pid).n}</p><h2>${DAY_NAMES[d]}</h2></div></div>
  <div class="card"><p class="sm">🔥 <b>قبل:</b> 5 دقايق إحماء، وأول تمرين سِت خفيف بنص الوزن.<br>⏱️ <b>الراحة:</b> دقيقة ونص بالتمارين الكبيرة، ودقيقة بالصغيرة.<br>📈 <b>تتطور شلون؟</b> لما تخلّص كل السِتات بأعلى عدّة، زيد الوزن شوية الجلسة الجاية.</p></div>
  ${[...new Set(L.map(x => GRP(x.id)))].map(g => { const G = L.filter(x => GRP(x.id) === g); return `<div class="sec-h"><h2>${MUSN(g)}</h2><span class="xs mut num">${G.length} تمارين • ${G.reduce((a, x) => a + x.s, 0)} سِت</span></div>
  <div class="col">${G.map(x => `<button class="exrow" data-ex="${x.id}"><img src="img/ex3d/${x.id}.jpg" alt="" loading="lazy"><div class="grow"><h3><span class="num" style="color:var(--g)">${L.indexOf(x) + 1}.</span> ${EX[x.id].n}</h3><p class="sm num" style="color:var(--g)">${x.s} سِتات • كل سِت ${x.r[0] === x.r[1] ? x.r[0] : x.r[0] + ' إلى ' + x.r[1]} ${EX[x.id].sec ? 'ثانية' : 'عدّة'}</p><p class="xs mut">${MNAME[EX[x.id].m[0]] || ''}${x.w ? ' • ابدي بـ ' + x.w + ' كغم' : ''}</p></div><span class="k">${I.play}</span></button>`).join('')}</div>`; }).join('')}`, true);
}
function openPick(rec) {
  const cur = S.month.pid, done = Object.keys(S.month.done).length;
  show(`<div class="row"><button class="ib" data-close aria-label="رجوع">${I.back}</button><div class="grow"><h2>اختار الكورس</h2><p class="xs mut">كل كورس شهرين، 3 أيام تمرين ويوم راحة وتنعاد</p></div></div>
  ${done && done < MDAYS ? `<div class="warm">⚠️ إذا غيّرت هسه يبدي الكورس الجديد من اليوم الأول. الأحسن تكمّل كورسك (${done} من ${MDAYS}).</div>` : ''}
  <div class="col">${PROGRAMS.map(P => `<button class="prog ${P.id === cur ? 'cur' : ''}" data-progv="${P.id}"><img src="img/ex3d/${P.img}.jpg" alt=""><div class="grow"><div class="row" style="gap:6px;flex-wrap:wrap">${P.id === cur ? '<span class="pill g">كورسك هسه</span>' : ''}${rec === P.id ? '<span class="pill g">⭐ ننصحك بيه</span>' : ''}</div><h3>${P.ic} ${P.n}</h3><p class="xs">${P.goal}</p><p class="xs mut">${P.who}</p></div>${I.chev}</button>`).join('')}</div>`, true);
}
function openProg(pid) {
  const P = progOf(pid);
  show(`<div class="row"><button class="ib" data-back aria-label="رجوع">${I.back}</button><div class="grow"><h2>${P.ic} ${P.n}</h2></div></div>
  <div class="card"><p class="sm">${P.goal}</p><p class="xs mut">${P.who} • شهرين • 3 أيام وراحة</p></div>
  ${['A', 'B', 'C'].map(d => `<div class="card"><h3>${DAY_NAMES[d]}</h3>${P.days[d].map(([id, sN, a, b]) => `<div class="row between sm" style="padding:6px 0;border-bottom:1px solid var(--line)"><span>${EX[id].n}</span><span class="num mut">${sN} × ${a}-${b}</span></div>`).join('')}</div>`).join('')}
  <button class="gbtn" style="width:100%" data-setprog="${P.id}">ابدأ هذا الكورس</button>`, true);
}
function setProg(pid) { const last = S.evals.length ? S.evals[S.evals.length - 1] : null, fin = curDay() >= MDAYS; S.month = buildProg(pid, (S.month.n || 1) + (fin || Object.keys(S.month.done).length ? 1 : 0), fin ? last : null); startCourse(); save(); closeScreen(); location.hash = '#course'; toast('بدا ' + progOf(pid).n + ' 💪'); }
function openMuscle(g) {
  const [, n] = MUS.find(m => m[0] === g), L = exList(g).sort((a, b) => (MGROUP(b) === g ? 2 : 0) + (EX[b].star ? 1 : 0) - (MGROUP(a) === g ? 2 : 0) - (EX[a].star ? 1 : 0));
  show(`<div class="row"><button class="ib" data-close aria-label="رجوع">${I.back}</button><div class="grow"><h1>تمارين ${n}</h1><p class="xs mut">${L.length} تمرين • اضغط على التمرين تشوف الحركة والشرح</p></div></div>
  <div class="exgrid">${L.map(id => { const e = EX[id]; return `<button class="excard" data-ex="${id}"><img src="img/ex3d/${id}.jpg" alt="" loading="lazy"><div><h3>${e.n}${e.star ? ' ⭐' : ''}</h3><p class="xs num">${e.sec ? '3 × 20-40 ثانية' : e.c ? '3 × 8-12' : '3 × 10-15'}</p></div></button>`; }).join('')}</div>`);
}
/* ================= شاشة اليوم ================= */
let SES = null;
const WARM = ['دقيقتين مشي سريع أو دراجة لحد ما تعرق شوية', 'تدوير الكتف لگدام وورا 10 مرات، وتدوير الذراع الممدودة 10', 'تدوير الرسغ 10 لكل جهة، وتدوير الورك 10', 'سكوات بدون وزن 10 مرات على مهلك', 'وقفة الجدار: ظهرك ويديك على الحايط، ارفع إيدك لفوگ 10 مرات (تفتح الكتف)'];
function openDay(i) {
  if (i >= MDAYS) { openEval(); return; }
  const t = dayType(i), it = dayItems(i);
  show(`<div class="row"><button class="ib" data-close aria-label="رجوع">${I.back}</button><div class="grow"><p class="xs mut">اليوم ${AR(i + 1)} من ${MDAYS} • ${progOf(S.month.pid).n}</p><h2>${DAY_NAMES[t]}</h2></div></div>
  <div class="month" style="min-height:200px"><img src="img/ex3d/${t === 'R' ? 'child' : DAY_IMG[t]}.jpg" alt=""><h1>${DAY_NAMES[t]}</h1><p class="sm mut">${t === 'R' ? 'مشي 30 دقيقة، وهاي التمارين 10 دقايق قبل النوم.' : 'إحماء: 5 دقايق مشي سريع أو دراجة، وأول تمرين سِت خفيف بنص الوزن.'}</p></div>
  ${t !== 'R' ? `<details class="card warmc"><summary><b>🔥 إحماء المفاصل (5 دقايق)</b><span class="xs mut"> يحمي الكتف والركبة والرسغ</span></summary><div class="steps sm">${WARM.map(w => `<p>${w}</p>`).join('')}</div></details>` : ''}
  ${isDeload(i) ? '<div class="warm">🌿 <b>أسبوع تخفيف:</b> سِت أقل وأوزان أخف 15٪. هذا مو كسل: العضل يكبر وقت الراحة، والمدربين الكبار يسوّوه كل 6-8 أسابيع.</div>' : ''}
  <div class="col">${it.map((x, k) => `<button class="exrow" data-ex="${x.id}"><img src="img/ex3d/${x.id}.jpg" alt="" loading="lazy"><div class="grow"><h3>${EX[x.id].n}${EX[x.id].star ? ' ⭐' : ''}</h3><p class="sm num" style="color:var(--g)">${AR(setsAt(x, i))} × ${rng(x.r)} ${EX[x.id].sec ? 'ثانية' : ''}</p><p class="xs mut">${x.w ? 'ابدي بـ ' + AR(x.w) + ' كغم' : 'بدون وزن'}</p></div><span class="k num">${AR(k + 1)}</span></button>`).join('')}</div>
  <button class="btn wide" data-start="${i}">${I.play} ${t === 'R' ? 'يلا نبدي' : 'ابدأ التمرين'}</button>
  ${S.month.done[i] ? '' : `<button class="btn ghost wide" data-skipday="${i}">${t === 'R' ? 'خلصت يوم الراحة ✓' : 'سوّيته بدون تسجيل ✓'}</button>`}`);
}

/* ================= الأنيميشن ================= */
let engineP = null, anims = [];
const engine = () => engineP || (engineP = import('./anim/engine.js'));
async function mountAnim(canvas, id, phEl) {
  if (!canvas) return null;
  try {
    const { createAnimator, EXERCISES } = await engine();
    if (!canvas.isConnected) return null;
    const E = EXERCISES[id]; if (!E) return null;
    const a = createAnimator(canvas, id, { theme: 'brand', onPhase: p => { if (phEl) phEl.textContent = p === 0 ? E.phases[0] : p === 1 ? E.phases[1] : p === 2 ? (E.hold ? E.phases[2] : 'اعصر') : 'استعد'; } });
    anims.push(a); return a;
  } catch (e) { if (phEl) phEl.textContent = 'ما گدر يشتغل الأنيميشن'; return null; }
}
function killAnims() { anims.forEach(a => { try { a.dispose(); } catch (e) {} }); anims = []; }

/* ================= شرح التمرين ================= */
const MNAME = { chest: 'الصدر', back: 'الظهر', shoulders: 'الكتف', traps: 'الترابيس', biceps: 'البايسبس', triceps: 'الترايسبس', forearms: 'الساعد', abs: 'البطن', obliques: 'الخواصر', quads: 'الفخذ الأمامي', hamstrings: 'الفخذ الخلفي', glutes: 'المؤخرة', calves: 'السمانة', lowerback: 'أسفل الظهر', hipflex: 'الورك' };
const vframe = (id, cls = 'vid') => `<div class="${cls}"><iframe src="https://www.youtube-nocookie.com/embed/${VID[id]}?autoplay=1&mute=1&loop=1&playlist=${VID[id]}&playsinline=1&rel=0&modestbranding=1" title="فيديو الحركة" referrerpolicy="strict-origin-when-cross-origin" allow="autoplay; encrypted-media; picture-in-picture; fullscreen" allowfullscreen loading="lazy"></iframe></div>`;
const HAS = new Set(CLIP);
const clipEl = (id, cls = 'clip') => `<div class="${cls}"><img src="img/clip/${id}-0.webp" alt=""><img class="b" src="img/clip/${id}-1.webp" alt=""><span class="cph"><i></i><span class="lb"><b class="p0">البداية</b><b class="p1">النهاية</b></span></span><span class="off">✓ يشتغل بدون نت</span></div>`;
function exInfo(id) {
  const e = EX[id];
  return `${HAS.has(id) ? clipEl(id) : VID[id] ? vframe(id) : `<div class="anim"><canvas id="ac"></canvas><span class="ph"><i></i><span id="aph">استعد</span></span></div>`}
  <div><p class="xs mut">اسمه بالجيم: ${e.gym}</p><h1>${e.n}${e.star ? ' ⭐' : ''}</h1><div class="mchips" style="margin-top:8px">${e.m.map((m, i) => `<i style="${i ? '' : 'background:var(--grad);color:#1a1000;font-weight:800'}">${i ? '' : '🎯 '}${MNAME[m] || m}</i>`).join('')}</div></div>
  ${HAS.has(id) && VID[id] ? `<button class="ytbtn" data-ytv="${id}">▶ شوف فيديو كامل من يوتيوب <small>(يحتاج نت)</small></button>` : ''}
  <div class="card"><h3>شلون تسويه</h3><div class="steps sm">${e.st.map(s => `<p>${s}</p>`).join('')}</div></div>
  ${e.bad.length ? `<div class="card"><h3>لا تسوي هيچ</h3><div class="bad sm col">${e.bad.map(s => `<p>${s}</p>`).join('')}</div></div>` : ''}
  ${EASY[id] && EX[EASY[id][0]] ? `<button class="easy" data-ex="${EASY[id][0]}"><img src="img/ex3d/${EASY[id][0]}.jpg" alt=""><div class="grow"><span class="xs" style="color:#34c759">صعبة عليك؟ جرّب الأسهل</span><b>${EX[EASY[id][0]].n}</b><span class="xs mut">نفس العضلة • ${EASY[id][1]}</span></div>${I.chev}</button>` : ''}
  ${TIPS[id] ? `<div class="lvl"><div><span class="pill g">للمبتدئ</span><p class="sm">${TIPS[id][0]}</p></div><div><span class="pill" style="color:var(--gold)">للمحترف</span><p class="sm">${TIPS[id][1]}</p></div></div>` : ''}
  ${e.sec ? '' : `<div class="card"><p class="sm"><b>الوزن الصح:</b> تخلّص العدّات وتحس تگدر تسوي 2 بعد بس. إذا كلش سهل زيد، وإذا الحركة خربت نقّص.</p></div>`}
  ${e.yt ? `<button class="video" data-yt="${e.yt}"><img src="https://i.ytimg.com/vi/${e.yt}/hqdefault.jpg" alt=""><span class="play"><span>${I.play}</span></span><span class="cap">شرح بالعربي من مدرّب (بيه صوت)</span></button>` : ''}`;
}
function openEx(id) { killAnims(); show(`<div class="row"><button class="ib" data-back aria-label="رجوع">${I.back}</button></div>${exInfo(id)}`, true); mountAnim($('#ac'), id, $('#aph')); }

/* ================= مشغّل التمرين ================= */
function startDay(i) {
  const it = dayItems(i);
  const dl = isDeload(i), lw = w => w ? (dl ? Math.round(w * .85 * 2) / 2 : w) : '';
  SES = { i, k: 0, deload: dl, items: it, sets: it.map(x => Array.from({ length: setsAt(x, i) }, () => ({ w: lw(x.w), r: EX[x.id].sec ? x.r[0] : x.r[1], ok: false }))) };
  closeScreen(true); renderPlayer();
}
function renderPlayer() {
  killAnims();
  const P = $('#player'), x = SES.items[SES.k], e = EX[x.id], sets = SES.sets[SES.k], n = SES.items.length;
  const doneEx = SES.sets.map(s => s.every(z => z.ok)); const C = 2 * Math.PI * 22, frac = (SES.k + 1) / n;
  const cur = sets.findIndex(s => !s.ok);
  P.hidden = false; document.body.style.overflow = 'hidden';
  P.innerHTML = `<div class="stage">${HAS.has(x.id) ? clipEl(x.id, 'clip pclip') : VID[x.id] ? vframe(x.id, 'pvid') : '<canvas id="pc"></canvas>'}<div class="fade"></div><div class="ov"><div class="row between"><button class="ib" data-pclose aria-label="طلّع">${I.x}</button><div class="row"><button class="ib" data-swap="${x.id}" aria-label="بدّل التمرين">⇄</button><button class="ib" data-slow aria-label="أبطأ">${I.slow}</button><button class="ib" data-info="${x.id}" aria-label="الشرح">${I.info}</button></div></div>
   <span class="ph"><i></i><span id="pph">استعد</span></span></div></div>
  <div class="ploop">
   ${S.last[x.id] ? `<div class="lastt"><span>المرة الفاتتة</span><b class="num">${S.last[x.id].map(z => AR(z.w) + '×' + AR(z.r)).join('  ')}</b></div>` : `<div class="lastt"><span>أول مرة</span><b>ابدي خفيف وتعلّم الحركة</b></div>`}
   <div class="row between"><div><h2>${e.n}${e.star ? ' ⭐' : ''}</h2><p class="xs mut">${e.gym}</p></div><span class="pill g num">${AR(sets.length)} × ${rng(x.r)}${e.sec ? ' ث' : ''}</span></div>
   ${sets.map((s, j) => `<div class="set ${s.ok ? 'done' : ''}"><span class="i ${j === cur ? 'cur' : ''}">${j === cur ? '●' : AR(j + 1)}</span>${!e.w0 ? `<div class="pillin"><span>${e.sec ? 'وزن الجسم' : 'بدون وزن'}</span></div>` : `<label class="pillin"><input inputmode="decimal" data-w="${j}" value="${s.w}" aria-label="الوزن"><span>كغم</span></label>`}<label class="pillin"><input inputmode="numeric" data-r="${j}" value="${s.r}" aria-label="العدّات"><span>${e.sec ? 'ث' : '×'}</span></label><button class="ok" data-ok="${j}" aria-label="خلصت السِت">${I.check}</button></div>`).join('')}
   ${SES.k === 0 && x.w ? `<div class="warm">🔥 <b>سِتات إحماء قبل:</b> <span class="num">${Math.round(x.w * .5 * 2) / 2}</span> كغم × 10، وبعدها <span class="num">${Math.round(x.w * .75 * 2) / 2}</span> كغم × 5. ما تنحسب.</div>` : ''}
   ${SES.deload ? '<div class="warm">🌿 أسبوع تخفيف: نفس الحركة بوزن أخف 15٪. جسمك يرتاح ويرجع أقوى.</div>' : ''}
   <p class="xs mut" style="text-align:center">خلي <b>1-2 عدّة بالخزان</b>: آخر عدّة صعبة بس حركتها صحيحة. ونزول الوزن على مهلك 3 ثواني. بعد كل سِت اضغط ✓ ويبدي وكت الراحة (${x.rest} ثانية)</p>
   ${SES.k < n - 1 ? `<button class="btn wide" data-pnext>التمرين الجاي</button>` : `<button class="btn wide" data-pfinish>خلصت اليوم 🎉</button>`}
   <div style="height:8px"></div>
  </div>
  <div class="pbar"><div class="ringp"><svg viewBox="0 0 52 52"><circle cx="26" cy="26" r="22" style="stroke:var(--s3)" stroke-width="5" fill="none"/><circle cx="26" cy="26" r="22" stroke="var(--g)" stroke-width="5" fill="none" stroke-linecap="round" stroke-dasharray="${C}" stroke-dashoffset="${C * (1 - frac)}"/></svg><b class="num">${AR(SES.k + 1)}/${AR(n)}</b></div>
   <div class="grow"><b class="d">${e.n}</b><p class="xs mut">${MN[e.m[0]] || ''}</p></div>
   <div class="dots">${SES.items.map((_, j) => `<button class="${j === SES.k ? 'on' : ''} ${doneEx[j] ? 'ok' : ''}" data-pgo="${j}">${AR(j + 1)}</button>`).join('')}</div></div>`;
  mountAnim($('#pc'), x.id, $('#pph'));
}
let restT, ac;
function rest(sec) {
  clearInterval(restT); let left = sec, all = sec; const o = document.createElement('div'); o.className = 'rest-ov'; document.body.append(o); const C = 2 * Math.PI * 100;
  const paint = () => { o.innerHTML = `<h2>ارتاح وتنفّس</h2><div class="ring"><svg viewBox="0 0 230 230"><circle cx="115" cy="115" r="100" style="stroke:var(--s3)" stroke-width="14" fill="none"/><circle cx="115" cy="115" r="100" stroke="#ff2d3d" stroke-width="14" fill="none" stroke-linecap="round" stroke-dasharray="${C}" stroke-dashoffset="${C * (1 - left / all)}"/></svg><b class="num">${AR(left)}</b></div><p class="mut sm">اشرب شوية مي</p><div class="row"><button class="btn ghost" data-plus>+15 ثانية</button><button class="btn" data-skip>كمّل</button></div>`; };
  paint(); o.onclick = ev => { if (ev.target.closest('[data-plus]')) { left += 15; all += 15; paint(); } if (ev.target.closest('[data-skip]')) { clearInterval(restT); o.remove(); } };
  restT = setInterval(() => { left--; if (left <= 0) { clearInterval(restT); o.remove(); beep(); toast('يلا السِت الجاي 💪'); return; } paint(); }, 1000);
}
function beep() { try { ac = ac || new (window.AudioContext || window.webkitAudioContext)(); const os = ac.createOscillator(), g = ac.createGain(); os.frequency.value = 880; g.gain.setValueAtTime(.3, ac.currentTime); g.gain.exponentialRampToValueAtTime(.001, ac.currentTime + .6); os.connect(g); g.connect(ac.destination); os.start(); os.stop(ac.currentTime + .6); } catch (e) {} try { navigator.vibrate && navigator.vibrate([200, 100, 200]); } catch (e) {} }
function finishDay(skip) {
  clearInterval(restT); const i = SES ? SES.i : skip; let sets = 0; const mus = new Set();
  if (SES) SES.items.forEach((x, k) => {
    const d = SES.sets[k].filter(s => s.ok); if (!d.length) return; sets += d.length; EX[x.id].m.forEach(m => mus.add(m));
    if (!EX[x.id].sec) { const top = d.reduce((a, s) => (+s.w > +a.w || (+s.w === +a.w && +s.r > +a.r)) ? s : a, d[0]); S.last[x.id] = d.map(s => ({ w: +s.w || 0, r: +s.r || 0 })); const b = S.best[x.id]; if (!b || +top.w > b.w || (+top.w === b.w && +top.r > b.r)) S.best[x.id] = { w: +top.w || 0, r: +top.r || 0 }; }
  });
  S.month.done[i] = today(); S.hist.push({ d: today(), t: dayType(i), sets, mus: [...mus] }); save();
  killAnims(); $('#player').hidden = true; $('#player').innerHTML = '';
  show(`${confetti()}<div class="col" style="min-height:75vh;justify-content:center;align-items:center;text-align:center;gap:18px"><div class="medal pop" style="width:auto;padding:20px 28px"><span class="c" style="width:84px;height:84px">${I.trophy}</span></div><h1>عاشت إيدك يا بطل!</h1><span class="pill g num">+${AR(sets * 10 + 50)} نقطة</span><p class="mut">خلصت اليوم ${AR(i + 1)} من ${MDAYS}${sets ? ' • ' + AR(sets) + ' سِت' : ''}</p><div class="card" style="text-align:right;width:100%"><p class="sm">${dayType(i) === 'R' ? 'باچر تمرين، نام زين الليلة.' : 'هسه: سكوب البروتين خلال ساعتين، وجبة زينة، ونوم 8 ساعات.'}</p></div><button class="btn wide" data-close>رجوع</button></div>`);
  SES = null;
}

/* ================= تقييم الشهر ================= */
let EV = null;
function openEval() {
  const comp = [...new Set(Object.values(S.month.plan).flat().filter(x => EX[x.id].c).map(x => x.id))];
  EV = { weak: [], feel: 'ok' };
  show(`<div class="row"><button class="ib" data-close aria-label="رجوع">${I.back}</button><h2>تقييم الكورس</h2></div>
  <div class="card"><p class="sm">جاوب بصراحة. من أجوبتك أنصحك بالكورس الجاي وأظبط الأوزان والعدّات.</p></div>
  <div class="card"><h3>وزنك هسه</h3><label class="f">بالكيلو<input class="field" id="evW" inputmode="decimal" value="${curW()}"></label></div>
  <div class="card"><h3>أثقل وزن شلته بكل تمرين</h3><p class="xs mut">الوزن والعدّات بأحسن سِت. معبّية من الي سجلته، عدّلها إذا تريد.</p>
   ${comp.map(id => `<div class="row"><img src="img/ex3d/${id}.jpg" alt="" style="width:46px;height:46px;border-radius:12px;object-fit:cover"><span class="grow sm">${EX[id].n}</span><input class="field" style="width:76px;text-align:center" inputmode="decimal" data-evw="${id}" value="${S.best[id]?.w ?? ''}" placeholder="كغم" aria-label="الوزن"><input class="field" style="width:62px;text-align:center" inputmode="numeric" data-evr="${id}" value="${S.best[id]?.r ?? ''}" placeholder="×" aria-label="العدّات"></div>`).join('')}</div>
  <div class="card"><h3>أي عضلة تحسها ضعيفة أو تريدها تكبر أكثر؟</h3><div class="chips" id="evWeak">${['chest', 'back', 'shoulders', 'biceps', 'triceps', 'quads', 'hamstrings', 'calves'].map(m => `<button data-weak="${m}">${MN[m]}</button>`).join('')}</div></div>
  <div class="card"><h3>شلون كان الكورس عليك؟</h3><div class="chips" id="evFeel"><button data-feel="easy">سهل</button><button data-feel="ok" class="on">مناسب</button><button data-feel="hard">صعب ومتعب</button></div></div>
  <button class="btn wide" data-evsubmit>شوف الكورس الجاي</button>`);
}
function submitEval() {
  const w = +$('#evW').value; if (w > 25 && w < 200) { const t = today(), x = S.weights.find(z => z.d === t); if (x) x.w = w; else S.weights.push({ d: t, w }); }
  document.querySelectorAll('[data-evw]').forEach(inp => { const id = inp.dataset.evw, wv = +inp.value, r = +document.querySelector(`[data-evr="${id}"]`).value; if (wv || r) S.best[id] = { w: wv || 0, r: r || 0 }; });
  const prevW = S.evals.length ? S.evals[S.evals.length - 1].w : (S.weights[0]?.w || +S.w), gain = curW() - prevW;
  const kcalAdj = (S.evals.length ? S.evals[S.evals.length - 1].kcalAdj || 0 : 0) + (gain < .8 ? 200 : gain > 2.5 ? -150 : 0);
  const ev = { d: today(), month: S.month.n, w: curW(), gain, weak: EV.weak, feel: EV.feel, kcalAdj };
  S.evals.push(ev); save();
  const W = EV.weak, rec = W.some(m => m === 'back') ? 'vtaper' : W.some(m => m === 'shoulders') ? 'shoulders' : W.some(m => m === 'biceps' || m === 'triceps') ? 'arms' : W.includes('chest') ? 'chest' : EV.feel === 'easy' ? 'strength' : S.month.pid === 'base' ? 'vtaper' : 'strength';
  closeScreen(true); openPick(rec);
}

/* ================= الأكل ================= */
/* ================= الأكل: أقسام، وكل وجبة بجدول مكوناتها ومجموعها ================= */
let fdCat = 'market', fdQ = '';
const SLOTS = [['b', 'الريوق', '7-9 الصبح'], ['s', 'سناك', 'الضحى'], ['l', 'الغدا', '1-3 الظهر'], ['a', 'العصرونية', 'بعد التمرين'], ['d', 'العشا', 'قبل النوم بـ3 ساعات']];
const POOL = { b: ['b'], s: ['s'], l: ['l'], a: ['sh', 's'], d: ['d'] };
const dayNo = (d = today()) => Math.floor(new Date(d + 'T12:00') / 864e5);
const hsh = n => { n = (n ^ 61) ^ (n >>> 16); n = n + (n << 3); n ^= n >>> 4; n = Math.imul(n, 0x27d4eb2d); return (n ^ (n >>> 15)) >>> 0; };
function perm(len, seed) { const a = [...Array(len).keys()]; for (let i = len - 1; i > 0; i--) { const j = hsh(seed * 131 + i) % (i + 1); [a[i], a[j]] = [a[j], a[i]]; } return a; }
function genMeal(seed) {
  const g = GEN, P = g.pro[hsh(seed) % g.pro.length], Cb = g.carb[hsh(seed + 7) % g.carb.length], Vg = g.veg[hsh(seed + 13) % g.veg.length], St = g.style[hsh(seed + 29) % g.style.length];
  return { id: 'g' + seed, s: 'l', gen: 1, t: 30, n: `${P[2]} ${St[0]} ويا ${Cb[2]}`, img: 'dish/' + P[3], tag: 'أكلة جديدة اخترعها NEXFIT إلك: بروتين ونشويات وخضرة بطريقة طبخ مختلفة', it: [[P[0], P[1]], [Cb[0], Cb[1]], ...Vg, [St[1], 14]],
    prep: [St[2], `اطبخ ${FOODS[Cb[0]].n} على جنب`, `الخضرة: ${Vg.map(x => FOODS[x[0]].n).join(' و')}، مشوية أو مسلوقة`, 'رتّب الصحن: ربعه بروتين، ربعه نشويات، ونصه خضرة'] };
}
function recById(id) { return id[0] === 'g' ? genMeal(+id.slice(1)) : RECIPES.find(r => r.id === id); }
function poolOf(slot, d) { const cats = POOL[slot]; const n = dayNo(d); const c = cats.length > 1 ? cats[n % cats.length] : cats[0]; const R = S.rate || {}; const L0 = RECIPES.filter(r => r.s === c && !((S.fx || {})[r.id] < 0) && !(R[r.id] && R[r.id] <= 2)); const L1 = SUS && SUS.size ? L0.filter(r => !r.it.some(x => SUS.has(x[0]))) : L0; const L = L1.length >= 4 ? L1 : L0; return L.concat(L.filter(r => R[r.id] >= 4)); }
function pickFor(slot, d = today()) {
  const own = ((S.mp || {})[d] || {})[slot]; if (own) return recById(own);
  const pool = poolOf(slot, d), n = dayNo(d), sw = ((S.msw || {})[d] || {})[slot] || 0;
  if (slot === 'l' && (n + sw) % 3 === 2) return genMeal(n * 7 + sw);
  const order = perm(pool.length, slot.charCodeAt(0) * 977 + Math.floor((n + sw) / pool.length));
  return pool[order[(n + sw) % pool.length]];
}
function itemVal(k, a) { const f = FOODS[k]; if (!f) return { k: 0, p: 0, c: 0, f: 0 }; const m = a / 100; return { k: f.v[0] * m, p: f.v[1] * m, c: f.v[2] * m, f: f.v[3] * m }; }
function todayMeals() { calcScale(); return SLOTS.map(([k, n, t]) => ({ m: { k, n, t }, o: Object.assign({}, forMe(pickFor(k))), j: 0 })).map(x => (x.o.fn = x.o.n, x)); }
const fimg = k => FOODS[k] && FOODS[k].img ? `img/${FOODS[k].img}.webp` : '';
const fthumb = (k, sz = 52) => `<span class="pth" style="width:${sz}px;height:${sz}px">${fimg(k) ? `<img src="${fimg(k)}" alt="" loading="lazy">` : '🍽'}</span>`;
const r1 = x => Math.round(x * 10) / 10;
function amt(k, a) { const M = MEAS[k]; let h = ''; if (M) { const q = Math.round(a / M[1] * 2) / 2; if (q >= .5 && q <= 40) h = `${q === .5 ? 'نص' : q} ${M[0]}`; } return { g: `${Math.round(a)} غم`, h }; }
/* شكد مرة تاكله: قواعد من إرشادات التغذية للرياضيين */
function freqOf(k) {
  const f = FOODS[k], F = { tuna: 'لحد 3 علب بالأسبوع (الزئبق)', salmon: 'مرتين بالأسبوع', herring: 'مرتين بالأسبوع', mackerel: 'مرتين بالأسبوع', sardine: 'مرتين بالأسبوع', beef: '2-3 مرات بالأسبوع', mince: '2-3 مرات بالأسبوع', lamb: 'مرة أو مرتين بالأسبوع', egg: 'كل يوم، 2-4 بيضات', chicken: 'كل يوم عادي', thigh: 'كل يوم عادي', turkey: 'كل يوم عادي', choc: 'مربعين باليوم بالكثير', chips: 'مرة بالأسبوع', popcorn: 'كم مرة بالأسبوع', cola: 'لا، أو نادراً', oj: 'گلاص صغير باليوم', coffee: 'گلاصين باليوم بالكثير', brazil: 'حبتين باليوم، مو أكثر', butter: 'ملعقة باليوم', maple: 'ملعقة أو ثنتين باليوم', bun: 'مرتين بالأسبوع', water: 'طول اليوم، 8-10 گلاصات', dates: 'تمرة وحدة باليوم' };
  if (F[k]) return F[k];
  if (f.ibs === 'bad') return 'قللها هسه، أو جرّب كمية صغيرة';
  if (f.ibs === 'limit') return 'كمية صغيرة، عادي كل يوم';
  if (f.cat === 'veg' || f.cat === 'fruit') return 'كل يوم، كلما أكثر أحسن';
  if (f.cat === 'nuts') return 'كل يوم گبضة صغيرة';
  if (f.cat === 'market' || f.cat === 'dairy') return 'كل يوم عادي';
  if (f.cat === 'grain') return 'كل يوم، أساس التضخيم';
  return 'عادي';
}
const ibsB = i => i === 'ok' ? '<i class="ok">يناسب القولون</i>' : i === 'limit' ? '<i class="mid">كمية قليلة</i>' : '<i class="no">ينفخ</i>';
const recImg = r => `img/${r.img}.webp`, isCut = r => /^(fd|mkt|supp)\//.test(r.img);
function score(r) { const v = optVal(r), ibs = r.it.every(([k]) => FOODS[k].ibs === 'ok') ? 5 : r.it.some(([k]) => FOODS[k].ibs === 'bad') ? 2 : 4; return { pro: Math.min(5, Math.max(1, Math.round(v.p / 9))), ease: (r.t || 15) <= 10 ? 5 : r.t <= 20 ? 4 : r.t <= 35 ? 3 : 2, ibs }; }
function macroRow(v, big) { return `<div class="mac ${big ? 'big' : ''}"><div><b class="num">${Math.round(v.k)}</b><span>سعرة</span></div><div><b class="num" style="color:var(--gold)">${Math.round(v.p)}</b><span>بروتين غ</span></div><div><b class="num" style="color:var(--blue)">${Math.round(v.c)}</b><span>كارب غ</span></div><div><b class="num" style="color:#ff9f0a">${Math.round(v.f)}</b><span>دهون غ</span></div></div>`; }
function vFood() {
  const T = targets(), eaten = (S.eaten || {})[today()] || {}, TM = todayMeals();
  const tot = TM.reduce((a, x) => { if (!eaten[x.m.k]) return a; const v = optVal(x.o); return { k: a.k + v.k, p: a.p + v.p, c: a.c + v.c, f: a.f + v.f }; }, { k: 0, p: 0, c: 0, f: 0 });
  const plan = TM.reduce((a, x) => { const v = optVal(x.o); return { k: a.k + v.k, p: a.p + v.p }; }, { k: 0, p: 0 });
  const bar = (v, max, col, n, u) => `<div class="mbar"><div class="row between"><span class="xs">${n}</span><span class="xs num"><span dir="ltr"><b>${Math.round(v)}</b> / ${max}</span> ${u}</span></div><div class="bar"><i style="width:${Math.min(100, v / max * 100)}%;background:${col}"></i></div></div>`;
  const IC = { b: ['🍳', '#ff9f0a'], s: ['🥣', '#34c759'], l: ['🍛', '#ff2d3d'], a: ['🥤', '#5e5ce6'], d: ['🥗', '#30b0c7'] }, SEC = { b: 'b', s: 's', l: 'l', a: 'sh', d: 'd' };
  const extra = [['fridge', '🧊', 'شنو عندي بالبيت؟', 'اختار الي بالثلاجة وأگلك شنو تطبخ'], ['sw', '🍫', 'حلا صحي', 'حلو بدون ما يخرّب جسمك'], ['k', '🥜', 'كرزات وموالح', 'مكسرات وبذور وفوايدها'], ['sh', '🥤', 'شيكات التضخيم', 'سعرات وبروتين بگلاص'], ['drinks', '💧', 'المشروبات', 'شنو تشرب وشنو لا'], ['fdb', '🔎', 'الأطعمة والبذور', Object.keys(FOODS).length + ' أكلة بقيمها'], ['shop', '🛒', 'سلة الأسبوع', 'شنو تشتري من الماركت'], ['supps', '💊', 'المكملات', 'بروتين وكرياتين وفيتامينات وروابط الشراء']];
  return `${head('الأكل')}
  <div class="card"><div class="sec-h"><h2>أكلت اليوم</h2><span class="xs mut num">القائمة: ${Math.round(plan.k)} سعرة • ${Math.round(plan.p)}g بروتين</span></div>
   ${bar(tot.k, T.k, 'var(--g)', 'السعرات', 'سعرة')}${bar(tot.p, T.p, 'var(--gold)', 'البروتين', 'غم')}${bar(tot.c, Math.round(T.k * .5 / 4), 'var(--blue)', 'الكارب', 'غم')}${bar(tot.f, Math.round(T.k * .27 / 9), '#ff9f0a', 'الدهون', 'غم')}
   <p class="xs mut">هدفك للتضخيم النظيف: ${T.k} سعرة و${T.p}g بروتين.</p></div>
  <button class="pcbtn" data-protcalc><span>🧮</span><div class="grow"><b>حاسبة البروتين</b><small>وزنك ← شكد تحتاج، وجدول تقسيمه على الوجبات</small></div>${I.chev}</button>
  <div class="sec-h"><h2>وجباتك اليوم</h2><span class="xs mut">اضغط على الوجبة وسجّل شنو أكلت</span></div>
  <div class="meals">${TM.map(({ m, o }) => { const v = optVal(o), c = IC[m.k]; return `<div class="ml ${eaten[m.k] ? 'on' : ''}"><button class="mlb" data-sec="${SEC[m.k]}" data-forslot="${m.k}"><span class="mi" style="background:${c[1]}22">${c[0]}</span><b>${m.n}</b><small>${m.t}</small><span class="mn">${o.n}</span><span class="xs num" style="color:var(--g)">${Math.round(v.p)}g بروتين • ${Math.round(v.k)} سعرة</span></button><button class="mck ${eaten[m.k] ? 'on' : ''}" data-eat="${m.k}">${eaten[m.k] ? '✓ أكلتها' : 'سجّل إنك أكلتها'}</button></div>`; }).join('')}</div>
  <div class="sec-h"><h2>أقسام ثانية</h2></div>
  <div class="slist">${extra.map(([k, ic, n, sub]) => { const at = k === 'ban' || k === 'supps' ? `href="#${k}"` : ['drinks', 'fdb', 'shop', 'fridge'].includes(k) ? `data-${k}` : `data-sec="${k}"`; const tag = k === 'ban' || k === 'supps' ? 'a' : 'button'; return `<${tag} class="slot ex" ${at}><span class="sico">${ic}</span><span class="stxt"><b>${n}</b><span class="xs mut">${sub}${['sw', 'k', 'sh'].includes(k) ? ' • ' + RECIPES.filter(r => r.s === k).length + ' وصفة' : ''}</span></span>${I.chev}</${tag}>`; }).join('')}</div>`;
}
function openSection(k, forSlot) {
  const sec = SECTIONS.find(x => x[0] === k), L = RECIPES.filter(r => r.s === k).concat(k === 'l' ? [0, 1, 2, 3, 4, 5].map(i => genMeal(dayNo() * 7 + 100 + i)) : []);
  const slot = forSlot || { b: 'b', l: 'l', d: 'd', s: 's', sh: 'a', sw: 's', k: 's' }[k], curR = pickFor(slot), cur = curR.id, slotN = (SLOTS.find(x => x[0] === slot) || [])[1];
  const cv = optVal(curR), mine = curR.s === k || (k === 'sh' && slot === 'a');
  const html = `<div class="row"><button class="ib" data-close aria-label="رجوع">${I.back}</button><div class="grow"><h1>${sec[1]}</h1><p class="xs mut">${sec[2]} • ${L.length} وصفة</p></div></div>
  ${mine ? `<button class="curmeal noimg" data-rec="${cur}" data-slot="${slot}"><div><span class="xs">✓ ${slotN} اليوم</span><b>${curR.n}</b>${macroRow(cv)}<span class="xs" style="opacity:.85">اضغط تشوف المكونات بالغرام وشلون تسويها</span></div></button>` : ''}
  <div class="sec-h"><h2>${mine ? 'بدّل بوحدة من هاي' : 'كل الوصفات'}</h2><span class="xs mut">الأعلى بروتين أول</span></div>
  <div class="col">${L.filter(r => r.id !== cur).map(r => [r, optVal(r)]).sort((a, b) => b[1].p - a[1].p).map(([r, v]) => `<div class="rrow"><button class="rmain" data-rec="${r.id}" data-slot="${slot}">${r.gen ? '<span class="newtag">✨ جديدة</span>' : ''}<span class="grow col" style="gap:3px"><b>${r.n}</b><span class="xs mut clamp">${r.tag || ''}</span><span class="pmac num"><span><b style="color:var(--gold)">${Math.round(v.p)}g</b> بروتين</span><span><b>${Math.round(v.k)}</b> سعرة</span><span>⏱ ${r.t || 15}د</span></span></span></button><button class="pick" data-userec="${r.id}:${slot}:${k}">اختارها</button></div>`).join('')}</div>`;
  const s = $('#screen'); if (!s.hidden && s.querySelector('.curmeal,.rrow')) { const y = s.scrollTop; s.innerHTML = `<div class="in keep">${html}</div>`; s.scrollTop = y; } else show(html);
}
function openRecipe(id, slot) {
  calcScale(); const o = forMe(recById(id)), v = optVal(o), sl = SLOTS.find(x => x[0] === slot) || SLOTS.find(x => POOL[x[0]].includes(o.s)) || SLOTS[2], cur = pickFor(sl[0]).id === id, sc = score(o), my = (S.rate || {})[id] || 0;
  const bar5 = (n, x) => `<div class="sc"><span class="xs">${n}</span><span class="dots5">${[1, 2, 3, 4, 5].map(i => `<i class="${i <= x ? 'on' : ''}"></i>`).join('')}</span></div>`;
  show(`<div class="row"><button class="ib" data-back aria-label="رجوع">${I.back}</button><div class="grow"><p class="xs mut">${sl[1]}</p></div><span class="pill num">⏱ ${o.t || 15} دقيقة</span></div>
  <h1 class="rtitle">${o.n}</h1>
  ${o.tag ? `<p class="sm">${o.tag}</p>` : ''}
  ${o.scaled ? `<div class="warm">🧠 الكميات معدّلة على هدفك (×${o.scaled.toFixed(2)})، حتى توصل ${targets().k} سعرة باليوم.</div>` : ''}
  <div class="card"><h3>مجموع الوجبة</h3>${macroRow(v, 1)}</div>
  <div class="card"><h3>المكونات وشكد بكل وحدة</h3>
   <div class="itab"><div class="ih"><span>المكوّن</span><span>بروتين</span><span>كارب</span><span>دهون</span><span>سعرة</span></div>
   ${o.it.map(([k, a]) => { const iv = itemVal(k, a), A = amt(k, a); return `<button class="ir" data-food="${k}">${fthumb(k, 40)}<span class="inm"><b>${FOODS[k].n}</b><small class="num">${A.g}${A.h ? ' • ' + A.h : ''}</small></span><span class="num">${r1(iv.p)}</span><span class="num">${r1(iv.c)}</span><span class="num">${r1(iv.f)}</span><span class="num">${Math.round(iv.k)}</span></button>`; }).join('')}
   <div class="ir tot"><span class="inm"><b>المجموع</b></span><span class="num">${r1(v.p)}</span><span class="num">${r1(v.c)}</span><span class="num">${r1(v.f)}</span><span class="num">${Math.round(v.k)}</span></div></div>
</div>
  <div class="card"><h3>شلون تسويها</h3><div class="steps sm">${o.prep.map(p => `<p>${p}</p>`).join('')}</div></div>
  <div class="card"><h3>تقييم NEXFIT</h3>${bar5('البروتين', sc.pro)}${bar5('السهولة', sc.ease)}${bar5('راحة القولون', sc.ibs)}<p class="xs mut">محسوب من مكونات الوجبة ووكتها.</p>
   <h3 style="margin-top:6px">تقييمك إنت للطعم</h3><div class="stars">${[1, 2, 3, 4, 5].map(i => `<button data-rate="${id}:${i}" class="${i <= my ? 'on' : ''}" aria-label="${i}">★</button>`).join('')}</div><p class="xs mut">${my ? (my >= 4 ? 'راح أطلعلك ياها أكثر 😋' : my <= 2 ? 'راح أقللها من قائمتك' : 'انحفظ تقييمك') : 'بعد ما تاكلها قيّمها، والقائمة تتعلم ذوقك.'}</p></div>
  <div class="card"><h3>شلون حسيت بطنك بعدها؟</h3><div class="row"><button class="btn ghost grow" data-fx="${id}:1">😌 ريّحتني</button><button class="btn ghost grow" data-fx="${id}:-1">😣 نفختني</button></div>${(S.fx || {})[id] < 0 ? '<p class="xs" style="color:var(--gold)">⚠ هاي نفختك قبل، فما راح تطلعلك بالقائمة.</p>' : ''}</div>
  <button class="btn wide" data-ateit="${id}:${sl[0]}">✓ أكلت هاي ${sl[1]} اليوم</button>
  <button class="btn wide ghost" data-userec="${id}:${sl[0]}">${cur ? 'هاي أكلتك اليوم ✓' : 'خليها ' + sl[1] + ' اليوم'}</button>`, true);
}
function openDB() {
  const q = fdQ.trim(), keys = Object.keys(FOODS).filter(k => q ? (FOODS[k].n + ' ' + FOODS[k].fi).toLowerCase().includes(q.toLowerCase()) : FOODS[k].cat === fdCat).sort((a, b) => FOODS[b].v[1] - FOODS[a].v[1]);
  const html = `<div class="row"><button class="ib" data-close aria-label="رجوع">${I.back}</button><h1 class="grow">الأطعمة والبذور</h1></div>
  <input class="field" id="fdq" type="search" placeholder="🔎 دوّر: دجاج، برتقال، شيا..." value="${esc(fdQ)}">
  ${q ? '' : `<div class="cats">${CATS.map(([k, n, ic]) => `<button class="${fdCat === k ? 'on' : ''}" data-fcat="${k}"><span>${ic}</span>${n}</button>`).join('')}<button class="${fdCat === 'fin' ? 'on' : ''}" data-fcat="fin"><span>🇫🇮</span>منتجات بيتك</button></div>`}
  ${!q && fdCat === 'fin' ? `<div class="pgrid">${Object.keys(INFO).map(k => { const f = FD[k], i = INFO[k]; return `<button class="pcard" data-prod="${k}"><span class="pimg"><img src="img/${f.img}.webp" alt="" loading="lazy"></span><b>${f.n}</b><span class="fi">${f.b || ''}</span><span class="badges"><i class="ok">حلال</i>${i.lac === 'yes' ? '<i class="no">لاكتوز</i>' : '<i class="ok">بدون لاكتوز</i>'}</span></button>`; }).join('')}</div>`
  : `<p class="xs mut">${keys.length} • مرتّبة من الأعلى بروتين. الأرقام للحصة العادية.</p><div class="col">${keys.map(k => { const f = FOODS[k], s = itemVal(k, f.srv); return `<button class="frow" data-food="${k}">${fthumb(k, 64)}<div class="grow"><b>${f.n}</b><span class="fi">${f.fi}</span>${f.ben ? `<span class="xs mut clamp">${f.ben}</span>` : ''}<span class="badges">${ibsB(f.ibs)}<i class="mid" style="background:var(--s2);color:var(--mut)">🗓 ${freqOf(k)}</i></span></div><div class="qty"><b class="num">${r1(s.p)}g</b><span>بروتين</span><span class="num">${Math.round(s.k)} سعرة</span><span>${f.sn || f.srv + ' غم'}</span></div></button>`; }).join('') || '<p class="mut">ما لگيت شي. جرّب كلمة ثانية.</p>'}</div>`}`;
  const s = $('#screen'); if (!s.hidden && s.querySelector('#fdq')) { s.innerHTML = `<div class="in keep">${html}</div>`; } else show(html);
}
function openDrinks() {
  const T = targets(), row = ([k, n, w], c) => `<div class="irow ${c}"><span class="pimg">${k && fimg(k) ? `<img src="${fimg(k)}" alt="">` : c === 'no' ? '⛔' : '🥤'}</span><div class="grow col" style="gap:4px"><b>${n}</b><span class="xs mut">${w}</span></div></div>`;
  show(`<div class="row"><button class="ib" data-close aria-label="رجوع">${I.back}</button><h1 class="grow">المشروبات</h1></div>
  <div class="card"><h2>💧 مي اليوم</h2><p class="sm">هدفك <b class="num">${Math.round(T.water * 4)}</b> گلاص. شربت <b class="num" style="color:var(--blue)">${(S.water || {})[today()] || 0}</b>.</p><button class="btn wide" data-water>💧 شربت گلاص</button></div>
  <h2>✓ اشربها</h2><div class="col">${DRINKS.good.map(x => row(x, 'ok')).join('')}</div>
  <h2>⚠ بكمية قليلة</h2><div class="col">${DRINKS.limit.map(x => row(x, 'mid')).join('')}</div>
  <h2 style="color:var(--red)">⛔ لا تشربها</h2><div class="col">${DRINKS.bad.map(x => row(x, 'no')).join('')}</div>`);
}
function openShop() {
  const need = {};
  for (let i = 0; i < 7; i++) { const d = new Date(); d.setDate(d.getDate() + i); SLOTS.forEach(([s]) => pickFor(s, dk(d)).it.forEach(([k, a]) => need[k] = (need[k] || 0) + a)); }
  const rows = Object.entries(need).sort((x, y) => CATS.findIndex(c => c[0] === FOODS[x[0]].cat) - CATS.findIndex(c => c[0] === FOODS[y[0]].cat));
  const wk = (k, a) => { const M = MEAS[k]; if (M && /بيضة|علبة|قنينة|موزة|حبة|برتقالة|طماطة|خيارة|جزرة|بطاطاية|ليمونة|فلفلة/.test(M[0])) return `${Math.ceil(a / M[1])} ${M[0]}`; return a >= 1000 ? `${r1(a / 1000)} كيلو` : `${Math.round(a / 10) * 10} غم`; };
  show(`<div class="row"><button class="ib" data-close aria-label="رجوع">${I.back}</button><h1 class="grow">سلة الأسبوع</h1></div>
  <p class="sm mut">محسوبة من أكلك للسبع أيام الجاية. اللحم والدجاج من محل حلال.</p>
  <div class="col">${rows.map(([k, a]) => { const f = FOODS[k]; return `<button class="frow" data-food="${k}">${fthumb(k, 56)}<div class="grow"><b>${f.n}</b><span class="fi">${f.fi}</span></div><div class="qty"><b class="num">${wk(k, a)}</b><span>بالأسبوع</span></div></button>`; }).join('')}</div>`);
}
function openFood(k) {
  const f = FOODS[k], s = itemVal(k, f.srv), v = f.v, inR = RECIPES.filter(r => r.it.some(x => x[0] === k)).slice(0, 10);
  const rr = (n, a, u = 'غم') => `<p><span>${n}</span><span class="num">${r1(a)} ${u}</span></p>`;
  show(`<div class="row"><button class="ib" data-back aria-label="رجوع">${I.back}</button><h2 class="grow">${f.n}</h2></div>
  <div class="prod big">${fimg(k) ? `<img src="${fimg(k)}" alt="">` : '<span style="font-size:80px">🍽</span>'}</div>
  <span class="fi" style="font-size:14px">${f.fi}</span>
  ${f.ben ? `<div class="feel">💡 <b>شنو يفيدك:</b> ${f.ben}</div>` : ''}
  <div class="warm">🗓 <b>شكد مرة:</b> ${freqOf(k)}</div>
  <div class="verd">${f.ibs === 'ok' ? '<div class="ok"><b>✓ يناسب القولون</b></div>' : f.ibs === 'limit' ? `<div class="mid"><b>⚠ للقولون: كمية قليلة</b><span>${f.note || ''}</span></div>` : `<div class="no"><b>✕ ينفخ القولون</b><span>${f.note || ''}</span></div>`}</div>
  <div class="card"><h3>بحصة ${f.sn || ''} (${f.srv} غم)</h3>${macroRow(s)}</div>
  <div class="card"><h3>بكل 100 غم</h3><div class="items">${rr('سعرات', v[0], 'سعرة')}${rr('بروتين', v[1])}${rr('كاربوهيدرات', v[2])}${rr('منها سكر', v[5])}${rr('دهون', v[3])}${rr('ألياف', v[4])}</div><p class="xs mut">${f.cat === 'market' ? 'من غلاف المنتج.' : 'من قاعدة القيم الغذائية الرسمية (USDA).'}</p></div>
  ${inR.length ? `<div class="card"><h3>وصفات بيها ${f.n}</h3><div class="hscroll">${inR.map(r => `<button class="mini" data-rec="${r.id}"><span class="mimg"><img src="${recImg(r)}" alt="" loading="lazy" class="${isCut(r) ? 'cut' : ''}"></span><b>${r.n}</b></button>`).join('')}</div></div>` : ''}`, true);
}
function openProd(k) {
  const f = FD[k], i = INFO[k], v = x => x == null ? '—' : AR(Math.round(x * 10) / 10);
  const row = (n, x, u = 'غم') => `<p><span>${n}</span><span class="num">${x == null ? '—' : v(x) + ' ' + u}</span></p>`;
  show(`<div class="row"><button class="ib" data-back aria-label="رجوع">${I.back}</button><h2 class="grow">${f.n}</h2></div>
  <div class="prod" style="height:240px"><img src="img/${f.img}.webp" alt="${esc(f.fi)}" style="max-height:220px"></div>
  <div><span class="fi" style="font-size:14px">${f.b || ''} • ${f.fi}</span>${f.shop ? `<p class="sm mut">🛒 ${f.shop}</p>` : ''}</div>
  <div class="verd"><div class="ok"><b>✓ حلال</b><span>ما بيه خنزير ولا جيلاتين</span></div>${i.lac === 'yes' ? '<div class="no"><b>✕ بيه لاكتوز</b><span>ينفخ القولون</span></div>' : `<div class="ok"><b>✓ ${i.lac === 'low' ? 'لاكتوز قليل كلش' : 'بدون لاكتوز'}</b><span>يناسب بطنك</span></div>`}<div class="${i.ibs === 'ok' ? 'ok' : 'mid'}"><b>${i.ibs === 'ok' ? '✓ يناسب القولون' : '⚠ للقولون: كمية قليلة'}</b><span>${i.ibsNote || 'ما ينفخ'}</span></div></div>
  <div class="card"><h3>القيم الغذائية لكل 100 غم</h3><div class="items">${row('سعرات', f.k, 'سعرة')}${row('بروتين', f.p)}${row('كاربوهيدرات', f.c)}${row('منها سكر', i.sug)}${row('دهون', f.f)}${row('منها دهون مشبعة', i.sat)}${row('ملح', i.salt)}</div><p class="xs mut">من غلاف المنتج.${f.raw ? ' القيم للوزن الني قبل الطبخ.' : ''}</p></div>
  <div class="card"><h3>المكونات</h3><p class="sm">${i.ing}</p>${i.fiIng ? `<span class="fi">${i.fiIng}</span>` : ''}</div>
  ${f.note ? `<div class="warn">${f.note}</div>` : ''}`, true);
}
/* ================= مدرّب التضخيم الذكي =================
   يقرا وزنك الأسبوعي: إذا ما يزيد يزيد سعراتك 150، وإذا يزيد بسرعة ينقص 100. هدف التضخيم النظيف 0.25-0.5 كغم بالأسبوع */
function trend() {
  const W = (S.weights || []).slice().sort((a, b) => a.d < b.d ? -1 : 1).filter(x => daysBetween(x.d, today()) <= 28);
  if (W.length < 2) return null; const d0 = W[0].d, xs = W.map(x => daysBetween(d0, x.d)), ys = W.map(x => x.w);
  const span = xs[xs.length - 1]; if (span < 6) return null;
  const mx = xs.reduce((a, b) => a + b) / xs.length, my = ys.reduce((a, b) => a + b) / ys.length;
  const sl = xs.reduce((a, x, i) => a + (x - mx) * (ys[i] - my), 0) / (xs.reduce((a, x) => a + (x - mx) ** 2, 0) || 1);
  return sl * 7;
}
function bellyAsk(sl) { const r = pickFor(sl); let o = $('.sheet'); if (o) o.remove(); o = document.createElement('div'); o.className = 'sheet'; o.innerHTML = `<div><b>صحة وعافية 😋 +8 نقاط</b><p class="xs mut">${r.n}: شلون بطنك بعدها؟ (يعلّم كاشف القولون)</p><div class="row"><button class="btn ghost grow" data-bel="${r.id}:1">😌 مرتاح</button><button class="btn ghost grow" data-bel="${r.id}:-1">😣 نفخني</button></div></div>`; document.body.append(o); setTimeout(() => o.remove(), 9000); }
function smartTick() {
  const r = trend(); S.adapt = S.adapt || { adj: 0, log: [] }; const A = S.adapt;
  if (r == null || (A.last && daysBetween(A.last, today()) < 7)) return;
  let ch = 0, why = '';
  if (r < .2) { ch = 150; why = `وزنك زاد ${r.toFixed(2)} كغم بالأسبوع، أقل من المطلوب. زدت سعراتك 150 (تقريباً سناك صغير).`; }
  else if (r > .6) { ch = -100; why = `وزنك يزيد ${r.toFixed(2)} كغم بالأسبوع، أسرع من اللازم وممكن دهون. نقّصت 100 سعرة.`; }
  else why = `وزنك يزيد ${r.toFixed(2)} كغم بالأسبوع: بالضبط مثل ما لازم. نكمّل نفس الشي 💪`;
  A.adj = Math.max(-300, Math.min(900, A.adj + ch)); A.last = today(); A.log.unshift({ d: today(), r: +r.toFixed(2), ch, why }); A.log = A.log.slice(0, 12); save();
}
function smartCard() {
  const A = S.adapt, r = trend(), T = targets();
  const last = A && A.log && A.log[0];
  return `<div class="smart"><div class="row"><span class="sico" style="background:rgba(255,45,61,.15);color:var(--g)">🧠</span><div class="grow"><b class="d">مدرّب التضخيم الذكي</b><p class="xs mut">${r == null ? 'سجّل وزنك مرة بالأسبوع (الصبح قبل الأكل)، وأنا أعدّل سعراتك لحالي' : `سرعتك: <b class="num" dir="ltr" style="color:${r < .2 ? 'var(--gold)' : r > .6 ? 'var(--red)' : '#34c759'}">${r >= 0 ? '+' : ''}${r.toFixed(2)}</b> كغم بالأسبوع • الهدف <span dir="ltr">0.25–0.5</span>`}</p></div><span class="pill g num">${T.k}</span></div>${last ? `<p class="sm">${last.why}</p>` : ''}</div>`;
}
/* الكميات تتعدل على هدفك: إذا هدفك أعلى من القائمة، نكبّر الحصص (مو البروتين الجاهز) */
let SCALE = 1;
function calcScale() { const T = targets(); const base = SLOTS.reduce((a, [k]) => a + optVal(pickFor(k)).k, 0); SCALE = base ? Math.max(.8, Math.min(1.45, T.k / base)) : 1; return SCALE; }
function forMe(o) {
  if (!o || Math.abs(SCALE - 1) < .04) return o;
  const it = o.it.map(([k, a]) => { if (/^m_|^whey$/.test(k)) return [k, a]; const M = MEAS[k]; let g = a * SCALE; if (M && /بيضة|موزة|برتقالة|حبة|تمرة|جزرة|طماطة|خيارة|ليمونة|بطاطاية|علبة/.test(M[0])) g = k === 'egg' || k === 'tuna' || /^m_/.test(k) ? Math.max(M[1], Math.round(g / M[1]) * M[1]) : Math.max(M[1] * .5, Math.round(g / M[1] * 2) / 2 * M[1]); else g = Math.max(5, Math.round(g / 5) * 5); return [k, g]; });
  return Object.assign({}, o, { it, scaled: SCALE });
}
/* ================= كاشف القولون: يتعلم شنو الأكل الي ينفخك إنت بالذات ================= */
let SUS = null;
function refreshSus() { SUS = new Set(); const D = ibsDetect(); SUS = new Set(D.sus.map(x => x.k)); }
function ibsDetect() {
  const ex = {}, add = (id, bad) => { const r = recById(id); if (!r) return; new Set(r.it.map(x => x[0])).forEach(k => { if (/olive_oil|rapeseed|water|lemon|mint|ginger/.test(k)) return; ex[k] = ex[k] || { b: 0, g: 0 }; ex[k][bad ? 'b' : 'g']++; }); };
  Object.entries(S.fx || {}).forEach(([id, v]) => add(id, v < 0));
  Object.entries(S.check || {}).forEach(([d, c]) => { const e = (S.eaten || {})[d] || {}; Object.keys(e).filter(k => e[k]).forEach(sl => add(pickFor(sl, d).id, c.belly >= 3)); });
  const sus = Object.entries(ex).filter(([, v]) => v.b + v.g >= 3 && (v.b + 1) / (v.b + v.g + 2) >= .6).sort((a, b) => b[1].b - a[1].b).map(([k, v]) => ({ k, ...v }));
  const safe = Object.entries(ex).filter(([, v]) => v.g >= 3 && v.b === 0).map(([k]) => k);
  const n = Object.keys(S.fx || {}).length + Object.keys(S.check || {}).length;
  return { sus, safe, n };
}
function ibsCard() {
  const D = ibsDetect();
  return `<div class="card"><h2>🔬 كاشف القولون</h2><p class="xs mut">كل ما تضغط 😌 أو 😣 بعد وجبة، أو تجاوب "بطنك اليوم"، أتعلم شنو الي ينفخك إنت بالذات. عندي هسه ${D.n} تسجيل${D.n < 6 ? '، أحتاج 6 على الأقل' : ''}.</p>
  ${D.sus.length ? `<h3 style="color:var(--red)">مشتبه بيهم</h3><div class="col">${D.sus.slice(0, 6).map(x => `<button class="frow" data-food="${x.k}">${fthumb(x.k, 46)}<div class="grow"><b>${FOODS[x.k].n}</b><span class="xs mut">نفخك ${x.b} مرات من ${x.b + x.g}</span></div></button>`).join('')}</div><p class="xs mut">هاي الأكلات تنشال من قائمتك لحالها. جرّبها مرة ثانية بعد شهر بكمية صغيرة.</p>` : '<p class="sm">لحد هسه ما لگيت شي مشتبه بيه 👍</p>'}
  ${D.safe.length ? `<h3 style="color:#34c759;margin-top:6px">آمنة إلك</h3><p class="sm">${D.safe.slice(0, 12).map(k => FOODS[k].n).join('، ')}</p>` : ''}</div>`;
}
/* ================= شنو عندي بالبيت؟ ================= */
let fridge = new Set();
function openFridge() {
  const groups = [['البروتين', ['egg', 'chicken', 'thigh', 'beef', 'mince', 'lamb', 'turkey', 'salmon', 'tuna', 'cod', 'shrimp', 'm_rahka', 'quark', 'greek', 'm_rae', 'cheese_e', 'feta', 'mozz', 'whey']], ['النشويات', ['rice', 'basmati', 'potato', 'sweetpot', 'oats', 'glutenfree_pasta', 'bread_gf', 'tortilla', 'quinoa', 'couscous', 'ricenoodle', 'bun']], ['الخضرة والفواكه', ['tomato', 'cucumber', 'pepper', 'carrot', 'spinach', 'lettuce', 'zucchini', 'broccoli', 'greenbean', 'banana', 'blueb', 'strawb', 'orange', 'kiwi', 'avocado']], ['غيرها', ['milk_lf', 'pb', 'tahini', 'maple', 'choc', 'cocoa', 'walnut', 'almond', 'chia', 'butter']]];
  const free = /olive_oil|rapeseed|water|lemon|mint|ginger|coffee|tea/;
  const res = fridge.size ? RECIPES.map(r => { const need = r.it.map(x => x[0]).filter(k => !free.test(k)), have = need.filter(k => fridge.has(k)); return { r, miss: need.filter(k => !fridge.has(k)), f: have.length / (need.length || 1) }; }).filter(x => x.f >= .6).sort((a, b) => a.miss.length - b.miss.length || b.f - a.f).slice(0, 25) : [];
  const html = `<div class="row"><button class="ib" data-close aria-label="رجوع">${I.back}</button><div class="grow"><h1>شنو عندي بالبيت؟</h1><p class="xs mut">اختار الي بثلاجتك، وأگلك شنو تگدر تطبخ هسه</p></div></div>
  ${groups.map(([n, ks]) => `<h3>${n}</h3><div class="fchips">${ks.filter(k => FOODS[k]).map(k => `<button class="${fridge.has(k) ? 'on' : ''}" data-fr="${k}">${fimg(k) ? `<img src="${fimg(k)}" alt="">` : ''}${FOODS[k].n}</button>`).join('')}</div>`).join('')}
  ${fridge.size ? `<div class="sec-h"><h2>تگدر تسوي ${res.filter(x => !x.miss.length).length} أكلة هسه</h2><button class="xs mut" style="background:none;border:0" data-frclear>امسح</button></div><div class="col">${res.map(({ r, miss }) => { const v = optVal(r); return `<button class="rrow" data-rec="${r.id}"><span class="rimg2"><img src="${recImg(r)}" alt="" loading="lazy" class="${isCut(r) ? 'cut' : ''}"></span><span class="grow col" style="gap:3px"><b>${r.n}</b><span class="xs" style="color:${miss.length ? 'var(--gold)' : '#34c759'}">${miss.length ? 'ناقصك: ' + miss.map(k => FOODS[k].n).join('، ') : '✓ عندك كل شي'}</span><span class="pmac num"><span><b style="color:var(--gold)">${Math.round(v.p)}g</b> بروتين</span><span>${Math.round(v.k)} سعرة</span></span></span></button>`; }).join('') || '<p class="mut sm">اختار أكثر حتى ألگى وصفات.</p>'}</div>` : ''}`;
  const s = $('#screen'); if (!s.hidden && s.querySelector('.fchips')) { const y = s.scrollTop; s.innerHTML = `<div class="in keep">${html}</div>`; s.scrollTop = y; } else show(html);
}
/* ================= برنامج الساعد (بالبيت، 6 دقايق) ================= */
const FORE = [['wristcurl', '3 × 15-20', 'كفك لفوگ، الحركة من الرسغ بس'], ['revcurl', '3 × 12-15', 'كفك لتحت، يقوّي ظهر الساعد'], ['farmer', '3 × 30-40 ثانية', 'امشي وانت ماسك أثقل دمبل تگدر عليه'], ['hang', '2 × لحد ما تتعب', 'تعلّگ بالعقلة: أقوى شي للقبضة']];
function openFore() {
  const L = S.fore || {}, days = Object.keys(L).sort(), wk = days.filter(d => daysBetween(d, today()) < 7).length, M = (S.meas || []).filter(m => m.fore), m0 = M[0], m1 = M[M.length - 1];
  show(`<div class="row"><button class="ib" data-close aria-label="رجوع">${I.back}</button><div class="grow"><h1>برنامج الساعد</h1><p class="xs mut">3 مرات بالأسبوع، بعد التمرين أو بالبيت. 6 دقايق بس</p></div></div>
  <div class="card fhero"><div class="row between"><div><span class="xs mut">هالأسبوع</span><h2 class="num">${wk} / 3</h2></div><div style="text-align:left"><span class="xs mut">ساعدك</span><h2 class="num">${m1 ? m1.fore + ' سم' : '—'}</h2>${m0 && m1 && m1 !== m0 ? `<span class="xs" style="color:#34c759">+${(m1.fore - m0.fore).toFixed(1)} سم من البداية</span>` : ''}</div></div><div class="bar"><i style="width:${Math.min(100, wk / 3 * 100)}%"></i></div></div>
  <div class="col">${FORE.filter(([id]) => EX[id]).map(([id, r, w], i) => `<button class="exrow" data-ex="${id}"><img src="img/ex3d/${id}.jpg" alt="" loading="lazy"><div class="grow"><h3>${i + 1}. ${EX[id].n}</h3><p class="sm num" style="color:var(--g)">${r}</p><p class="xs mut">${w}</p></div><span class="k">${I.play}</span></button>`).join('')}</div>
  <button class="btn wide ${L[today()] ? 'ghost' : ''}" data-foredone>${L[today()] ? '✓ سوّيته اليوم' : 'خلصت برنامج الساعد اليوم'}</button>
  <div class="card"><h3>قيس ساعدك (كل أسبوعين)</h3><p class="xs mut">بشريط خياطة على أعرض مكان تحت الكوع، وإيدك مشدودة.</p><div class="row"><input class="field num grow" id="foreIn" inputmode="decimal" placeholder="مثلاً 24.5"><button class="btn sm" data-foremeas>احفظ</button></div></div>
  <div class="card"><h3>ليش الساعد مهم؟</h3><div class="good sm col"><p>أول عضلة تبين بالتيشيرت نص كم</p><p>قبضة أقوى = ترفع أثقل بكل تمارين الظهر</p><p>عضلة صغيرة وترتاح بسرعة، فتتحمل تدريب أكثر من غيرها</p></div></div>`);
}
/* ================= رأس الصفحة وزر الإعدادات ================= */
const gearBtn = () => `<button class="ib" data-settings aria-label="الإعدادات">${I.gear}</button>`;
const head = (t, extra = '') => `<div class="row between"><h1>${t}</h1><div class="row" style="gap:8px">${extra}${gearBtn()}</div></div>`;
const nutTiles = n => `<div class="nut4"><div><b class="num">${AR(n.k)}</b><span>سعرة</span></div><div><b class="num" style="color:var(--gold)">${AR(n.p)}</b><span>بروتين غ</span></div><div><b class="num">${AR(n.c)}</b><span>كارب غ</span></div><div><b class="num">${AR(n.f)}</b><span>دهون غ</span></div></div>`;
const tags = ok => `<span class="badges">${ok.filter(([, t]) => !/حلال/.test(t)).map(([c, t]) => `<i class="${c}">${c === 'no' ? '✕ ' : c === 'mid' ? '⚠ ' : '✓ '}${t}</i>`).join('')}</span>`;

/* ================= المكملات ================= */
let suppCat = 'protein';
function vSupps() {
  const minor = +S.age && +S.age < 18;
  const card = (C, k) => { const x = C[k]; return `<button class="spc ${k}" data-sp="${C.id}:${k}"><span class="tag">${k === 'best' ? '🥇 الأفضل' : '🥈 البديل'}</span><span class="pi"><img src="img/supp/${x.img}.webp" alt="" loading="lazy"></span><b>${x.n}</b><small>${esc(x.b)}</small><span class="go">التفاصيل والشراء ‹</span></button>`; };
  return `${head('المكملات')}
  <button class="pcbtn" data-protcalc><span>🧮</span><div class="grow"><b>احسب بروتينك</b><small>اكتب وزنك وأگلك شكد تحتاج وشلون تقسمه باليوم</small></div>${I.chev}</button>
  <p class="sm mut" style="margin-top:-6px">لكل نوع اخترنا <b>الأفضل</b> حسب الدراسات والمدربين، و<b>بديل</b> إذا ما لگيته أو غالي. الجرعات محسوبة على جسمك.</p>
  ${minor ? '<div class="warn"><b>عمرك أقل من 18:</b> لا تاخذ كرياتين ولا بروتين قبل ما تسأل طبيب.</div>' : ''}
  ${SUPP2.map(C => `<section class="sps"><div class="sec-h"><h2>${C.ic} ${C.n}</h2>${C.must ? '<span class="pill g">أساسي</span>' : '<span class="pill">اختياري</span>'}</div>
   <div class="dz"><div><span>💊 شكد</span><b>${C.dose}</b></div><div><span>⏰ شوكت</span><b>${C.when}</b></div><div><span>📦 تكفيك</span><b>${C.last}</b></div><div class="mx"><span>⛔ الحد</span><b>${C.max}</b></div></div>
   <div class="pgrid">${card(C, 'best')}${card(C, 'alt')}</div>
   <details class="card stdy"><summary><b>📚 شنو تگول الدراسات</b></summary><p class="sm" style="margin-top:8px">${C.study}</p>${C.otc ? `<p class="xs" style="color:#34c759;margin-top:6px">✓ ${C.otc}</p>` : ''}</details></section>`).join('')}
  <p class="xs mut">تثقيف عام مو وصفة طبية. كل هاي ما تحتاج وصفة، بس إذا عندك مرض أو تاخذ دوا اسأل الصيدلي أو الطبيب.</p>`;
}
function openSp(cid, k) {
  const C = SUPP2.find(c => c.id === cid), x = C[k], o = C[k === 'best' ? 'alt' : 'best'];
  show(`<div class="row"><button class="ib" data-back aria-label="رجوع">${I.back}</button><div class="grow"><p class="xs mut">${C.n}</p><h2>${k === 'best' ? '🥇 الأفضل' : '🥈 البديل'}</h2></div></div>
  <div class="prod" style="height:260px"><img src="img/supp/${x.img}.webp" alt="${esc(x.b)}" style="max-height:240px"></div>
  <div><h1 style="font-size:24px">${x.n}</h1><span class="fi" style="font-size:13.5px">${esc(x.b)}</span><p class="sm" style="color:var(--g);margin-top:4px">${x.per}</p></div>
  <div class="card"><h3>ليش اخترناه</h3><div class="good sm col">${x.why.map(t => `<p>${t}</p>`).join('')}</div></div>
  <div class="card"><h3>منين تشتريه</h3><div class="buyrow">${x.stores.map(([n, u]) => `<a class="buy" href="${u}" target="_blank" rel="noopener"><span>🛒</span><b>${n}</b><i>↗</i></a>`).join('')}</div><p class="xs mut" style="margin-top:8px">قبل ما تشتري شوف تاريخ الانتهاء. الأسعار تتغير، فقارن بين المتاجر.</p></div>
  <div class="card"><h3>شلون تاخذه (محسوب على جسمك)</h3><div class="dz"><div><span>💊 شكد</span><b>${C.dose}</b></div><div><span>⏰ شوكت</span><b>${C.when}</b></div><div><span>📦 تكفيك</span><b>${C.last}</b></div><div class="mx"><span>⛔ الحد</span><b>${C.max}</b></div></div></div>
  <div class="card"><h3>📚 شنو تگول الدراسات</h3><p class="sm">${C.study}</p>${C.otc ? `<p class="xs" style="color:#34c759;margin-top:6px">✓ ${C.otc}</p>` : ''}</div>
  <button class="prow" data-sp="${C.id}:${k === 'best' ? 'alt' : 'best'}"><span class="pth" style="width:60px;height:60px"><img src="img/supp/${o.img}.webp" alt=""></span><div class="grow"><span class="xs mut">${k === 'best' ? 'إذا غالي أو ما لگيته، البديل:' : 'الأفضل:'}</span><b>${o.n}</b></div>${I.chev}</button>`, true);
}
function openSupp(cid, id) {
  const C = SUPP_LIB.find(c => c.id === cid), x = C.items.find(i => i.id === id), alts = C.items.filter(i => i.id !== id && !i.bad), daily = SUPPS.find(s => s.img === x.img.replace('supp/', ''));
  show(`<div class="row"><button class="ib" data-back aria-label="رجوع">${I.back}</button><div class="grow"><p class="xs mut">${C.n}</p><h2>${x.n}</h2></div></div>
  <div class="prod" style="height:250px"><img src="img/${x.img}.webp" alt="${esc(x.b)}" style="max-height:230px"></div>
  <div><span class="fi" style="font-size:14px">${esc(x.b)}</span>${x.where ? `<p class="sm mut">🛒 ${x.where}</p>` : ''}</div>
  ${x.best ? '<div class="pill g" style="align-self:flex-start">⭐ هذا الأفضل إلك</div>' : ''}
  ${x.buy ? `<div class="buyrow">${x.buy.map(([n, u]) => `<a class="buy" href="${u}" target="_blank" rel="noopener"><span>🛒</span><b>اشتريه من ${n}</b><i>↗</i></a>`).join('')}</div><p class="xs mut">روابط محلات فنلندية رسمية (تأكدت منها). قبل ما تشتري شوف تاريخ الانتهاء (Parasta ennen) على الصفحة أو العلبة.</p>` : ''}${x.bad ? '<div class="warn"><b>ما ننصحك بيه.</b> شوف السبب جوة.</div>' : ''}
  ${x.nut.k ? `<div class="card"><h3>بكل ${x.srv}</h3>${nutTiles(x.nut)}</div>` : `<div class="card"><h3>بكل ${x.srv}</h3><p class="sm mut">ما بيه سعرات ولا بروتين ولا دهون تُذكر.</p></div>`}
  <div class="card"><h3>إلك وحدك</h3>${tags(x.ok)}</div>
  <div class="card"><h3>شنو يفيدك</h3><div class="good sm col">${x.good.map(t => `<p>${t}</p>`).join('')}</div></div>
  <div class="feel">💪 <b>شكد يساعدك:</b> ${C.help}</div>
  ${daily ? `<div class="card"><h3>شلون تاخذه</h3><div class="kv"><div><span>شكد</span><b>${daily.dose}</b></div><div><span>وكت</span><b>${daily.when}</b></div><div><span>الحد</span><b>${daily.max}</b></div></div><div class="feel">⏳ <b>شوكت تحس بالفرق:</b> ${daily.feel}</div></div>` : ''}
  <div class="card"><h3>الطعم</h3><p class="sm">${x.taste}</p></div>
  ${alts.length ? `<div class="card"><h3>إذا ما عجبك، بدايله</h3><div class="col">${alts.map(a => `<button class="prow" data-supp="${C.id}:${a.id}"><span class="pth" style="width:60px;height:60px"><img src="img/${a.img}.webp" alt=""></span><div class="grow"><b>${a.n}</b><span class="xs mut">${a.good[0]}</span></div>${I.chev}</button>`).join('')}</div></div>` : ''}`, true);
}

/* ================= الممنوعات ================= */
const gOf = b => /جيلي|حلاوة|علكة|عرق السوس/.test(b.n) ? 'sweet' : /موس|پودينگ|جبن كريمي|حلاوة الپاشا/.test(b.n) ? 'dairy' : 'meat';
const BAN = BAN0.map(b => Object.assign({ g: gOf(b) }, b)).concat(BAN2);
let banG = 'all';
let banView = 'haram';
function vBan() {
  const seg = `<div class="seg"><button class="${banView === 'haram' ? 'on' : ''}" data-bv="haram">حرام</button><button class="${banView === 'ibs' ? 'on' : ''}" data-bv="ibs">ينفخ القولون</button><button class="${banView === 'words' ? 'on' : ''}" data-bv="words">اقرا الغلاف</button></div>`;
  let body = '';
  if (banView === 'haram') {
    const F = b => banG === 'all' || b.g === banG, sn = BAN.filter(b => b.sneaky && F(b)), rest = BAN.filter(b => !b.sneaky && F(b));
    const grid = L => `<div class="bgrid">${L.map(b => `<button class="bcard" data-ban="${BAN.indexOf(b)}"><span class="pimg"><img src="img/${b.img}.webp" alt="" loading="lazy"><i>✕</i></span><b>${b.n}</b><span class="xs mut">${b.why}</span><span class="fi">${b.fi}</span></button>`).join('')}</div>`;
    body = `<div class="danger"><span>${I.warn}</span><div><b>لا تشتري هاي المنتجات</b><p class="xs">كلها منتجات حقيقية بمحلات فنلندا، منها مستوردة من ألمانيا والدنمارك والسويد. تحت كل وحدة الكلمة المكتوبة بالمكونات.</p></div></div>
    <div class="chips">${[['all', 'الكل ' + BAN.length], ['meat', '🍕 أكل جاهز ولحوم'], ['sweet', '🍬 حلويات'], ['dairy', '🍮 ألبان وحلا']].map(([k, n]) => `<button class="${banG === k ? 'on' : ''}" data-bang="${k}">${n}</button>`).join('')}</div>
    ${sn.length ? '' : '<!-- -->'}<div class="sec-h"><h2>🕵️ الخنزير المخفي</h2><span class="xs mut num">${AR(sn.length)} منتج</span></div><p class="sm mut" style="margin-top:-8px">تشوفها وتگول عادية، بس جوّاها خنزير أو جيلاتين خنزير.</p>${grid(sn)}
    <div class="sec-h"><h2>🐖 خنزير أو جيلاتين بالمكونات</h2><span class="xs mut num">${AR(rest.length)} منتج</span></div>${grid(rest)}
    <div class="card"><h3>القاعدة الذهبية</h3><div class="good sm col"><p>اللحم والدجاج اشتريهم من المحلات العربية والتركية، مكتوب عليهم Halal</p><p>أي أكل جاهز (پيتزا، شوربة، سندويچ، كفتة) اقرا مكوناته قبل ما تشتري</p><p>أي حلاوة جيلي أو موس أو علكة: دوّر على كلمة liivate</p><p>الحلويات الحلال مكتوب عليها Halal أو "ilman liivatetta" يعني بدون جيلاتين</p></div></div>`;
  } else if (banView === 'ibs') {
    body = `${ibsCard()}<div class="danger mid"><span>🫃</span><div><b>هاي تنفخ القولون العصبي</b><p class="xs">مو حرام، بس قللها حتى بطنك يرتاح. وجرّب كل وحدة لحالها، لأن كل جسم يختلف.</p></div></div>
    <div class="col">${IBS_BAN.map(x => `<div class="irow"><span class="pimg"><img src="img/${x.img}.webp" alt="" loading="lazy"></span><div class="grow col" style="gap:4px"><b>${x.n}</b><span class="xs mut">${x.why}</span><span class="xs alt">↩ بداله: ${x.alt}</span></div></div>`).join('')}</div>
    <h2 style="color:#34c759">✓ هاي تريّح بطنك</h2><div class="bgrid">${IBS_GOOD.map(x => `<div class="bcard good"><span class="pimg"><img src="img/${x.img}.webp" alt="" loading="lazy"></span><b>${x.n}</b><span class="xs mut">${x.why}</span></div>`).join('')}</div>
    <div class="card"><h2>عادات تريّح بطنك</h2><div class="good sm col">${IBS.tips.map(t => `<p>${t}</p>`).join('')}</div></div>`;
  } else {
    body = `<div class="card"><h2>اقرا المكونات بثواني</h2><p class="sm mut">بالغلاف دوّر على كلمة <b class="fi" style="display:inline">Ainesosat</b> (يعني المكونات). إذا لگيت وحدة من هاي الكلمات، رجّع المنتج.</p></div>
    <div class="col">${BAN_WORDS.map(([w, m, c]) => `<div class="wrow ${c}"><span class="fi">${w}</span><b class="sm">${c === 'no' ? '⛔' : '⚠'} ${m}</b></div>`).join('')}</div>
    <div class="warn">⚠ يعني العلماء مختلفين عليه أو ممكن يكون نباتي. إذا تريد تحتاط، ابتعد عنه.</div>`;
  }
  return `${head(`<span style="color:var(--g)">⚠</span> الممنوعات`)}<button class="scanbtn" data-scan><span>📷</span><div class="grow"><b>افحص منتج بالكاميرا</b><small>وجّه على الباركود بالماركت ويگلك حلال لو لا، ويناسب القولون لو لا</small></div>${I.chev}</button>${(S.scans || []).length ? `<div class="hscroll">${S.scans.slice(0, 8).map(x => `<button class="chipscan ${x.r}" data-bc="${x.c}">${x.r === 'no' ? '⛔' : x.r === 'mid' ? '⚠' : '✓'} ${esc(x.n.slice(0, 18) || x.c)}</button>`).join('')}</div>` : ''}${seg}${body}`;
}
/* ================= فحص المنتج بالكاميرا (باركود) ================= */
/* ================= الماركت والفحص (باركود، صورة، بحث بالاسم، محلات العالم) ================= */
let mkP = null, mkFilter = 'all';
const mk = () => mkP || (mkP = import('./market.js'));
const REG = R => Object.fromEntries(Object.entries(R).map(([k, v]) => [k, v.map(([p, m]) => [new RegExp(p, 'i'), m])]));
async function analyzeP(p) {
  const { RULES } = await mk(), C = REG(RULES);
  const ing = [p.ingredients_text_en, p.ingredients_text, p.ingredients_text_fi, p.ingredients_text_sv, p.ingredients_text_de, p.ingredients_text_fr].filter(Boolean).filter((x, i, a) => a.indexOf(x) === i).join(' • ');
  const blob = ing + ' ' + (p.ingredients_tags || []).map(t => t.split(':').pop().replace(/-/g, ' ')).join(' '), lbl = (p.labels_tags || []).join(' ');
  const hl = /halal/.test(lbl), uniq = a => [...new Set(a)];
  const h = uniq(C.haram.filter(([r]) => r.test(blob)).map(x => x[1]));
  let d = uniq(C.doubt.filter(([r]) => r.test(blob)).map(x => x[1]));
  if (h.some(x => /جيلاتين/.test(x))) d = d.filter(x => !/جيلاتين/.test(x));
  if (hl) d = d.filter(x => !/مذبوح|حيواني/.test(x));
  const i = uniq(C.ibs.filter(([r]) => r.test(blob)).map(x => x[1]));
  if (/\bmilk|lactose|maito|laktoosi|\blait\b|milch|乳|ミルク|우유|นม/i.test(blob) && !/laktoositon|lactose[- ]free|laktaasi/i.test(blob)) i.push('لاكتوز');
  return { ing, h, d, i, hl, v: h.length ? 'no' : d.length ? 'mid' : ing || blob.trim() ? 'ok' : 'unk' };
}
const VB = { no: ['⛔', 'حرام'], mid: ['⚠', 'مشكوك'], ok: ['✓', 'ما بيه حرام'], unk: ['?', 'مو معروف'] };
function productView(x, code) {
  const v = n => n == null || n === '' ? '—' : Math.round(n * 10) / 10, ibs = (x.i || []).length;
  const fit = ibs ? ['🟡', 'انتبه للقولون: بيه ' + x.i.join('، ')] : x.ing ? ['🟢', 'ما بيه أشياء معروفة تنفخ القولون'] : ['⚪', 'المكونات مو مكتوبة بالقاعدة'];
  return `<div class="row"><button class="ib" data-back aria-label="رجوع">${I.back}</button><h2 class="grow">${esc(x.n || 'منتج')}</h2></div>
  ${x.img ? `<div class="prod big"><img src="${String(x.img).replace('.400.jpg', '.full.jpg')}" onerror="this.src='${x.img}'" alt=""></div>` : ''}
  <span class="fi" style="font-size:14px">${esc(x.b || '')} ${esc(x.q || '')} ${code ? '• ' + code : ''}</span>
  <div class="card"><h3>بكل 100 غم</h3>${nutTiles({ k: v(x.k), p: v(x.p), c: v(x.cb), f: v(x.f) })}${x.p >= 10 ? '<p class="xs" style="color:var(--g)">💪 بروتين عالي، يفيدك بالتضخيم</p>' : ''}</div>
  <div class="fitbig"><span>${fit[0]}</span><b>${fit[1]}</b></div>
  ${x.ing ? `<details class="card"><summary class="sm">المكونات كما مكتوبة</summary><p class="fi" style="font-size:13px;line-height:1.7;margin-top:8px">${esc(x.ing.slice(0, 1400))}</p></details>` : ''}
  <button class="btn ghost wide" data-scan>📷 افحص منتج ثاني</button>`;
}
function vScan() {
  const sc = (S.scans || []).slice(0, 10);
  return `${head('الماسح')}
  <button class="scanhero" data-scan><span class="ring">📷</span><b>افحص منتج</b><small>وجّه الكاميرا على الباركود، ويگلك شكد بيه بروتين وسعرات، ويناسب القولون لو لا</small></button>
  <div class="row"><label class="btn ghost grow" style="font-size:14px">🖼 صورة الباركود<input type="file" accept="image/*" capture="environment" id="bcImg" hidden></label><label class="btn ghost grow" style="font-size:14px">📄 صوّر المكونات<input type="file" accept="image/*" capture="environment" id="ingImg" hidden></label></div><button class="btn ghost wide" style="font-size:14px" data-bctype>⌨ اكتب رقم الباركود</button>
  <div class="card"><h3>🔎 دوّر على منتج بالاسم</h3><div class="row"><input class="field" id="mq" type="search" placeholder="مثلاً: Shin Ramyun، Pocky، Indomie"><button class="btn sm" data-msearch>دوّر</button></div><div id="mres"></div></div>
  <div class="sec-h"><h2>محلات العالم</h2><span class="xs mut">منتجات مفحوصة</span></div>
  <div class="stores">${(window.__STORES || []).map(([k, f, n, sub]) => `<button class="store" data-store="${k}"><span>${f}</span><b>${n}</b><small>${sub}</small></button>`).join('') || '<p class="xs mut">دا يحمّل...</p>'}</div>
  ${sc.length ? `<div class="sec-h"><h2>آخر الي فحصته</h2></div><div class="slist">${sc.map(x => `<button class="slot ex" data-bc="${x.c}"><span class="sico">🔎</span><span class="stxt"><b>${esc(x.n || x.c)}</b><span class="xs mut">${x.t}</span></span>${I.chev}</button>`).join('')}</div>` : ''}`;
}
mk().then(m => { window.__STORES = m.STORES; if (location.hash === '#scan') reroute(); });
async function openStore(k) {
  const { MARKET, STORES } = await mk(), st = STORES.find(s => s[0] === k), all = MARKET[k] || [];
  const L = all.filter(x => mkFilter === 'all' || x.v === mkFilter || (mkFilter === 'pro' && x.p >= 8 && x.v === 'ok'));
  const cnt = v => all.filter(x => x.v === v).length;
  const html = `<div class="row"><button class="ib" data-close aria-label="رجوع">${I.back}</button><div class="grow"><h1>${st[1]} ${st[2]}</h1><p class="xs mut">${all.length} منتج مفحوص • ${st[3]}</p></div></div>
  <div class="chips">${[['all', 'الكل'], ['pro', '💪 بروتين عالي']].map(([f, n]) => `<button class="${mkFilter === f ? 'on' : ''}" data-mkf="${f}:${k}">${n}</button>`).join('')}</div>
  <div class="mgrid2">${L.map(x => `<button class="mcard" data-mitem="${k}:${all.indexOf(x)}"><span class="pimg"><img src="${x.img}" alt="" loading="lazy"></span><b>${esc(x.n)}</b><span class="xs mut">${esc(x.b)}</span><span class="xs">${x.p != null ? `<b class="num" style="color:var(--g)">${x.p}g</b> بروتين • ${x.k != null ? x.k + ' سعرة' : ''}` : ''}</span></button>`).join('') || '<p class="mut">ماكو منتجات بهالفلتر.</p>'}</div>`;
  const s = $('#screen'); if (!s.hidden && s.querySelector('.mgrid2')) { const y = s.scrollTop; s.innerHTML = `<div class="in keep">${html}</div>`; s.scrollTop = y; } else show(html);
}
async function openMItem(k, i) { const { MARKET } = await mk(); const x = MARKET[k][i]; show(productView(x, x.c), true); }
async function nameSearch() {
  const q = ($('#mq') || {}).value?.trim(); if (!q) return; const box = $('#mres'); box.innerHTML = '<p class="xs mut">دا أدوّر...</p>';
  const { MARKET } = await mk(), loc = Object.entries(MARKET).flatMap(([k, L]) => L.map((x, i) => [k, i, x])).filter(([, , x]) => (x.n + ' ' + x.b).toLowerCase().includes(q.toLowerCase())).slice(0, 12);
  let on = [];
  const qs = { search_terms: q, page_size: 15, fields: 'code,product_name,brands,image_front_url' };
  const cg = 'https://world.openfoodfacts.org/cgi/search.pl?' + new URLSearchParams(Object.assign({ search_simple: 1, json: 1, action: 'process' }, qs)); for (const u of [cg, cg, cg]) {  try { const r = await fetch(u); if (!r.ok) { await new Promise(z => setTimeout(z, 1500)); continue; } on = ((await r.json()).products || []).filter(h => h.product_name && h.code); if (on.length) break; } catch (e) {} }
  box.innerHTML = (loc.length || on.length) ? `<div class="slist" style="margin-top:10px">${loc.map(([k, i, x]) => `<button class="slot ex" data-mitem="${k}:${i}"><span class="sico">🛒</span><span class="stxt"><b>${esc(x.n)}</b><span class="xs mut">${esc(x.b)}${x.p != null ? ' • ' + x.p + 'g بروتين' : ''}</span></span>${I.chev}</button>`).join('')}${on.map(h => `<button class="slot ex" data-bc="${h.code}">${h.image_front_url ? `<img src="${h.image_front_url}" alt="" style="width:46px;height:46px;object-fit:contain;background:#fff;border-radius:12px">` : '<span class="sico">🔎</span>'}<span class="stxt"><b>${esc(h.product_name)}</b><span class="xs mut">${esc([].concat(h.brands || []).join(', '))} • اضغط حتى أفحصه</span></span>${I.chev}</button>`).join('')}</div>` : '<p class="xs mut">ما لگيت شي. جرّب اسم ثاني أو صوّر الباركود.</p>';
}
async function decodeImage(file) {
  toast('دا أقرا الصورة...');
  try { const ZX = await loadZX(), r = new ZX.BrowserMultiFormatReader(), u = URL.createObjectURL(file); const res = await r.decodeFromImageUrl(u); URL.revokeObjectURL(u); lookupBC(res.getText()); }
  catch (e) { toast('ما گدرت أقرا الباركود. صوّره قريب وواضح'); }
}
let zxP = null, zxR = null, camS = null, ocrP = null;
const loadZX = () => zxP || (zxP = new Promise((res, rej) => { const s = document.createElement('script'); s.src = 'vendor/zxing.min.js'; s.onload = () => res(window.ZXing); s.onerror = rej; document.head.append(s); }));
function stopScan() { try { zxR && zxR.reset(); } catch (e) {} zxR = null; try { camS && camS.getTracks().forEach(t => t.stop()); } catch (e) {} camS = null; }
/* الكاميرا: نفتحها بنفسنا (أوضح دقة وأسرع)، وكل مرة ترجع للشاشة تنفتح من جديد */
async function startCam() {
  const v = $('#scv'), m = $('#scmsg'); if (!v) return; stopScan();
  try {
    const ZX = await loadZX();
    camS = await navigator.mediaDevices.getUserMedia({ audio: false, video: { facingMode: { ideal: 'environment' }, width: { ideal: 1920 }, height: { ideal: 1080 } } });
    if (!$('#scv')) { stopScan(); return; }
    const hints = new Map(); hints.set(ZX.DecodeHintType.POSSIBLE_FORMATS, [ZX.BarcodeFormat.EAN_13, ZX.BarcodeFormat.EAN_8, ZX.BarcodeFormat.UPC_A, ZX.BarcodeFormat.UPC_E, ZX.BarcodeFormat.CODE_128]); hints.set(ZX.DecodeHintType.TRY_HARDER, true);
    zxR = new ZX.BrowserMultiFormatReader(hints, 150);
    let last = '', n = 0;
    zxR.decodeFromStream(camS, v, r => { if (!r) return; const t = r.getText(); n = t === last ? n + 1 : 1; last = t; if (n >= 2 || t.length >= 12) { try { navigator.vibrate && navigator.vibrate(60); } catch (e) {} stopScan(); lookupBC(t); } });
    if (m) m.textContent = 'قرّب الباركود لحد ما يملا الخط الأحمر';
  } catch (e) { if (m) m.textContent = 'ما گدرت أفتح الكاميرا. من إعدادات الآيفون ← سفاري ← الكاميرا ← سماح. أو صوّر الباركود تحت.'; }
}
function openScan() {
  show(`<div class="row"><button class="ib" data-back aria-label="رجوع">${I.back}</button><h2 class="grow">افحص منتج</h2></div>
  <div class="scanbox"><video id="scv" playsinline muted autoplay></video><div class="scanline"></div><p id="scmsg">دا أفتح الكاميرا...</p></div>
  <div class="row"><label class="btn ghost grow" style="font-size:15px">🖼 صوّر الباركود<input type="file" accept="image/*" capture="environment" id="bcImg" hidden></label><label class="btn ghost grow" style="font-size:15px">📄 صوّر المكونات<input type="file" accept="image/*" capture="environment" id="ingImg" hidden></label></div>
  <div class="card"><h3>أو اكتب رقم الباركود</h3><div class="row"><input class="field num" id="bcIn" inputmode="numeric" placeholder="6408430043019" dir="ltr"><button class="btn sm" data-bcgo>افحص</button></div></div>
  <p class="xs mut">نفحص بقاعدة المنتجات العالمية (Open Food Facts). إذا المنتج مو بيها، صوّر المكونات وأنا أقراها.</p>`, true);
  startCam();
}
async function fetchOFF(code) {
  const C = [code]; if (code.length === 12) C.push('0' + code); if (code.length === 13 && code[0] === '0') C.push(code.slice(1)); if (code.length === 8) C.push(code.padStart(13, '0'));
  const F = 'product_name,product_name_en,product_name_fi,brands,image_front_url,ingredients_text,ingredients_text_fi,ingredients_text_en,ingredients_text_sv,ingredients_text_de,ingredients_text_fr,ingredients_tags,labels_tags,nutriments,quantity';
  for (const c of C) for (const host of ['world.openfoodfacts.org', 'fi.openfoodfacts.org']) {
    try { const r = await fetch(`https://${host}/api/v2/product/${c}?fields=${F}`); if (!r.ok) continue; const j = await r.json(); if (j.product && (j.product.product_name || j.product.product_name_fi || j.product.ingredients_text || j.product.ingredients_tags)) return j.product; } catch (e) {}
  }
  return null;
}
async function lookupBC(code) {
  code = String(code).replace(/\D/g, ''); if (code.length < 8) { toast('الرقم قصير'); return; }
  stopScan(); show(`<div class="row"><button class="ib" data-back aria-label="رجوع">${I.back}</button><h2>دا أفحص...</h2></div><div class="card"><p class="sm num">${code}</p><div class="bar"><i style="width:60%" class="loading"></i></div></div>`, true);
  const { MARKET } = await mk(), hit = Object.entries(MARKET).flatMap(([k, L]) => L.map((x, i) => [k, i, x])).find(([, , x]) => x.c === code);
  const p = await fetchOFF(code);
  if (!p) { if (hit) { openMItem(hit[0], hit[1]); return; } notFound(code); return; }
  const A = await analyzeP(p), n = p.nutriments || {};
  const x = { n: p.product_name_fi || p.product_name || p.product_name_en, b: [].concat(p.brands || []).join(', '), img: p.image_front_url || `https://public.keskofiles.com/f/k-ruoka/product/${code}?h=600`, q: p.quantity, v: A.v, h: A.h, d: A.d, i: A.i, hl: A.hl, k: n['energy-kcal_100g'], p: n.proteins_100g, cb: n.carbohydrates_100g, f: n.fat_100g, ing: A.ing };
  S.scans = [{ c: code, n: x.n || '', t: today(), r: x.v }].concat((S.scans || []).filter(z => z.c !== code)).slice(0, 30); save();
  const s = $('#screen'); s.innerHTML = `<div class="in">${productView(x, code)}${x.v === 'unk' || !x.ing ? ingBox(code) : ''}</div>`;
}
const ingBox = code => `<div class="card"><h3>📄 خلّيني أقرا المكونات بنفسي</h3><p class="xs mut">صوّر قائمة المكونات (Ainesosat / Ingredients) قريب وواضح، وأنا أقراها وأگلك يناسب القولون لو لا.</p><label class="btn wide">📷 صوّر المكونات<input type="file" accept="image/*" capture="environment" id="ingImg" data-code="${code || ''}" hidden></label><details style="margin-top:6px"><summary class="xs mut">أو الصق المكونات ككتابة</summary><textarea id="ingTxt" placeholder="sokeri, glukoosisiirappi, liivate..." style="margin-top:8px"></textarea><button class="btn ghost sm" data-ingtxt="${code || ''}">افحص الكتابة</button></details></div>`;
function notFound(code) {
  const s = $('#screen');
  s.innerHTML = `<div class="in"><div class="row"><button class="ib" data-back aria-label="رجوع">${I.back}</button><h2 class="grow">هذا المنتج مو بالقاعدة</h2></div>
  <div class="prod" style="height:200px"><img src="https://public.keskofiles.com/f/k-ruoka/product/${code}?h=600" alt="" style="max-height:180px" onerror="this.parentNode.style.display='none'"></div>
  <p class="sm">رقم <b class="num">${code}</b> ما مسجّل بقاعدة المنتجات العالمية لحد هسه (أغلب منتجات العلامات الخاصة مثل Pirkka وK-Menu وليدل الجديدة ما مسجلة). بس أگدر أفحصه من المكونات:</p>
  ${ingBox(code)}
  <button class="btn ghost wide" data-scan>📷 افحص منتج ثاني</button></div>`;
}
async function ocrIngredients(file, code) {
  const s = $('#screen'); s.hidden = false; const st = `<div class="row"><button class="ib" data-back aria-label="رجوع">${I.back}</button><h2>دا أقرا المكونات...</h2></div><div class="card"><p class="sm" id="ocrMsg">أول مرة تاخذ دقيقة لأن أنزّل قارئ الكتابة. بعدين تصير أسرع.</p><div class="bar"><i id="ocrBar" style="width:5%"></i></div></div>`;
  show(st, true);
  try {
    const T = await (ocrP || (ocrP = new Promise((res, rej) => { const sc = document.createElement('script'); sc.src = 'https://cdn.jsdelivr.net/npm/tesseract.js@5.1.1/dist/tesseract.min.js'; sc.onload = () => res(window.Tesseract); sc.onerror = rej; document.head.append(sc); })));
    const r = await T.recognize(file, 'fin+eng+swe', { logger: m => { const b = $('#ocrBar'); if (b && m.progress) b.style.width = Math.round(m.progress * 100) + '%'; const t = $('#ocrMsg'); if (t && m.status) t.textContent = m.status.includes('recogniz') ? 'دا أقرا الكتابة...' : 'دا أجهّز القارئ...'; } });
    checkText(r.data.text, code, true);
  } catch (e) { const t = $('#ocrMsg'); if (t) t.textContent = 'ما گدرت أقرا الصورة. صوّرها أقرب وبضو أحسن، أو الصق الكتابة.'; }
}
async function checkText(text, code, fromPhoto) {
  const A = await analyzeP({ ingredients_text: text });
  const x = { n: fromPhoto ? 'فحص من صورة المكونات' : 'فحص من الكتابة', b: '', img: code ? `https://public.keskofiles.com/f/k-ruoka/product/${code}?h=600` : '', i: A.i, ing: text };
  if (code) { S.scans = [{ c: code, n: 'منتج ' + code.slice(-4), t: today(), r: x.v }].concat((S.scans || []).filter(z => z.c !== code)).slice(0, 30); save(); }
  const s = $('#screen'); s.innerHTML = `<div class="in">${productView(x, code)}<p class="xs" style="color:var(--gold)">القراءة من الصورة ممكن تغلط بحرف. تأكد من المكونات تحت إذا الحكم مهم إلك.</p></div>`;
}
function openBan(i) {
  const b = BAN[i];
  show(`<div class="row"><button class="ib" data-back aria-label="رجوع">${I.back}</button><h2 class="grow">${b.n}</h2></div>
  <div class="prod" style="height:280px;position:relative"><img src="img/${b.img}.webp" alt="" style="max-height:260px"><span class="stamp">ممنوع</span></div>
  <div class="danger"><span>${I.warn}</span><div><b>ليش ممنوع؟</b><p class="sm">${b.why}</p></div></div>
  <div class="card"><h3>المكتوب بالمكونات</h3><span class="fi" style="font-size:18px">${b.fi}</span><p class="xs mut">${b.b}</p></div>`, true);
}

/* ================= أنا ================= */
const VERSION = '36';
function weightInfo() {
  const start = S.startW || (S.weights[0]?.w) || +S.w || 52, goal = +S.goal || 62, cur = curW();
  const ms = [start + 1, start + 3, start + 5, start + 7].filter(x => x < goal).concat([goal]).map(x => +x.toFixed(1));
  const W = S.weights.length ? S.weights : [{ d: S.month.start, w: start }];
  let rate = null; if (W.length >= 2) { const a = W[0], b = W[W.length - 1], dd = daysBetween(a.d, b.d); if (dd >= 6) rate = (b.w - a.w) / dd * 7; }
  return { start, goal, cur, ms, W, rate, pct: Math.max(0, Math.min(100, (cur - start) / (goal - start) * 100)) };
}
function vMe() {
  const wi = weightInfo(), bmi = curW() / Math.pow((+S.h || 168) / 100, 2), next = wi.ms.find(m => wi.cur < m);
  const nWork = S.hist.filter(h => h.t !== 'R').length, nSets = S.hist.reduce((a, h) => a + (h.sets || 0), 0);
  const bests = Object.entries(S.best).filter(([id, b]) => EX[id] && b.w).slice(0, 6);
  const C = 2 * Math.PI * 64, meas = S.meas || [], m0 = meas[0] || {}, m1 = meas[meas.length - 1] || {};
  const lvl = nWork >= 60 ? 'متقدّم' : nWork >= 20 ? 'متوسط' : 'مبتدئ';
  return `<div class="pro-head"><div class="ava big">${esc((S.name || 'ب')[0])}</div><div class="grow"><h1>${esc(S.name || 'يا بطل')}</h1><p class="sm mut">${S.age ? AR(S.age) + ' سنة • ' : ''}${AR(S.h)} سم • <span style="color:var(--g)">${lvl}</span></p></div>${gearBtn()}</div>
  <div class="card goal"><div class="gring"><svg viewBox="0 0 150 150"><circle cx="75" cy="75" r="64" style="stroke:var(--s3)" stroke-width="12" fill="none"/><circle cx="75" cy="75" r="64" stroke="var(--g)" stroke-width="12" fill="none" stroke-linecap="round" stroke-dasharray="${C}" stroke-dashoffset="${C * (1 - wi.pct / 100)}"/></svg><div><b class="num">${AR(wi.cur)}</b><span>كغم هسه</span></div></div>
   <div class="col" style="gap:6px"><span class="pill g num">${AR(Math.round(wi.pct))}٪ من هدفك</span><p class="sm">بديت بـ <b class="num">${AR(wi.start)}</b> كغم</p><p class="sm">هدفك <b class="num">${AR(wi.goal)}</b> كغم</p><p class="sm">${next ? `الهدف الجاي: <b class="num" style="color:var(--g)">${AR(next)}</b> كغم` : '<b style="color:var(--g)">وصلت هدفك! 🎉</b>'}</p></div></div>
  <div class="card"><h2>سجّل وزنك</h2><div class="wstep"><button class="ib" data-wstep="-0.1" aria-label="ناقص">−</button><input class="field num" id="wIn" inputmode="decimal" value="${curW()}" aria-label="وزنك"><button class="ib" data-wstep="0.1" aria-label="زايد">+</button></div><button class="btn wide" data-addw>احفظ وزن اليوم</button><p class="xs mut">مرة بالأسبوع، الصبح قبل الأكل وبعد الحمّام.</p></div>
  <div class="card"><h2>أهدافك</h2><div class="mpath">${[wi.start].concat(wi.ms).map((m, i) => { const reached = wi.cur >= m, d = i ? (S.reached || {})[m] : null; return `<div class="mstep ${reached ? 'on' : ''} ${m === next ? 'next' : ''}"><span class="dot">${reached ? I.check : AR(i)}</span><div><b class="num">${AR(m)} كغم</b><span class="xs mut">${i === 0 ? 'البداية' : i === wi.ms.length ? 'الهدف النهائي' : 'هدف ' + AR(i)}${d ? ' • وصلته ' + AR(d.slice(5).replace('-', '/')) : ''}</span></div></div>`; }).join('')}</div></div>
  <div class="tiles"><div class="tile"><span>زدت</span><b class="num" dir="ltr">${wi.cur - wi.start >= 0 ? '+' : ''}${AR(+(wi.cur - wi.start).toFixed(1))}</b><span>كغم من البداية</span></div><div class="tile"><span>سرعتك</span><b class="num" dir="ltr">${wi.rate == null ? '—' : (wi.rate >= 0 ? '+' : '') + AR(+wi.rate.toFixed(2))}</b><span>كغم بالأسبوع</span></div><div class="tile"><span>مؤشر الجسم</span><b class="num">${AR(bmi.toFixed(1))}</b><span>${bmi < 18.5 ? 'نحيف' : bmi < 25 ? 'طبيعي ✓' : 'زايد'}</span></div></div>
  ${wi.rate != null ? `<div class="${wi.rate < .15 ? 'warn' : 'card'}"><p class="sm">${wi.rate < .15 ? 'وزنك يزيد ببطء. زيد سناك ثاني (مثلاً الشيك بالبيت) أو كبّر الغدا شوية.' : wi.rate > .6 ? 'وزنك يزيد بسرعة، ممكن دهون. خفف الحلو شوية.' : 'ممتاز! وزنك يزيد بالسرعة الصحيحة 💪'}</p></div>` : ''}
  <div class="card"><div class="sec-h"><h2>صوري (قبل وبعد)</h2><label class="btn sm">📷 صورة<input type="file" accept="image/*" capture="user" id="photoIn" hidden></label></div><div id="photos" class="ph2"><p class="xs mut">صوّر نفسك كل أسبوعين بنفس المكان والضو. الصور تبقى بموبايلك بس.</p></div></div>
  <div class="card"><h2>وزنك بالرسم</h2><div class="chart">${chart(wi.W, wi.goal)}</div></div>
  <div class="tiles"><div class="tile">${I.dumb}<b class="num">${AR(nWork)}</b><span>تمرين خلصته</span></div><div class="tile">${I.bolt}<b class="num">${AR(nSets)}</b><span>سِت كلها</span></div><div class="tile">${I.fire}<b class="num">${AR(streak())}</b><span>أيام ورا بعض</span></div></div>
  <div class="card"><h2>قياسات جسمك (سم)</h2><p class="xs mut">بشريط خياطة كل أسبوعين. الزند وانت شادّه، والخصر على السرّة.</p>
   <div class="mgrid">${[['arm', 'الزند'], ['fore', 'الساعد'], ['chest', 'الصدر'], ['sh', 'الكتف'], ['waist', 'الخصر']].map(([k, n]) => { const d = m1[k] && m0[k] ? +(m1[k] - m0[k]).toFixed(1) : null; return `<label class="f">${n}${d ? ` <span style="color:${(k === 'waist' ? d < 0 : d > 0) ? 'var(--g)' : 'var(--gold)'}" dir="ltr">${d > 0 ? '+' : ''}${AR(d)}</span>` : ''}<input class="field num" inputmode="decimal" data-meas="${k}" value="${m1[k] || ''}" placeholder="—"></label>`; }).join('')}</div>
   <button class="btn ghost wide" data-savemeas>احفظ القياسات</button></div>
  ${bests.length ? `<div class="card"><h2>أرقامك القياسية</h2>${bests.map(([id, b]) => `<div class="row"><img src="img/ex3d/${id}.jpg" alt="" style="width:44px;height:44px;border-radius:12px;object-fit:cover"><span class="grow sm">${EX[id].n}</span><b class="num" style="color:var(--g)">${AR(b.w)} كغم × ${AR(b.r)}</b></div>`).join('')}</div>` : ''}
  <p class="xs mut" style="text-align:center">NEXFIT • النسخة ${VERSION} • بدون إعلانات • يتحدث لحاله</p>`;
}
/* ================= الإعدادات (مثل الآيفون) ================= */
const row = (ic, col, t, sub, attr, right = I.chev) => `<button class="srow" ${attr}><span class="sic" style="background:${col}">${ic}</span><span class="grow"><b>${t}</b>${sub ? `<small>${sub}</small>` : ''}</span><span class="sr">${right}</span></button>`;
const tgl = on => `<span class="tg ${on ? 'on' : ''}"><i></i></span>`;
function openSettings() {
  const th = S.theme || 'dark', hd = (S.health || {})[today()];
  show(`<div class="row"><button class="ib" data-close aria-label="رجوع">${I.back}</button><h1>الإعدادات</h1></div>
  <button class="sprof" data-profile><div class="ava big">${esc((S.name || 'ب')[0])}</div><div class="grow"><b>${esc(S.name || 'اكتب اسمك')}</b><small>${S.age ? AR(S.age) + ' سنة • ' : ''}${AR(S.h)} سم • هدفك ${AR(weightInfo().goal)} كغم</small></div>${I.chev}</button>
  <p class="sh">الكورس</p>
  <div class="sgrp">${row('🏋️', '#ff9500', 'كورسك: ' + progOf(S.month.pid).n, S.month.started ? 'اليوم ' + (curDay() + 1) + ' من ' + MDAYS : 'ما بديت بعد', 'data-pick')}
   ${row('📅', '#34c759', 'بديت الكورس اليوم', 'يرجّع العدّ ليوم 1', 'data-startc', '')}</div>
  <p class="sh">المظهر</p>
  <div class="sgrp"><div class="themes">${[['dark', 'غامق', I.moon], ['light', 'فاتح', I.sun], ['auto', 'تلقائي', '◐']].map(([k, n, ic]) => `<button class="${th === k ? 'on' : ''}" data-theme="${k}"><span class="tprev ${k}"><i></i><i></i></span>${n}</button>`).join('')}</div>
   ${row('✨', '#8e5cf7', 'حركة بين الخانات', 'حركة بسيطة لما تتنقل', 'data-anim', tgl(!S.noAnim))}</div>
  ${fontPicker()}
  <p class="sh">الصحة</p>
  <div class="sgrp">${row(I.watch, '#ff2d3d', 'ساعة أبل والصحة', hd ? `آخر قراءة اليوم: ${AR(hd.steps || 0)} خطوة` : 'اربط الخطوات والنبض بالتطبيق', 'data-health')}
   ${row('🩺', '#1aa260', 'قواعد صحتك', 'متى توگف التمرين وتروح للطبيب', 'data-rules')}</div>
  <p class="sh">التطبيق</p>
  <div class="sgrp">${row('⟳', '#2f80ed', 'حدّث التطبيق هسه', `النسخة ${VERSION} • يتحدث لحاله`, 'data-hardupdate', '')}
   ${row('⬇', '#5e6ad2', 'احفظ نسخة من معلوماتك', 'ملف ينحفظ بموبايلك', 'data-export')}
   <label class="srow"><span class="sic" style="background:#f2994a">⬆</span><span class="grow"><b>رجّع معلوماتك من ملف</b><small>إذا بدّلت الموبايل</small></span><input type="file" accept=".json,application/json" id="impIn" hidden><span class="sr">${I.chev}</span></label></div>
  <div class="sgrp">${row('🗑', '#eb5757', '<span style="color:var(--red)">امسح كل معلوماتي</span>', '', 'data-wipe', '')}</div>
  <p class="xs mut" style="text-align:center">NEXFIT • النسخة ${VERSION} • بدون إعلانات • معلوماتك بموبايلك بس</p>`);
}
function openProfile() {
  show(`<div class="row"><button class="ib" data-back aria-label="رجوع">${I.back}</button><h2>معلوماتك</h2></div>
  <div class="card"><label class="f">اسمك<input class="field" id="pN" value="${esc(S.name)}"></label><div class="row"><label class="f grow">عمرك<input class="field" id="pA" inputmode="numeric" value="${esc(S.age)}" placeholder="مثلاً 22"></label><label class="f grow">طولك (سم)<input class="field" id="pH" inputmode="numeric" value="${S.h}"></label></div>
  <div class="row"><label class="f grow">وزنك بالبداية<input class="field" id="pS" inputmode="decimal" value="${weightInfo().start}"></label><label class="f grow">هدفك (كغم)<input class="field" id="pG" inputmode="decimal" value="${weightInfo().goal}"></label></div><button class="btn wide" data-saveme>احفظ</button></div>`, true);
}
function openRules() {
  show(`<div class="row"><button class="ib" data-back aria-label="رجوع">${I.back}</button><h2>قواعد صحتك</h2></div>
  <div class="card"><div class="bad sm col"><p>وجع حاد بالمفصل: وگّف التمرين فوراً</p><p>دوخة أو وجع صدر أو ضيق نفس: وگّف وروح للطبيب</p><p>نبضك وانت مرتاح أعلى من 100 أكثر من يوم: راجع الطبيب</p></div></div>
  <div class="card"><div class="good sm col"><p>نام 7-9 ساعات، العضلة تكبر بالنوم</p><p>اشرب مي قبل وبعد التمرين</p><p>الوجع الخفيف بالعضل بعد يومين طبيعي</p></div></div>`, true);
}
/* ================= ساعة أبل والصحة =================
   تطبيق الويب ما يگدر يقرا الصحة مباشرة. الطريقة الحقيقية: اختصار بتطبيق "الاختصارات" يقرا الصحة وينسخ الأرقام، والتطبيق يلصقها. */
const HK = [['steps', 'خطوة اليوم', I.steps, '#ff2d3d'], ['kcal', 'سعرة حركة', I.fire, '#ff9f0a'], ['rhr', 'نبض الراحة', I.heart, '#ff375f'], ['sleep', 'ساعات نوم', I.moon, '#5e5ce6'], ['bp', 'ضغط الدم', '🩺', '#30b0c7']];
function parseHK(t) {
  const o = {}; String(t).replace(/[\u0660-\u0669]/g, d => d.charCodeAt(0) - 0x660).split(/[;\n,&|]+/).forEach(p => { const m = p.match(/^\s*(steps|kcal|rhr|sleep|bp|sys|dia|hr)\s*[=:]\s*([\d.\/]+)/i); if (m) o[m[1].toLowerCase()] = m[2]; });
  if (o.sys && o.dia) o.bp = o.sys + '/' + o.dia;
  const r = {}; ['steps', 'kcal', 'rhr', 'sleep'].forEach(k => { if (o[k] != null && !isNaN(+o[k])) r[k] = Math.round(+o[k] * (k === 'sleep' ? 10 : 1)) / (k === 'sleep' ? 10 : 1); }); if (o.bp && /^\d+\/\d+$/.test(o.bp)) r.bp = o.bp;
  return Object.keys(r).length ? r : null;
}
function saveHK(r) { S.health = S.health || {}; S.health[today()] = Object.assign({}, S.health[today()], r, { t: Date.now() }); save(); }
function rhrBase() { const v = Object.entries(S.health || {}).filter(([d, x]) => d !== today() && x.rhr).slice(-7).map(([, x]) => x.rhr); return v.length >= 3 ? v.reduce((a, b) => a + b, 0) / v.length : null; }
function healthCard() {
  const h = (S.health || {})[today()]; if (!h) return '';
  const b = rhrBase(), up = b && h.rhr && h.rhr - b >= 5;
  return `<button class="hcard" data-health><div class="hk">${HK.filter(([k]) => h[k] != null).slice(0, 4).map(([k, n, ic, c]) => `<div><span style="color:${c}">${ic}</span><b class="num">${AR(h[k])}</b><small>${n}</small></div>`).join('')}</div>${up ? '<p class="xs" style="color:var(--gold)">نبضك وانت مرتاح أعلى من عادتك. جسمك تعبان، خفّف اليوم.</p>' : ''}</button>`;
}
function openHealth() {
  const h = (S.health || {})[today()] || {};
  show(`<div class="row"><button class="ib" data-back aria-label="رجوع">${I.back}</button><h2>صحتك اليوم</h2></div>
  <div class="card"><div class="hk">${HK.map(([k, n, ic, c]) => `<div><span style="color:${c}">${ic}</span><b class="num">${h[k] != null ? h[k] : '—'}</b><small>${n}</small></div>`).join('')}</div></div>
  <div class="card"><h3>سجّل أرقامك (10 ثواني)</h3><p class="xs mut">افتح تطبيق "الصحة" أو الساعة، شوف الرقم، واكتبه هنا. المدرّب يستعملها حتى يعدّل تمرينك.</p>
   <div class="mgrid">${[['steps', 'خطوات اليوم'], ['rhr', 'نبض الراحة'], ['sleep', 'ساعات النوم'], ['kcal', 'سعرات الحركة']].map(([k, n]) => `<label class="f">${n}<input class="field num" inputmode="decimal" data-hk="${k}" value="${h[k] ?? ''}" placeholder="—"></label>`).join('')}</div>
   <label class="f">ضغط الدم (إذا عندك جهاز، مثلاً 120/80)<input class="field num" data-hk="bp" value="${h.bp || ''}" inputmode="text" placeholder="—"></label>
   <button class="btn wide" data-hksave>احفظ</button></div>
  <div class="card"><h3>شلون المدرّب يستعملها</h3><div class="good sm col"><p>نبض الراحة أعلى من عادتك بـ5 أو أكثر: يگلك خفّف التمرين اليوم</p><p>نمت أقل من 6 ساعات: يخفف الأوزان</p><p>الخطوات والسعرات تبين بالرئيسية</p></div></div>
  <div class="warn"><b>بصراحة:</b> ساعة أبل ما ترتبط مباشرة بتطبيق مثل NEXFIT، لأن أبل تسمح بهذا بس للتطبيقات المدفوعة بمتجرها. فالأسهل تكتب الأرقام بإيدك. وساعة أبل ما تقيس رقم ضغط الدم، بس تنبهك إذا تشك بضغط عالي.</div>
  <details class="card"><summary><b>للمتقدمين: ربط شبه تلقائي بالاختصارات</b></summary>
   <p class="xs mut" style="margin:8px 0">تطبيق "الاختصارات" بموبايلك يگدر يقرا أرقامك وينسخها، وانت تلصقها هنا بضغطة.</p>
   <button class="btn ghost wide" data-hkpaste>${I.watch} الصق الأرقام المنسوخة</button>
   <div class="steps sm" style="margin-top:12px"><p>افتح تطبيق الاختصارات واضغط + وسمّيه NEXFIT</p><p>أضف إجراء "العثور على عينات الصحة": النوع الخطوات، التاريخ اليوم. وبعده "حساب الإحصائيات": المجموع</p><p>كرّرها للطاقة النشطة (المجموع)، ولنبض الراحة (آخر وحدة)</p><p>أضف إجراء "نص" واكتب بيه السطر الي تحت، وبدّل كل كلمة بين قوسين بالرقم من الخطوة الي فوگها</p><p>آخر شي أضف "نسخ إلى الحافظة"، وشغّله، وارجع اضغط الزر الي فوگ</p></div>
   <div class="code" dir="ltr">steps=[الخطوات];kcal=[الطاقة];rhr=[النبض]</div></details>`, true);
}
/* ================= اهتزاز خفيف مثل التطبيقات ================= */
const hapEl = (() => { try { const l = document.createElement('label'); l.style.cssText = 'position:fixed;left:-99px;top:0;opacity:0;pointer-events:none'; const i = document.createElement('input'); i.type = 'checkbox'; i.setAttribute('switch', ''); l.append(i); document.body.append(l); return l; } catch (e) { return null; } })();
function haptic(ms = 8) { try { if (navigator.vibrate) navigator.vibrate(ms); else if (hapEl) hapEl.click(); } catch (e) {} }

/* ================= حاسبة البروتين =================
   الدراسات (ISSN 2017، Morton 2018): للي يتمرن 1.6 لحد 2.2 غم لكل كيلو. الجسم يستفاد أحسن إذا توزّعه على 4-5 وجبات، كل وجبة تقريباً 0.4 غم لكل كيلو.
   للقولون: لا تاخذ أكثر من 30 غم بالمرة الوحدة، والسكوب يتقسم نصين إذا ينفخك. */
let PC = null;
function openProtCalc() {
  PC = PC || { w: +curW() || 52, g: 'bulk', ibs: true, n: 4 };
  show(`<div class="row"><button class="ib" data-back aria-label="رجوع">${I.back}</button><div class="grow"><h2>🧮 حاسبة البروتين</h2><p class="xs mut">اكتب وزنك وأگلك شكد تحتاج وشلون تقسمه</p></div></div><div id="pcOut">${protBody()}</div>`, true);
}
function protBody() {
  const { w, g, ibs, n } = PC, F = { bulk: [2.0, 'تضخيم (تكبير عضل)'], keep: [1.6, 'ثبات (تحافظ على عضلك)'], cut: [2.2, 'تنشيف (تنزل دهون وتحافظ على العضل)'] }, f = F[g][0];
  const tot = Math.round(w * f), lo = Math.round(w * 1.6), hi = Math.round(w * 2.2), cap = ibs ? 30 : 40;
  const meals = n === 3 ? [['🍳', 'الريوق', '8 الصبح'], ['🍛', 'الغدا', '2 الظهر'], ['🥗', 'العشا', '8 بالليل']] : n === 4 ? [['🍳', 'الريوق', '8 الصبح'], ['🍛', 'الغدا', '1 الظهر'], ['🥤', 'العصرونية / بعد التمرين', '5 العصر'], ['🥗', 'العشا', '9 بالليل']] : [['🍳', 'الريوق', '8 الصبح'], ['🥣', 'سناك الضحى', '11 الضحى'], ['🍛', 'الغدا', '2 الظهر'], ['🥤', 'بعد التمرين', '5 العصر'], ['🥗', 'العشا', '9 بالليل']];
  let per = Math.round(tot / n); if (per > cap) per = cap;
  const shake = Math.min(25, Math.round(tot * .25)), food = tot - shake, rows = meals.map((m, i) => { const p = i === meals.length - 2 && n > 3 ? Math.min(per, cap) : per; return [m, p]; });
  const sum = rows.reduce((a, x) => a + x[1], 0), short = Math.max(0, tot - sum);
  const EQ = [['صدر دجاج مطبوخ', 100, 31], ['بيضة كبيرة', 1, 6, 'حبة'], ['رهكا (Rahka) بدون لاكتوز', 250, 25], ['تونة بالمي', 100, 25], ['سلمون', 100, 22], ['سكوب بروتين أيزوليت', 1, 25, 'سكوب'], ['حليب بدون لاكتوز', 250, 8, 'مل'], ['عدس مطبوخ', 150, 13]];
  return `<div class="card pcin"><label class="f">وزنك (كيلو)<input class="field num" id="pcW" type="number" inputmode="decimal" value="${w}" min="30" max="200"></label>
   <p class="xs mut" style="margin:10px 0 6px">هدفك</p><div class="chips">${Object.entries(F).map(([k, [, t]]) => `<button class="${g === k ? 'on' : ''}" data-pcg="${k}">${t}</button>`).join('')}</div>
   <p class="xs mut" style="margin:10px 0 6px">كم وجبة باليوم؟</p><div class="chips">${[3, 4, 5].map(k => `<button class="${n === k ? 'on' : ''}" data-pcn="${k}">${k} وجبات</button>`).join('')}</div>
   <label class="srow" style="margin-top:10px;padding:8px 0" data-pcibs><span class="sic" style="background:#34c759">🫃</span><span class="grow"><b>عندي قولون أو معدة حساسة</b><small>أقسم البروتين لكميات أصغر حتى ما ينفخك</small></span>${tgl(ibs)}</label></div>
  <div class="pcres"><small>جسمك يحتاج باليوم</small><b class="num" data-count="${tot}">${tot}</b><span>غرام بروتين</span><p class="xs">المدى الصحي إلك: ${lo} إلى ${hi} غم (يعني ${w} كيلو × 1.6 لحد 2.2)</p></div>
  ${scoopBox(tot)}
  <div class="card"><h3>📅 جدولك اليومي</h3><div class="pct">${rows.map(([[ic, nm, tm], p]) => `<div class="pcr"><span class="ic">${ic}</span><div class="grow"><b>${nm}</b><small>${tm}</small></div><b class="num g">${p} غم</b></div>`).join('')}
   ${short ? `<div class="pcr" style="opacity:.85"><span class="ic">🌙</span><div class="grow"><b>سناك قبل النوم</b><small>رهكا أو حليب</small></div><b class="num g">${short} غم</b></div>` : ''}</div>
   <p class="xs mut" style="margin-top:8px">المجموع: <b class="num">${tot}</b> غم. منها تقريباً <b class="num">${shake}</b> غم من سكوب البروتين، والباقي <b class="num">${food}</b> غم من الأكل.</p></div>
  ${ibs ? `<div class="card"><h3>🫃 للقولون والمعدة</h3><div class="good sm col"><p>لا تاخذ أكثر من <b>30 غم</b> بالمرة الوحدة. المعدة تهضم أريح لما الكمية أصغر.</p><p>إذا السكوب ينفخك: <b>قسمه نصين</b>، نص الصبح (12 غم) ونص العصر (12 غم).</p><p>خلّي البروتين <b>أيزوليت</b> (لاكتوز قليل) وبمي مو حليب.</p><p>اشرب البروتين على مهلك، مو مرة وحدة.</p><p>لا تاخذه على معدة فارغة كلش إذا يزعجك، خليه ويا أكلة خفيفة.</p></div></div>` : ''}
  <div class="card"><h3>🍗 شكد بروتين بالأكل؟</h3><div class="pct">${EQ.map(([n2, a, p, u]) => `<div class="pcr"><div class="grow"><b>${n2}</b><small class="num">${a} ${u || 'غم'}</small></div><b class="num g">${p} غم</b></div>`).join('')}</div></div>
  <p class="xs mut">المصدر: الجمعية الدولية للتغذية الرياضية (ISSN 2017) ودراسة مورتون 2018 الي جمعت 49 دراسة. تثقيف عام مو وصفة طبية.</p>`;
}

/* شكد سكوب آخذ اليوم؟ تعد الي أكلته بحركات بسيطة، والتطبيق يگلك */
const PQ = [['meat', '🍗', 'قطعة دجاج أو لحم أو سمك', 'بحجم كف إيدك', 25], ['tuna', '🐟', 'علبة تونة', '', 25], ['rahka', '🥣', 'علبة رهكا أو زبادي يوناني', '250 غم', 25], ['egg', '🥚', 'بيضة', '', 6], ['milk', '🥛', 'گلاص حليب', '250 مل', 8], ['cheese', '🧀', 'شريحتين جبن', '', 7], ['beans', '🫘', 'صحن عدس أو فاصوليا', '', 12], ['carb', '🍚', 'صحن تمن أو مكرونة أو خبزتين', '', 6]];
function scoopBox(tot) {
  const q = ((S.pq || {})[today()]) || {}, ate = PQ.reduce((a, [k, , , , g]) => a + (q[k] || 0) * g, 0), rem = Math.max(0, tot - ate);
  const sc = rem <= 8 ? 0 : rem <= 30 ? 1 : 2, after = Math.max(0, rem - sc * 25);
  const msg = ate === 0 ? `<b>ما سجلت أكل بعد.</b> إذا ما تعرف شكد أكلت: <b>خذ سكوب واحد بس</b>، هذا دائماً آمن.` : sc === 0 ? `<b>✓ ما تحتاج سكوب اليوم.</b> وصلت بروتينك من الأكل.` : sc === 1 ? `<b>خذ سكوب واحد</b> (25 غم)${after ? `، وباقيلك ${after} غم كمّلها بأكلة.` : '، وتكمل حاجتك بالضبط.'}` : `<b>خذ سكوبين</b> على مرتين (الصبح والعصر)، وباقيلك ${after} غم من الأكل.${after > 0 ? ' لا تزيد على سكوبين.' : ''}`;
  return `<div class="card sbx"><h3>🥄 شكد سكوب آخذ اليوم؟</h3><p class="xs mut">اضغط + على كل شي أكلته اليوم، والتطبيق يحسب لحاله.</p>
   <div class="pq">${PQ.map(([k, ic, n, sub, g]) => `<div class="pqr"><span class="ic">${ic}</span><div class="grow"><b>${n}</b><small>${sub ? sub + ' • ' : ''}${g} غم بروتين</small></div><button class="pqb" data-pq="${k}:-1" aria-label="ناقص">−</button><b class="num pqn">${q[k] || 0}</b><button class="pqb p" data-pq="${k}:1" aria-label="زايد">+</button></div>`).join('')}</div>
   <div class="sres"><div class="sbar"><i style="width:${Math.min(100, ate / tot * 100)}%"></i></div><p class="sm num">أكلت <b>${ate}</b> غم من <b>${tot}</b> • باقي <b>${rem}</b> غم</p><div class="scoops">${[0, 1].map(i => `<span class="${i < sc ? 'on' : ''}">🥄</span>`).join('')}</div><p class="sm">${msg}</p></div></div>`;
}
const pcRe = () => { const o = $('#pcOut'); if (o) { o.innerHTML = protBody(); countUp(o); } };
/* ================= الخط ================= */
const FONTS = [['vazir', 'وزير', 'Vazirmatn', ''], ['cairo', 'القاهرة', 'Cairo', 'Cairo:wght@400;500;600;700;800;900'], ['tajawal', 'تجوّل', 'Tajawal', 'Tajawal:wght@400;500;700;800;900'], ['plex', 'بلكس', 'IBM Plex Sans Arabic', 'IBM+Plex+Sans+Arabic:wght@400;500;600;700'], ['kufi', 'كوفي', 'Noto Kufi Arabic', 'Noto+Kufi+Arabic:wght@400;500;600;700;800;900'], ['almarai', 'المراعي', 'Almarai', 'Almarai:wght@400;700;800'], ['readex', 'ريدكس', 'Readex Pro', 'Readex+Pro:wght@400;500;600;700']];
function loadFont(k) { const f = FONTS.find(x => x[0] === k); if (f && f[3] && !document.querySelector(`link[data-f="${k}"]`)) { const l = document.createElement('link'); l.rel = 'stylesheet'; l.dataset.f = k; l.href = 'https://fonts.googleapis.com/css2?family=' + f[3] + '&display=swap'; document.head.append(l); } return f; }
function applyFont() { const f = loadFont(S.font || 'vazir') || FONTS[0], r = document.documentElement.style; r.setProperty('--fd', `'${f[2]}',system-ui,sans-serif`); r.setProperty('--fb', `'${f[2]}',system-ui,sans-serif`); r.setProperty('--z', S.fz || 1); }
applyFont();
function fontPicker() { FONTS.forEach(f => loadFont(f[0])); const cur = S.font || 'vazir', z = S.fz || 1;
  return `<p class="sh">الخط</p><div class="sgrp"><div class="fonts">${FONTS.map(([k, n, fam]) => `<button class="${cur === k ? 'on' : ''}" data-font="${k}" style="font-family:'${fam}',system-ui"><b>عاشت إيدك 💪</b><em>Bench Press 3×12</em><small>${n}</small></button>`).join('')}</div>
  <div class="fsz">${[[.92, 'صغير'], [1, 'عادي'], [1.1, 'كبير']].map(([v, n]) => `<button class="${z === v ? 'on' : ''}" data-fz="${v}">${n}</button>`).join('')}</div></div>`; }
/* ================= المظهر ================= */
function applyTheme() {
  const t = S.theme || 'dark', dark = t === 'auto' ? matchMedia('(prefers-color-scheme: dark)').matches : t === 'dark';
  document.documentElement.dataset.theme = dark ? 'dark' : 'light';
  document.documentElement.classList.toggle('noanim', !!S.noAnim);
  const m = document.querySelector('meta[name=theme-color]'); if (m) m.content = dark ? '#09090b' : '#f2f2f7';
}
applyTheme();
try { matchMedia('(prefers-color-scheme: dark)').addEventListener('change', () => { if (S.theme === 'auto') applyTheme(); }); } catch (e) {}
function confetti() { const cols = ['#ff2d3d', '#ffffff', '#c9cdd4', '#f5bd45']; return `<div class="conf" aria-hidden="true">${Array.from({ length: 40 }, (_, i) => `<i style="left:${(i * 37) % 100}%;background:${cols[i % 4]};animation-delay:${(i % 10) * .08}s;animation-duration:${1.6 + (i % 5) * .3}s;transform:rotate(${i * 23}deg)"></i>`).join('')}</div>`; }
/* ================= المدرّب اليومي ================= */
function coachMsg() {
  const c = (S.check || {})[today()], t = curDay() < MDAYS ? dayType(curDay()) : null, wi = weightInfo();
  const hk = (S.health || {})[today()], b = rhrBase();
  if (!c && !(hk && b && hk.rhr - b >= 5)) return null;
  const m = [];
  if (hk && b && hk.rhr - b >= 5 && t !== 'R') m.push('ساعتك تگول نبضك وانت مرتاح أعلى من عادتك بـ' + AR(Math.round(hk.rhr - b)) + '. جسمك ما ارتاح زين: خفّف الأوزان اليوم.');
  if (!c) return m;
  if (c.sleep < 6 || (hk && hk.sleep && hk.sleep < 6)) m.push('نمت قليل. خفّف الأوزان اليوم 10٪ وركّز على الحركة الصحيحة، ونام بدري الليلة.');
  if (c.sore >= 3 && t !== 'R') m.push('عضلاتك كلش موجوعة. سوّي إحماء أطول 10 دقايق، وإذا الوجع بالمفصل خليها راحة.');
  if (c.belly >= 3) m.push('بطنك منفوخ اليوم. كُل الوجبات الخفيفة (تمن، بطاطا، بيض)، وامشي 10 دقايق بعد الأكل، وابتعد عن الحليب والخبز اليوم.');
  if (c.energy >= 3 && c.sleep >= 7 && t !== 'R') m.push('طاقتك عالية ونومك زين! جرّب تزيد كيلو بالتمرين الأول اليوم 💪');
  if (!m.length) m.push(t === 'R' ? 'يوم راحة: امشي 30 دقيقة واشرب مي زين.' : 'كلشي تمام. التزم بالتمرين والأكل وانت على الطريق الصحيح.');
  if (wi.rate != null && wi.rate < .15) m.push('وزنك يزيد ببطء، زيد سناك ثاني اليوم.');
  return m;
}
function coachCard() {
  const c = (S.check || {})[today()], m = coachMsg();
  if (!c) return `<div class="coach"><div class="row"><span class="cav">${I.user}</span><div class="grow"><b class="d">مدرّبك يسأل</b><p class="xs mut">شلونك اليوم؟ 4 أسئلة بثواني حتى أعدّل يومك.</p></div></div><button class="btn wide sm" data-checkin>جاوب</button></div>`;
  return `<div class="coach"><div class="row"><span class="cav">${I.user}</span><b class="d grow">مدرّبك يگول</b><button class="xs mut" data-checkin style="background:none;border:0">عدّل</button></div><div class="good sm col">${m.map(x => `<p>${x}</p>`).join('')}</div></div>`;
}
const QS = [['sleep', 'شكد نمت البارحة؟', [[5, 'أقل من 6'], [6.5, '6-7 ساعات'], [8, '8 أو أكثر']]], ['energy', 'طاقتك اليوم؟', [[1, 'تعبان'], [2, 'عادي'], [3, 'نشيط']]], ['sore', 'وجع العضل؟', [[1, 'ماكو'], [2, 'خفيف'], [3, 'كلش']]], ['belly', 'بطنك (القولون)؟', [[1, 'مرتاح'], [2, 'شوية نفخة'], [3, 'منفوخ']]]];
let CK = {};
function openCheckin() {
  CK = Object.assign({}, (S.check || {})[today()] || {});
  show(`<div class="row"><button class="ib" data-close aria-label="رجوع">${I.back}</button><h2>شلونك اليوم؟</h2></div>
  ${QS.map(([k, q, opts]) => `<div class="card"><h3>${q}</h3><div class="chips">${opts.map(([v, l]) => `<button class="${CK[k] === v ? 'on' : ''}" data-ck="${k}:${v}">${l}</button>`).join('')}</div></div>`).join('')}
  <button class="btn wide" data-cksave>خلّي المدرّب يشوف</button>`);
}
/* ================= تبديل التمرين ================= */
function swapOpts(id) { const m = EX[id].m[0], e = EASY[id] && EX[EASY[id][0]] ? [EASY[id][0]] : []; return e.concat(Object.keys(EX).filter(k => k !== id && !e.includes(k) && EX[k].m[0] === m && !REST_DAY.includes(k))); }
/* ================= الصور (تنحفظ بالموبايل بس) ================= */
function idb() { return new Promise((res, rej) => { const r = indexedDB.open('coach-photos', 1); r.onupgradeneeded = () => r.result.createObjectStore('p', { keyPath: 'd' }); r.onsuccess = () => res(r.result); r.onerror = rej; }); }
async function savePhoto(file) { const db = await idb(); const tx = db.transaction('p', 'readwrite'); tx.objectStore('p').put({ d: today() + '-' + Date.now(), date: today(), blob: file }); return new Promise(r => tx.oncomplete = r); }
async function loadPhotos() { try { const db = await idb(); const all = await new Promise(r => { const q = db.transaction('p').objectStore('p').getAll(); q.onsuccess = () => r(q.result); }); const el = $('#photos'); if (!el || !all.length) return; const a = all[0], b = all[all.length - 1]; const u = x => URL.createObjectURL(x.blob); el.innerHTML = `<div class="ph2g"><figure><img src="${u(a)}" alt="أول صورة"><figcaption>${AR(a.date)}</figcaption></figure>${all.length > 1 ? `<figure><img src="${u(b)}" alt="آخر صورة"><figcaption>${AR(b.date)}</figcaption></figure>` : '<p class="xs mut">صوّر مرة ثانية بعد أسبوعين وتشوف الفرق جنب بعض.</p>'}</div><p class="xs mut">${AR(all.length)} صورة محفوظة</p>`; } catch (e) {} }
async function hardUpdate() { toast('دا أحدّث...'); try { const rs = await navigator.serviceWorker.getRegistrations(); for (const r of rs) await r.unregister(); const ks = await caches.keys(); for (const k of ks) await caches.delete(k); } catch (e) {} location.reload(); }
function chart(W, goal = 62) {
  const p = W.slice(-10), v = p.map(x => x.w).concat([goal]), lo = Math.floor(Math.min(...v) - 1), hi = Math.ceil(Math.max(...v) + 1), w = 320, h = 140, X = i => 34 + (p.length < 2 ? (w - 44) / 2 : i * (w - 44) / (p.length - 1)), Y = x => 12 + (hi - x) / (hi - lo) * (h - 24);
  let g = ''; for (let x = lo; x <= hi; x += Math.max(1, Math.round((hi - lo) / 4))) g += `<line x1="34" x2="${w - 6}" y1="${Y(x)}" y2="${Y(x)}" style="stroke:var(--line)"/><text x="28" y="${Y(x) + 4}" style="fill:var(--mut)" font-size="10" text-anchor="end">${x}</text>`;
  const ln = p.map((x, i) => `${X(i)},${Y(x.w)}`).join(' ');
  return `<svg viewBox="0 0 ${w} ${h}" role="img" aria-label="رسم وزنك">${g}<line x1="34" x2="${w - 6}" y1="${Y(goal)}" y2="${Y(goal)}" stroke="#ff2d3d" stroke-dasharray="4 4" opacity=".6"/><polyline points="${ln}" fill="none" stroke="#ff2d3d" stroke-width="3" stroke-linejoin="round"/>${p.map((x, i) => `<circle cx="${X(i)}" cy="${Y(x.w)}" r="4" fill="#ff2d3d"/>`).join('')}</svg>`;
}

/* ================= التنقل ================= */
const V = { home: vHome, course: vCourse, food: vFood, supps: vSupps, me: vMe };
const TABS = Object.keys(V); let lastTab = null;
function route() { if (SUS === null) refreshSus(); let h = location.hash.slice(1); if (h.startsWith('hk')) { const r = parseHK(decodeURIComponent(h.slice(3))); if (r) { saveHK(r); toast('وصلت أرقام الساعة ✓'); } history.replaceState(null, '', '#home'); h = 'home'; } if (!V[h]) h = 'home'; $('#app').innerHTML = V[h](); if (h === 'me') loadPhotos(); const a = $('#app'); a.classList.remove('fade', 'sl', 'sr'); if (lastTab !== h) { void a.offsetWidth; a.classList.add(lastTab == null ? 'fade' : TABS.indexOf(h) > TABS.indexOf(lastTab) ? 'sl' : 'sr'); if (lastTab != null && !S.noAnim) { const dx = TABS.indexOf(h) > TABS.indexOf(lastTab) ? -60 : 60; a.animate([{ opacity: 0, transform: `translateX(${dx}px) scale(.98)` }, { opacity: 1, transform: 'none' }], { duration: 420, easing: 'cubic-bezier(.22,1,.36,1)' }); } } lastTab = h; document.querySelectorAll('nav a').forEach(a => a.classList.toggle('on', a.dataset.t === h)); if (typeof countUp === 'function') countUp($('#app')); if (scrollMem && scrollMem[h] != null) { const y = scrollMem[h]; requestAnimationFrame(() => scrollTo(0, y)); } }
let stack = [], hdepth = 0, skipPops = 0, animating = false;
const RM = !!S.noAnim; // الحركة تشتغل دائماً، إلا إذا انت طفيتها من الإعدادات
const EASE = 'cubic-bezier(.22,1,.36,1)';
// حركة انتقال: الصفحة الجديدة تدخل من اليسار (عربي) والقديمة تطلع شوية لليمين وتغمق
function slideSwap(dir) { // dir: 1 دخول، -1 رجوع
  if (RM) return; const s = $('#screen'), cur = s.querySelector('.in'); if (!cur) return;
  cur.animate([{ transform: `translateX(${dir > 0 ? '-100%' : '30%'})`, opacity: dir > 0 ? 1 : .4 }, { transform: 'none', opacity: 1 }], { duration: 420, easing: EASE });
}
function ghost(dir) { // نسخة من الصفحة القديمة تتحرك وتختفي
  if (RM) return; const s = $('#screen'), cur = s.querySelector('.in'); if (!cur || s.hidden) return;
  const g = cur.cloneNode(true); g.classList.add('ghost'); g.style.top = (-s.scrollTop) + 'px'; s.appendChild(g);
  g.animate([{ transform: 'none', opacity: 1 }, { transform: `translateX(${dir > 0 ? '30%' : '-100%'})`, opacity: dir > 0 ? .3 : 1 }], { duration: 420, easing: EASE }).onfinish = () => g.remove();
}
function show(html, push) {
  const sh = $('.sheet'); if (sh) sh.remove(); const s = $('#screen'), wasOpen = !s.hidden && s.innerHTML;
  if (push && wasOpen) { ghost(1); stack.push({ h: s.querySelector('.in').innerHTML, y: s.scrollTop }); } else { killAnims(); stack = []; }
  if (!wasOpen) { history.pushState({ nx: 1 }, ''); hdepth = 1; } else if (push) { history.pushState({ nx: hdepth + 1 }, ''); hdepth++; }
  s.querySelectorAll('.in:not(.ghost)').forEach(x => x.remove());
  s.hidden = false; const d = document.createElement('div'); d.className = 'in'; d.innerHTML = html; s.prepend(d); s.scrollTop = 0; document.body.style.overflow = 'hidden';
  if (!wasOpen) { if (!RM) { s.animate([{ transform: 'translateX(-100%)' }, { transform: 'none' }], { duration: 440, easing: EASE }); $('#app').animate([{ transform: 'none', filter: 'brightness(1)' }, { transform: 'translateX(25%)', filter: 'brightness(.5)' }], { duration: 440, easing: EASE, fill: 'forwards' }); } }
  else if (push) slideSwap(1); else d.classList.add('pop');
}
function hideScreen(keep, animate = true) {
  const s = $('#screen'); stack = []; hdepth = 0;
  const done = () => { s.hidden = true; s.innerHTML = ''; s.style.transform = ''; $('#app').getAnimations().forEach(a => a.cancel()); if (!keep) { document.body.style.overflow = ''; route(); } };
  if (RM || !animate || s.hidden) { done(); return; }
  s.animate([{ transform: getComputedStyle(s).transform === 'none' ? 'none' : getComputedStyle(s).transform }, { transform: 'translateX(-100%)' }], { duration: 340, easing: EASE }).onfinish = done;
  $('#app').getAnimations().forEach(a => { a.cancel(); }); $('#app').animate([{ transform: 'translateX(25%)', filter: 'brightness(.5)' }, { transform: 'none', filter: 'brightness(1)' }], { duration: 340, easing: EASE });
}
function closeScreen(keep) { stopScan(); killAnims(); if (hdepth > 0 && !keep) { skipPops += hdepth; history.go(-hdepth); } hideScreen(keep); }
function doBack() {
  stopScan(); killAnims(); const s = $('#screen');
  if (stack.length) { ghost(-1); const p = stack.pop(); s.querySelectorAll('.in:not(.ghost)').forEach(x => x.remove()); const d = document.createElement('div'); d.className = 'in'; d.innerHTML = p.h; s.prepend(d); s.scrollTop = p.y || 0; slideSwap(-1); if ($('#scv')) startCam(); if (!$('#player').hidden) { s.hidden = true; renderPlayer(); } }
  else { const pl = !$('#player').hidden; hideScreen(pl); if (pl) renderPlayer(); }
}
function back() { if (hdepth > 0) history.back(); else doBack(); }
addEventListener('popstate', () => { if (skipPops > 0) { skipPops--; return; } const s = $('#screen'); if (!s.hidden && hdepth > 0) { hdepth--; doBack(); } });
// السحب من حافة الشاشة للرجوع (مثل الآيفون)
(() => {
  let x0 = 0, y0 = 0, t0 = 0, on = false, dx = 0, el = null;
  addEventListener('touchstart', e => { const s = $('#screen'); if (s.hidden) return; const t = e.touches[0], w = innerWidth; if (t.clientX > w - 30 || t.clientX < 30) { x0 = t.clientX; y0 = t.clientY; t0 = Date.now(); on = true; dx = 0; el = s.querySelector('.in:not(.ghost)'); } }, { passive: true });
  addEventListener('touchmove', e => { if (!on) return; const t = e.touches[0]; const d = (x0 > innerWidth / 2 ? x0 - t.clientX : t.clientX - x0); if (Math.abs(t.clientY - y0) > 40 && dx < 10) { on = false; return; } dx = Math.max(0, d); const dirX = x0 > innerWidth / 2 ? -1 : 1; const tgt = stack.length ? el : $('#screen'); tgt.style.transition = 'none'; tgt.style.transform = `translateX(${dirX * dx}px)`; tgt.style.opacity = 1 - dx / innerWidth * .4; }, { passive: true });
  addEventListener('touchend', () => { if (!on) return; on = false; const tgt = stack.length ? el : $('#screen'); const fast = dx > 60 && Date.now() - t0 < 260;
    if (dx > innerWidth * .33 || fast) { tgt.style.transition = ''; tgt.style.opacity = ''; if (stack.length) tgt.style.transform = ''; back(); }
    else { tgt.style.transition = 'transform .35s cubic-bezier(.22,1,.36,1), opacity .35s'; tgt.style.transform = ''; tgt.style.opacity = ''; } });
})();
window.addEventListener('hashchange', () => { const s = $('#screen'); if (!s.hidden) { stopScan(); killAnims(); stack = []; hdepth = 0; s.hidden = true; s.innerHTML = ''; $('#app').getAnimations().forEach(a => a.cancel()); document.body.style.overflow = ''; } route(); });
const reroute = () => { const y = scrollY; route(); scrollTo(0, y); };

document.addEventListener('click', e => {
  const b = e.target.closest('button,a'); if (!b) return; const d = b.dataset;
  if (d.day != null) { openDay(+d.day); return; }
  if (d.ex) { openEx(d.ex); return; }
  if (d.info) { killAnims(); $('#screen').hidden = false; stack = ['']; show(`<div class="row"><button class="ib" data-back aria-label="رجوع">${I.back}</button></div>${exInfo(d.info)}`, true); mountAnim($('#ac'), d.info, $('#aph')); return; }
  if ('close' in d) { closeScreen(); return; }
  if ('back' in d) { back(); return; }
  if (d.start != null) { startDay(+d.start); return; }
  if (d.skipday != null) { SES = null; S.month.done[+d.skipday] = today(); S.hist.push({ d: today(), t: dayType(+d.skipday), sets: 0, mus: [] }); save(); closeScreen(); toast('انحسب اليوم ✓'); return; }
  if ('pclose' in d) { killAnims(); clearInterval(restT); $('#player').hidden = true; $('#player').innerHTML = ''; SES = null; document.body.style.overflow = ''; route(); return; }
  if ('slow' in d) { const a = anims[anims.length - 1]; if (a) { const s = b.classList.toggle('on'); a.setSpeed(s ? .5 : 1); b.style.background = s ? 'var(--g)' : ''; b.style.color = s ? 'var(--ink)' : ''; } return; }
  if ('pnext' in d) { SES.k++; renderPlayer(); return; }
  if (d.pgo != null) { SES.k = +d.pgo; renderPlayer(); return; }
  if ('pfinish' in d) { finishDay(); return; }
  if (d.ok != null) { const s = SES.sets[SES.k][+d.ok]; s.ok = !s.ok; const left = SES.sets[SES.k].filter(x => !x.ok).length; const x = SES.items[SES.k]; if (s.ok && left && x.rest) rest(x.rest); if (s.ok && !left) toast('خلصت هذا التمرين 💪'); const a = anims[0]; renderPlayerSets(); return; }
  if (d.yt) { b.outerHTML = `<div class="video"><iframe src="https://www.youtube-nocookie.com/embed/${d.yt}?autoplay=1&playsinline=1&rel=0" title="فيديو شرح" referrerpolicy="strict-origin-when-cross-origin" allow="autoplay; encrypted-media; picture-in-picture; fullscreen" allowfullscreen></iframe></div>`; return; }
  if (d.eval != null) { openEval(); return; }
  if (d.weak) { b.classList.toggle('on'); const m = d.weak; EV.weak = EV.weak.includes(m) ? EV.weak.filter(x => x !== m) : [...EV.weak, m]; return; }
  if (d.feel) { document.querySelectorAll('[data-feel]').forEach(x => x.classList.toggle('on', x === b)); EV.feel = d.feel; return; }
  if ('evsubmit' in d) { submitEval(); return; }
  if (d.rec) { openRecipe(d.rec, d.slot); return; }
  if (d.food) { openFood(d.food); return; }
  if (d.fcat) { fdCat = d.fcat; openDB(); return; }
  if (d.sec) { openSection(d.sec, d.forslot); return; }
  if (d.font) { S.font = d.font; save(); applyFont(); document.querySelectorAll('[data-font]').forEach(x => x.classList.toggle('on', x === b)); haptic(); return; }
  if (d.fz) { S.fz = +d.fz; save(); applyFont(); document.querySelectorAll('[data-fz]').forEach(x => x.classList.toggle('on', x === b)); haptic(); return; }
  if (d.tk) { const t = today(); S.tk = S.tk || {}; S.tk[t] = S.tk[t] || {}; S.tk[t][d.tk] = !S.tk[t][d.tk]; save(); b.classList.toggle('on', S.tk[t][d.tk]); const n = $$('.td.on').length; const h = b.closest('.todo').previousElementSibling.querySelector('.num'); if (h) h.textContent = n + '/' + $$('.td').length; if (S.tk[t][d.tk]) haptic(14); return; }
  if ('startc' in d) { startCourse(); haptic(20); toast('يلا! اليوم أول يوم بالكورس 💪'); reroute(); return; }
  if (d.cshift) { startCourse(Math.max(0, curDay() + +d.cshift)); reroute(); return; }
  if (d.ateit) { const [id, sl] = d.ateit.split(':'), t = today(); S.mp = S.mp || {}; S.mp[t] = S.mp[t] || {}; S.mp[t][sl] = id; S.eaten = S.eaten || {}; S.eaten[t] = S.eaten[t] || {}; S.eaten[t][sl] = true; save(); haptic(14); toast('انسجلت ✓'); closeScreen(); return; }
  if (d.pq) { const [k, v] = d.pq.split(':'), t = today(); S.pq = S.pq || {}; S.pq[t] = S.pq[t] || {}; S.pq[t][k] = Math.max(0, (S.pq[t][k] || 0) + +v); save(); haptic(); const y = $('#screen').scrollTop; pcRe(); $('#screen').scrollTop = y; return; }
  if (d.pcg) { PC.g = d.pcg; pcRe(); return; }
  if (d.pcn) { PC.n = +d.pcn; pcRe(); return; }
  if ('pcibs' in d) { e.preventDefault(); PC.ibs = !PC.ibs; pcRe(); return; }
  if ('protcalc' in d) { openProtCalc(); return; }
  if (d.sp) { const [c, k] = d.sp.split(':'); openSp(c, k); return; }
  if (d.ytv) { b.outerHTML = vframe(d.ytv); return; }
  if (d.mus) { openMuscle(d.mus); return; }
  if (d.pday) { openPlanDay(d.pday); return; }
  if ('pick' in d) { openPick(); return; }
  if (d.progv) { openProg(d.progv); return; }
  if (d.setprog) { setProg(d.setprog); return; }
  if (d.goto) { location.hash = '#' + d.goto; return; }
  if ('drinks' in d) { openDrinks(); return; }
  if ('fdb' in d) { openDB(); return; }
  if ('shop' in d) { openShop(); return; }
  if (d.rate) { const [id, v] = d.rate.split(':'); S.rate = S.rate || {}; S.rate[id] = +v; save(); toast(+v >= 4 ? 'كفو، راح تطلعلك أكثر 😋' : 'انحفظ تقييمك'); openRecipe(id); stack.pop(); return; }
  if (d.swapm) { const t = today(); S.msw = S.msw || {}; S.msw[t] = S.msw[t] || {}; if (S.mp && S.mp[t]) delete S.mp[t][d.swapm]; let n = 0; do { S.msw[t][d.swapm] = (S.msw[t][d.swapm] || 0) + 1; n++; } while (n < 6 && (S.fx || {})[pickFor(d.swapm).id] < 0); save(); reroute(); toast('تبدّلت 🔄'); return; }
  if (false) { const t = today(); S.mp = S.mp || {}; S.mp[t] = S.mp[t] || {}; S.mp[t].l = 'g' + (Date.now() % 100000); save(); reroute(); toast('✨ أكلة جديدة للغدا'); return; }
  if (d.userec) { const [id, sl, sk] = d.userec.split(':'); const t = today(); S.mp = S.mp || {}; S.mp[t] = S.mp[t] || {}; S.mp[t][sl] = id; save(); toast('صارت أكلتك اليوم ✓'); if (sk) { openSection(sk, sl); $('#screen').scrollTop = 0; } else closeScreen(); return; }
  if (d.fx) { const [id, v] = d.fx.split(':'); S.fx = S.fx || {}; S.fx[id] = +v; save(); toast(+v > 0 ? 'كفو، نخليها بأكلك' : 'انحفظت، ما راح تطلعلك'); openRecipe(id, (recById(id) || {}).s); return; }
  if (d.took) { const t = today(); S.supp[t] = S.supp[t] || {}; S.supp[t][d.took] = !S.supp[t][d.took]; save(); reroute(); return; }
  if ('hideinstall' in d) { S.hideInstall = 1; save(); route(); return; }
  if ('addw' in d) { setTimeout(() => { const before = (S.adapt || {}).last; smartTick(); if ((S.adapt || {}).last !== before && S.adapt.log[0]) toast('🧠 ' + S.adapt.log[0].why.slice(0, 60) + '...'); }, 50); const v = +String($('#wIn').value).replace(',', '.'); if (!(v > 25 && v < 200)) { toast('اكتب وزن صحيح'); return; } const before = weightInfo(); const t = today(), x = S.weights.find(z => z.d === t); if (!S.startW) S.startW = before.start; if (x) x.w = v; else S.weights.push({ d: t, w: v }); S.reached = S.reached || {}; const hit = before.ms.filter(m => v >= m && !S.reached[m]); hit.forEach(m => S.reached[m] = t); save(); route(); if (hit.length) { const m = hit[hit.length - 1], i = before.ms.indexOf(m) + 1; show(`<div class="col" style="min-height:75vh;justify-content:center;align-items:center;text-align:center;gap:16px"><div class="medal" style="width:auto;padding:20px 28px"><span class="c" style="width:90px;height:90px">${I.trophy}</span></div><h1>${i === before.ms.length ? 'وصلت هدفك النهائي!' : 'وصلت الهدف ' + AR(i) + '!'}</h1><p class="mut">صار وزنك ${AR(v)} كغم. زدت ${AR(+(v - before.start).toFixed(1))} كغم من البداية 💪</p><button class="btn wide" data-close>كمّل</button></div>`); } else toast('انحفظ وزنك'); return; }
  if ('saveme' in d) { if (!$('#pN')) return; S.name = $('#pN').value.trim(); S.age = $('#pA').value; S.h = +$('#pH').value || 168; const st = +$('#pS').value, g = +$('#pG').value; if (st > 25) S.startW = st; if (g > 25) S.goal = g; save(); toast('انحفظ'); back(); return; }
  if ('settings' in d) { openSettings(); return; }
  if ('profile' in d) { openProfile(); return; }
  if ('rules' in d) { openRules(); return; }
  if ('health' in d) { openHealth(); return; }
  if (d.theme) { S.theme = d.theme; save(); applyTheme(); document.querySelectorAll('.themes button').forEach(x => x.classList.toggle('on', x === b)); return; }
  if ('anim' in d) { S.noAnim = !S.noAnim; save(); applyTheme(); b.querySelector('.tg').classList.toggle('on', !S.noAnim); return; }
  if ('export' in d) { const u = URL.createObjectURL(new Blob([JSON.stringify(S)], { type: 'application/json' })); const a = document.createElement('a'); a.href = u; a.download = 'nexfit-' + today() + '.json'; document.body.append(a); a.click(); a.remove(); setTimeout(() => URL.revokeObjectURL(u), 4000); toast('انحفظ الملف'); return; }
  if ('wipe' in d) { if (confirm('أكيد تريد تمسح كل معلوماتك؟ ما ترجع.')) { localStorage.removeItem(KEY); location.reload(); } return; }
  if ('hkpaste' in d) { (async () => { try { const t = await navigator.clipboard.readText(); const r = parseHK(t); if (!r) { toast('ما لگيت أرقام. شغّل الاختصار أول'); return; } saveHK(r); toast('وصلت أرقام الساعة ✓'); openHealth(); } catch (er) { toast('اسمح باللصق وجرّب مرة ثانية'); } })(); return; }
  if ('hksave' in d) { const r = {}; document.querySelectorAll('[data-hk]').forEach(x => { const v = x.value.trim(); if (!v) return; if (x.dataset.hk === 'bp') { if (/^\d+\/\d+$/.test(v)) r.bp = v; } else if (!isNaN(+v.replace(',', '.'))) r[x.dataset.hk] = +v.replace(',', '.'); }); if (!Object.keys(r).length) { toast('اكتب رقم واحد على الأقل'); return; } saveHK(r); toast('انحفظ ✓'); openHealth(); return; }
  if (d.scat) { suppCat = d.scat; reroute(); return; }
  if (d.supp) { const [c, i] = d.supp.split(':'); openSupp(c, i); return; }
  if (d.bv) { banView = d.bv; reroute(); return; }
  if (d.ban != null) { openBan(+d.ban); return; }
  if (d.bang) { banG = d.bang; reroute(); return; }
  if ('scan' in d) { openScan(); return; }
  if (d.store) { mkFilter = 'all'; openStore(d.store); return; }
  if (d.mkf) { const [f, k] = d.mkf.split(':'); mkFilter = f; openStore(k); return; }
  if (d.mitem) { const [k, i] = d.mitem.split(':'); openMItem(k, +i); return; }
  if ('msearch' in d) { nameSearch(); return; }
  if ('bctype' in d) { openScan(); setTimeout(() => { const i = $('#bcIn'); if (i) i.focus(); }, 300); return; }
  if ('banwords' in d) { banView = 'words'; closeScreen(true); location.hash = '#ban'; return; }
  if (d.ingtxt != null) { const t = ($('#ingTxt') || {}).value || ''; if (t.trim().length < 5) { toast('الصق المكونات أول'); return; } checkText(t, d.ingtxt, false); return; }
  if ('bcgo' in d) { lookupBC($('#bcIn').value); return; }
  if (d.bc) { lookupBC(d.bc); return; }
  if ('water' in d) { S.water = S.water || {}; S.water[today()] = (S.water[today()] || 0) + 1; save(); reroute(); toast('💧 كفو! كوب ' + AR(S.water[today()])); return; }
  if (d.bel) { const [id, v] = d.bel.split(':'); S.fx = S.fx || {}; S.fx[id] = +v; save(); refreshSus(); b.closest('.sheet').remove(); toast(+v > 0 ? 'كفو 👍' : 'انحفظت، ما راح تطلعلك هالأكلة'); if (+v < 0) reroute(); return; }
  if ('fridge' in d) { openFridge(); return; }
  if (d.fr) { fridge.has(d.fr) ? fridge.delete(d.fr) : fridge.add(d.fr); openFridge(); return; }
  if ('frclear' in d) { fridge.clear(); openFridge(); return; }
  if ('fore' in d) { openFore(); return; }
  if ('foredone' in d) { S.fore = S.fore || {}; S.fore[today()] = !S.fore[today()]; save(); toast(S.fore[today()] ? 'كفو! الساعد يكبر 💪' : 'انشال'); openFore(); return; }
  if ('foremeas' in d) { const v = +String($('#foreIn').value).replace(',', '.'); if (!(v > 10 && v < 60)) { toast('اكتب رقم صحيح بالسانتي'); return; } S.meas = S.meas || []; S.meas.push({ d: today(), fore: v }); save(); toast('انحفظ'); openFore(); return; }
  if (d.eat) { const t = today(); S.eaten = S.eaten || {}; S.eaten[t] = S.eaten[t] || {}; S.eaten[t][d.eat] = !S.eaten[t][d.eat]; save(); reroute(); if (S.eaten[t][d.eat]) bellyAsk(d.eat); if (false) toast('صحة وعافية 😋 +8 نقاط'); return; }
  if ('plan' in d) { showPlan = !showPlan; reroute(); return; }
  if ('checkin' in d) { openCheckin(); return; }
  if (d.ck) { const [k, v] = d.ck.split(':'); CK[k] = +v; b.parentNode.querySelectorAll('button').forEach(x => x.classList.toggle('on', x === b)); return; }
  if ('cksave' in d) { if (Object.keys(CK).length < 4) { toast('جاوب كل الأسئلة'); return; } S.check = S.check || {}; S.check[today()] = CK; save(); closeScreen(); return; }
  if (d.swap) { const alts = swapOpts(d.swap); if (!alts.length) { toast('ماكو بديل لهذا التمرين'); return; } killAnims(); show(`<div class="row"><button class="ib" data-back aria-label="رجوع">${I.back}</button><h2>صعبة أو الجهاز مشغول؟ بدّل بـ</h2></div><p class="sm mut">نفس العضلة، بتمرين ثاني.</p><div class="col">${alts.map(k => `<button class="exrow" data-swapto="${k}"><img src="img/ex3d/${k}.jpg" alt="" loading="lazy"><div class="grow"><h3>${EX[k].n}</h3><p class="xs mut">${EASY[d.swap] && EASY[d.swap][0] === k ? '<span style="color:#34c759">✓ أسهل • ' + EASY[d.swap][1] + '</span>' : EX[k].gym}</p></div></button>`).join('')}</div>`, true); $('#screen').hidden = false; return; }
  if (d.swapto && SES) { const x = SES.items[SES.k]; SES.items = SES.items.slice(); SES.items[SES.k] = Object.assign({}, x, { id: d.swapto, w: EX[d.swapto].w0 }); SES.sets[SES.k].forEach(z => z.w = EX[d.swapto].w0 || ''); stack = []; const sc = $('#screen'); sc.hidden = true; sc.innerHTML = ''; renderPlayer(); toast('تبدّل التمرين'); return; }
  if ('hardupdate' in d) { hardUpdate(); return; }
  if (d.prod) { openProd(d.prod); return; }
  if (d.wstep) { const i = $('#wIn'); i.value = Math.round((+String(i.value).replace(',', '.') + +d.wstep) * 10) / 10; return; }
  if ('savemeas' in d) { const m = { d: today() }; document.querySelectorAll('[data-meas]').forEach(x => { if (+x.value) m[x.dataset.meas] = +x.value; }); S.meas = S.meas || []; S.meas.push(m); save(); reroute(); toast('انحفظت القياسات'); return; }
});
function renderPlayerSets() { // تحديث السطور بدون ما نعيد الأنيميشن
  const sets = SES.sets[SES.k], cur = sets.findIndex(s => !s.ok);
  document.querySelectorAll('#player .set').forEach((row, j) => { row.classList.toggle('done', sets[j].ok); const i = row.querySelector('.i'); i.classList.toggle('cur', j === cur); i.textContent = j === cur ? '●' : AR(j + 1); });
  const done = SES.sets.map(s => s.every(z => z.ok)); document.querySelectorAll('#player .dots button').forEach((x, j) => x.classList.toggle('ok', done[j]));
}
document.addEventListener('keydown', e => { if (e.key === 'Enter' && e.target.id === 'mq') { e.preventDefault(); nameSearch(); } if (e.key === 'Enter' && e.target.id === 'bcIn') { e.preventDefault(); lookupBC(e.target.value); } });
document.addEventListener('change', async e => { if (e.target.id === 'ingImg' && e.target.files[0]) { ocrIngredients(e.target.files[0], e.target.dataset.code || ''); e.target.value = ''; return; } if (e.target.id === 'bcImg' && e.target.files[0]) { decodeImage(e.target.files[0]); e.target.value = ''; return; } if (e.target.id === 'impIn' && e.target.files[0]) { try { const o = JSON.parse(await e.target.files[0].text()); if (!o || !o.month) throw 0; S = Object.assign(def(), o); save(); applyTheme(); closeScreen(); toast('رجعت معلوماتك ✓'); } catch (er) { toast('الملف مو صحيح'); } return; } if (e.target.id === 'photoIn' && e.target.files[0]) { await savePhoto(e.target.files[0]); toast('انحفظت الصورة'); loadPhotos(); } });
document.addEventListener('input', e => { const t = e.target; if (t.id === 'pcW') { const v = +t.value; if (v >= 30 && v <= 200) { PC.w = v; const o = $('#pcOut'); const pos = t.selectionStart; pcRe(); const n = $('#pcW'); if (n) { n.focus(); try { n.setSelectionRange(pos, pos); } catch (er) {} } } return; } if (t.id === 'fdq') { fdQ = t.value; const pos = t.selectionStart; openDB(); const n = $('#fdq'); if (n) { n.focus(); try { n.setSelectionRange(pos, pos); } catch (er) {} } return; } if (!SES) return; if (t.dataset.w != null) SES.sets[SES.k][+t.dataset.w].w = t.value; if (t.dataset.r != null) SES.sets[SES.k][+t.dataset.r].r = t.value; });
/* ================= إحساس التطبيق الحقيقي ================= */
// لمسة ضوء مكان إصبعك
const RIPS = '.dayc,.exrow,.prog,.mus,.excard,.pcard,.slot,.chc,.cd,.gbtn,.obtn,.btn,.ytbtn,.srow,.hero2,.fonts button';
document.addEventListener('pointerdown', e => { const el = e.target.closest(RIPS); if (!el || RM) return; const r = el.getBoundingClientRect(), d = Math.max(r.width, r.height) * 2.2, sp = document.createElement('span'); sp.className = 'rip'; sp.style.cssText = `width:${d}px;height:${d}px;left:${e.clientX - r.left - d / 2}px;top:${e.clientY - r.top - d / 2}px`; el.append(sp); setTimeout(() => sp.remove(), 600); }, { passive: true });
// اهتزاز خفيف بالأزرار المهمة
document.addEventListener('click', e => { const b = e.target.closest('.gbtn,.btn,[data-ok],[data-start],[data-took],[data-back],[data-close],[data-setprog]'); if (b) haptic(b.matches('[data-ok],[data-setprog]') ? 14 : 8); }, true);
// التبويبات: تنط، وإذا ضغطت نفس التبويب يرجعك لفوگ
const scrollMem = {};
document.querySelector('nav').addEventListener('click', e => { const a = e.target.closest('a'); if (!a) return; haptic(); const t = a.dataset.t; if (location.hash.slice(1) === t || (!location.hash && t === 'home')) { e.preventDefault(); scrollTo({ top: 0, behavior: 'smooth' }); return; } scrollMem[lastTab] = scrollY; a.classList.remove('pop'); void a.offsetWidth; a.classList.add('pop'); });
// شريط العنوان الصغير
const mb = $('#minibar');
addEventListener('scroll', () => { if (!mb) return; const h = $('#app h1') || $('#app .hi b'); const on = scrollY > 70 && $('#screen').hidden; if (on && h) mb.textContent = h.textContent.replace(/!$/, ''); mb.classList.toggle('on', on); }, { passive: true });
// الأرقام تعد لحد قيمتها
function countUp(root = document) { if (RM) return; root.querySelectorAll('[data-count]').forEach(el => { const to = +el.dataset.count, suf = el.dataset.suf || '', t0 = performance.now(), D = 900; const f = now => { const k = Math.min(1, (now - t0) / D), v = Math.round(to * (1 - Math.pow(1 - k, 3))); el.textContent = v + suf; if (k < 1) requestAnimationFrame(f); }; requestAnimationFrame(f); }); }

route();
/* نحمّل كل مقاطع الحركة مرة وحدة، حتى تشتغل بعدين بدون نت */
setTimeout(() => { if (!navigator.onLine) return; let i = 0; const L = CLIP.flatMap(id => [`img/clip/${id}-0.webp`, `img/clip/${id}-1.webp`]); const next = () => { const u = L.slice(i, i + 6); i += 6; if (!u.length) return; Promise.all(u.map(x => fetch(x).catch(() => 0))).then(() => setTimeout(next, 150)); }; next(); }, 4000);
(() => { const sp = document.getElementById('splash'); if (!sp) return; const go = () => { if (sp.classList.contains('out') || sp.dataset.lock) return; sp.classList.add('out'); $('#app').animate([{ opacity: 0, transform: 'translateY(30px) scale(.97)' }, { opacity: 1, transform: 'none' }], { duration: 700, easing: 'cubic-bezier(.22,1,.36,1)' }); setTimeout(() => sp.remove(), 750); }; sp.classList.add('run', 'sp-shake'); setTimeout(go, 5400); })();

/* ================= التحديث التلقائي ================= */
if ('serviceWorker' in navigator) {
  navigator.serviceWorker.register('sw.js', { updateViaCache: 'none' }).then(reg => {
    reg.update();
    document.addEventListener('visibilitychange', () => { if (document.visibilityState === 'visible') reg.update(); });
  }).catch(() => {});
  let reloaded = false;
  navigator.serviceWorker.addEventListener('controllerchange', () => { if (reloaded || SES || document.getElementById('splash')) return; reloaded = true; location.reload(); });
}
