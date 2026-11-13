// مدرّبي: منطق التطبيق
import { EX, REST_DAY, DAY_NAMES, DAY_IMG, MONTHS, FD, IBS, SUPPS, SCHEDULE, TIPS, INFO, EASY, SUPP_LIB, BAN as BAN0, BAN2, BAN_WORDS, IBS_BAN, IBS_GOOD } from './data.js';
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

/* ================= بناء برنامج الشهر ================= */
const MDAYS = 28, CYC = ['A', 'B', 'C', 'R'];
const dayType = i => CYC[i % 4];
const MOS = ['تشرين الثاني', 'كانون الأول', 'كانون الثاني', 'شباط', 'آذار', 'نيسان', 'أيار', 'حزيران', 'تموز', 'آب', 'أيلول', 'تشرين الأول'];
const NEXT = [[2, 'القوة'], [4, 'الحجم'], [3, 'الكتف والزند'], [5, 'التشكيل']];
/* الكورس مفتوح: بعد الستة أشهر الأولى يدوّر على مراحل القوة والحجم والكتف والتشكيل، وكل دورة أثقل من الي قبلها لأن الأوزان تنبني على أرقامك */
function tplFor(n) { if (n <= MONTHS.length) return MONTHS[n - 1]; const [i, nm] = NEXT[(n - 7) % 4], T = MONTHS[i]; return Object.assign({}, T, { n: nm + ' ' + AR(Math.floor((n - 7) / 4) + 2), mo: MOS[(n - 1) % 12], tw: +(T.tw + 1.5 * Math.ceil((n - 6) / 2)).toFixed(1), goal: T.goal + ' (دورة جديدة بأوزانك الحالية)' }); }
function buildMonth(n, ev) {
  const T = tplFor(n), plan = {}, prevTop = id => (S.month && S.month.plan && Object.values(S.month.plan).flat().find(x => x.id === id) || {}).r?.[1];
  for (const d of ['A', 'B', 'C']) {
    plan[d] = T.days[d].map(id => {
      const e = EX[id], base = e.c ? T.c : T.i;
      let s = base.s, r = e.sec ? [20, 40] : base.r.slice();
      if (id === 'calf' || id === 'plank') s = 3;
      if (ev) {
        if (ev.weak.some(m => e.m.includes(m))) s += 1;
        if (ev.feel === 'easy' && e.c) s += 1;
        if (ev.feel === 'hard') s -= 1;
      }
      s = Math.max(2, Math.min(5, s));
      let w = e.w0;
      const b = S.best[id];
      if (b && b.w) { w = b.w; const pt = prevTop(id) || 12; if (b.r >= pt) w = +(w + e.inc).toFixed(1); }
      return { id, s, r, rest: e.c ? 90 : 60, w };
    });
  }
  return { n, name: T.n, goal: T.goal, start: today(), plan, done: {} };
}
if (!S.month) { S.month = buildMonth(1); save(); }
function curDay() { for (let i = 0; i < MDAYS; i++) if (!S.month.done[i]) return i; return MDAYS; }
const isDeload = i => S.month.n % 2 === 0 && i >= 21;
function setsAt(item, i) { if (S.month.n === 1 && i < 14 && !EX[item.id].sec) return Math.min(2, item.s); if (isDeload(i) && !EX[item.id].sec) return Math.max(2, item.s - 1); return item.s; }
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
function vHome() {
  const c = curDay(), t = c < MDAYS ? dayType(c) : null, T = targets();
  const doneToday = S.hist.some(h => h.d === today()), water = (S.water || {})[today()] || 0, wT = Math.round(T.water * 4), pro = eatenPro();
  const hr = new Date().getHours(), greet = hr < 12 ? 'صباح الخير' : hr < 18 ? 'هلا بيك' : 'مساء الخير';
  const sp = (S.supp || {})[today()] || {}, eaten = (S.eaten || {})[today()] || {}, TM = todayMeals();
  const kc = TM.reduce((a, x) => eaten[x.m.k] ? a + optVal(x.o).k : a, 0);
  const wk = t === 'R' || t === null, IC = { b: '🍳', s: '🥣', l: '🍛', a: '🥤', d: '🥗' };
  const ring = (v, r, col, bg) => { const C = 2 * Math.PI * r; return `<circle cx="70" cy="70" r="${r}" stroke="${bg}" stroke-width="12" fill="none"/><circle cx="70" cy="70" r="${r}" stroke="${col}" stroke-width="12" fill="none" stroke-linecap="round" stroke-dasharray="${C}" stroke-dashoffset="${C * (1 - Math.min(1, v))}"/>`; };
  const supN = SUPPS.filter(s => s.id !== 'mag').length, supD = SUPPS.filter(s => s.id !== 'mag' && sp[s.id]).length;
  return `<div class="hhead"><div><p class="mut">${greet}${S.name ? '، ' + esc(S.name) : ''} 👋</p><h1>${doneToday ? 'كفو! خلصت تمرين اليوم' : wk ? 'اليوم راحة' : 'يومك بنظرة وحدة'}</h1></div><div class="row" style="gap:8px"><span class="streak">${I.fire}<b class="num">${streak()}</b></span>${gearBtn()}</div></div>
  ${installCard()}${healthCard()}
  <div class="card rings2"><svg viewBox="0 0 140 140">${ring(kc / T.k, 60, 'var(--g)', 'var(--rg1)')}${ring(pro / T.p, 44, 'var(--gold)', 'var(--rg2)')}${ring(water / wT, 28, 'var(--blue)', 'var(--rg3)')}</svg>
   <div class="lg"><div><i style="background:var(--g)"></i><span>السعرات</span><b class="num" dir="ltr">${Math.round(kc)} / ${T.k}</b></div><div><i style="background:var(--gold)"></i><span>البروتين</span><b class="num" dir="ltr">${Math.round(pro)} / ${T.p}g</b></div><div><i style="background:var(--blue)"></i><span>المي</span><b class="num" dir="ltr">${water} / ${wT}</b></div><button class="btn sm ghost" data-water>💧 شربت گلاص</button></div></div>
  ${t === null ? `<div class="card"><h2>خلصت الشهر 🎉</h2><p class="sm mut">قيّم نفسك وأبنيلك الشهر الجاي.</p><button class="btn dark wide" data-eval>قيّم الشهر</button></div>`
   : `<div class="card"><button class="wo" data-day="${c}"><img src="img/ex3d/${t === 'R' ? 'child' : (dayItems(c)[0] || {}).id || 'chestpress'}.jpg" alt=""><div><small>${t === 'R' ? 'يوم راحة' : 'تمرين اليوم'} • اليوم ${c + 1}</small><h2>${DAY_NAMES[t]}</h2><p class="num">${t === 'R' ? 'مشي 30 دقيقة + إطالات' : dayItems(c).length + ' تمارين • 50 دقيقة'}</p></div></button>${doneToday ? '<div class="donebox">✓ خلصته اليوم، كفو</div>' : `<button class="btn dark wide" data-${t === 'R' ? 'day' : 'start'}="${c}">${t === 'R' ? 'شوف تمارين الراحة' : 'ابدأ التمرين'}</button>`}</div>`}
  <div class="card"><div class="sec-h"><h2>أكلك اليوم</h2><a class="xs" href="#food" style="color:var(--g)">كل الأكل</a></div>
   <div class="mlist">${TM.map(({ m, o }) => { const v = optVal(o); return `<button class="${eaten[m.k] ? 'on' : ''}" data-rec="${o.id}" data-slot="${m.k}"><span class="e">${eaten[m.k] ? '✓' : IC[m.k]}</span><span class="grow"><b>${o.n}</b><small>${m.n}</small></span><b class="num p">${Math.round(v.p)}g</b></button>`; }).join('')}</div></div>
  <a class="card linkc" href="#supps"><span class="e">💊</span><span class="grow"><b>حبوبك اليوم</b><small class="num">${supD} من ${supN} أخذتها</small></span>${I.chev}</a>
  ${smartCard()}
  ${coachCard()}`;
}
function installCard() {
  const sa = window.navigator.standalone || matchMedia('(display-mode: standalone)').matches;
  if (sa || S.hideInstall) return '';
  return `<div class="install"><b class="d">خلّيه تطبيق على شاشة الآيفون</b><p class="sm">افتح الرابط بسفاري ← اضغط زر المشاركة <span style="display:inline-flex;width:18px;vertical-align:-3px;color:var(--g)">${I.share}</span> ← "إضافة إلى الشاشة الرئيسية".</p><button class="btn ghost sm" data-hideinstall>سوّيتها</button></div>`;
}

/* ================= الكورس ================= */
let showPlan = false;
function vCourse() {
  const c = curDay(), M = S.month, doneN = Object.keys(M.done).length, t = c < MDAYS ? dayType(c) : null;
  const wk = Math.min(3, Math.floor(Math.min(c, MDAYS - 1) / 7));
  const strip = Array.from({ length: 7 }, (_, k) => wk * 7 + k).map(i => { const ty = dayType(i); return `<button class="dd ${M.done[i] ? 'done' : ''} ${i === c ? 'now' : ''} ${ty === 'R' ? 'rest' : ''}" data-day="${i}"><span class="xs">${['ص', 'ظ', 'ك', 'ر'][CYC.indexOf(ty)]}</span><b class="num">${AR(i + 1)}</b></button>`; }).join('');
  return `${head('تمريني')}<span class="pill g" style="align-self:flex-start">${M.mo || tplFor(M.n).mo} • ${tplFor(M.n).n}</span>
  ${t === null ? `<div class="card"><h2>خلصت الشهر 🎉</h2><p class="sm mut">قيّم نفسك وأبنيلك الشهر الجاي.</p><button class="btn wide" data-eval>قيّم الشهر</button></div>` : `
  <button class="hero" data-day="${c}"><div class="wm">اليوم ${AR(c + 1)}</div><div class="txt"><span class="lab">${t === 'R' ? 'يوم راحة' : 'تمرين اليوم'}</span><h1>${DAY_NAMES[t]}</h1><p class="sm">${t === 'R' ? 'مشي + وگفة' : AR(dayItems(c).length) + ' تمارين'}</p><span class="go">${I.play}</span></div><img src="img/ex3d/${DAY_IMG[t]}.jpg" alt=""></button>
  ${t !== 'R' ? `<div class="col">${dayItems(c).map((x, k) => `<button class="exrow" data-ex="${x.id}"><img src="img/ex3d/${x.id}.jpg" alt="" loading="lazy"><div class="grow"><h3>${EX[x.id].n}${EX[x.id].star ? ' ⭐' : ''}</h3><p class="sm num" style="color:var(--g)">${AR(setsAt(x, c))} × ${rng(x.r)} ${EX[x.id].sec ? 'ثانية' : ''}</p><p class="xs mut">${x.w ? AR(x.w) + ' كغم' : 'بدون وزن'}</p></div><span class="k">${I.play}</span></button>`).join('')}</div>
  <button class="btn wide big" data-start="${c}">${I.play} يلا نبدي</button>` : ''}`}
  <div class="card"><div class="sec-h"><h2>هالأسبوع</h2><span class="xs mut num">${AR(doneN)}/${AR(MDAYS)} يوم بالشهر</span></div><div class="strip">${strip}</div><p class="xs mut">ص = صدر وأمامية • ظ = ظهر وخلفية • ك = كتف ورجل • ر = راحة</p></div>
  <button class="forecard" data-fore><span>💪</span><div class="grow"><b>برنامج الساعد</b><small>${Object.keys(S.fore || {}).filter(d => daysBetween(d, today()) < 7 && S.fore[d]).length}/3 هالأسبوع • 6 دقايق، يكبّر الساعد ويقوّي القبضة</small></div>${I.chev}</button>
  <div class="sec-h"><h2>دليل المدرّب</h2></div>
  <details class="card guide"><summary><b>🏆 القواعد الذهبية للعضل</b></summary><div class="good sm col">
   <p><b>الزيادة التدريجية:</b> لما تكمّل كل السِتات بأعلى عدّات، زيد الوزن الجلسة الجاية. التطبيق يحسبها إلك لحاله</p>
   <p><b>جهد صح:</b> آخر سِت تخلّي 1-2 عدّة بالخزان. أبعد من هيچ ما يكبّر، وأقرب يتعبك ويعوّرك</p>
   <p><b>النزول على مهلك:</b> 3 ثواني للنزول. نص فايدة التمرين بالنزول</p>
   <p><b>الحركة كاملة:</b> المدى الكامل يكبّر العضلة أكثر من الوزن الثقيل بنص حركة</p>
   <p><b>عدد السِتات:</b> 10-20 سِت لكل عضلة بالأسبوع. الكورس محسوب على هالأساس</p>
   <p><b>النوم 8 ساعات</b> وبروتين 2 غم لكل كيلو. العضلة تنبني بالفراش والمطبخ، مو بس بالجيم</p></div></details>
  <details class="card guide"><summary><b>👕 العضلات الي تبين بالتيشيرت</b></summary><p class="xs mut">هاي العضلات صغيرة ومخفية، بس هي الي تسوي شكل الـV وتفرق بالمظهر. نشتغل عليها كل أسبوع:</p><div class="col">${[['lateral', 'الكتف الجانبي', 'يعرّض الكتف ويخلي الخصر يبين أنحف'], ['reardelt', 'الكتف الخلفي', 'يعدّل الوگفة ويحمي مفصل الكتف'], ['incline', 'أعلى الصدر', 'يملا فتحة التيشيرت'], ['wristcurl', 'الساعد (لگدام)', 'الساعد يبين أول شي بنص كم'], ['revcurl', 'الساعد (لورا)', 'يكمّل شكل الساعد ويقوّي القبضة'], ['farmer', 'القبضة', 'أقوى تمرين للساعد والقبضة'], ['calf', 'السمانة', 'ما تكبر إلا بعدّات كثيرة وتمطيط'], ['kneeraise', 'البطن السفلي', 'يبيّن البطن لما تقل الدهون']].filter(([id]) => EX[id]).map(([id, n, w]) => `<button class="exrow" data-ex="${id}"><img src="img/ex3d/${id}.jpg" alt="" loading="lazy"><div class="grow"><h3>${n}</h3><p class="xs mut">${w}</p></div></button>`).join('')}</div></details>
  <details class="card guide"><summary><b>🎬 مكتبة الحركات (${Object.keys(EX).length} حركة بالأنيميشن)</b></summary><p class="xs mut">كل حركة إلها أنيميشن وشرح، والصعبة إلها بديل أسهل.</p>${Object.entries(Object.keys(EX).reduce((a, id) => { const m = EX[id].m[0]; (a[m] = a[m] || []).push(id); return a; }, {})).map(([m, ids]) => `<h3 style="margin-top:10px">${MN[m] || m}</h3><div class="hscroll">${ids.map(id => `<button class="mini" data-ex="${id}"><span class="mimg"><img src="img/ex3d/${id}.jpg" alt="" loading="lazy"></span><b class="xs">${EX[id].n}</b>${EASY[id] ? '<span class="xs" style="color:#34c759">إلها بديل أسهل</span>' : ''}</button>`).join('')}</div>`).join('')}</details>
  <details class="card guide"><summary><b>🦴 مفاصلك والوگفة</b></summary><div class="good sm col">
   <p>إحماء المفاصل 5 دقايق قبل كل تمرين (موجود بصفحة اليوم)</p>
   <p>الكتف: لا تنزل بالضغط لتحت كلش، والكوع بزاوية 45 درجة مو مفتوح</p>
   <p>الركبة: باتجاه أصابع رجلك، ولا تقفلها بقوة فوگ</p>
   <p>الظهر: صدرك لگدام وظهرك مستقيم بالسحب والرفعة الرومانية</p>
   <p>الوگفة: تمرين الكتف الخلفي والسحب يرجّعون كتوفك لورا. حاول تسوي السحب أكثر من الدفع</p>
   <p>وجع حاد بالمفصل = وگّف. وجع العضلة بعد يومين = طبيعي</p></div></details>
  <button class="card plan-t" data-plan><div class="row between"><h2>رحلتك (مفتوحة، ما إلها نهاية)</h2><span class="mut">${showPlan ? '▲' : '▼'}</span></div><p class="xs mut">أول 6 أشهر تأسيس لجسمك، وبعدها نكمّل دورات جديدة أثقل. كل شهر يتبنى على تقييمك.</p></button>
  ${showPlan ? `<div class="card"><div class="road">${Array.from({ length: Math.max(6, M.n + 2) }, (_, k) => tplFor(k + 1)).map((T, k) => { const n = k + 1, st = n < M.n ? 'done' : n === M.n ? 'now' : 'lock'; return `<div class="rstep ${st}"><span class="dot">${st === 'done' ? I.check : st === 'lock' ? '🔒' : AR(n)}</span><div><b>${T.mo}: ${T.n}</b><span class="xs mut">${T.goal}</span><span class="xs" style="color:var(--g)">هدف الوزن ${AR(T.tw)} كغم</span></div></div>`; }).join('')}</div><button class="btn ghost wide" data-eval>خلصت الشهر؟ قيّم نفسك</button></div>` : ''}`;
}
/* ================= شاشة اليوم ================= */
let SES = null;
const WARM = ['دقيقتين مشي سريع أو دراجة لحد ما تعرق شوية', 'تدوير الكتف لگدام وورا 10 مرات، وتدوير الذراع الممدودة 10', 'تدوير الرسغ 10 لكل جهة، وتدوير الورك 10', 'سكوات بدون وزن 10 مرات على مهلك', 'وقفة الجدار: ظهرك ويديك على الحايط، ارفع إيدك لفوگ 10 مرات (تفتح الكتف)'];
function openDay(i) {
  if (i >= MDAYS) { openEval(); return; }
  const t = dayType(i), it = dayItems(i);
  show(`<div class="row"><button class="ib" data-close aria-label="رجوع">${I.back}</button><div class="grow"><p class="xs mut">اليوم ${AR(i + 1)} • الشهر ${AR(S.month.n)}</p><h2>${DAY_NAMES[t]}</h2></div></div>
  <div class="month" style="min-height:200px"><img src="img/ex3d/${DAY_IMG[t]}.jpg" alt=""><h1>${DAY_NAMES[t]}</h1><p class="sm mut">${t === 'R' ? 'مشي 30 دقيقة، وهاي التمارين 10 دقايق قبل النوم.' : 'إحماء: 5 دقايق مشي سريع أو دراجة، وأول تمرين سِت خفيف بنص الوزن.'}</p></div>
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
function exInfo(id) {
  const e = EX[id];
  return `<div class="anim"><canvas id="ac"></canvas><span class="ph"><i></i><span id="aph">استعد</span></span></div>
  <div><p class="xs mut">اسمه بالجيم: ${e.gym}</p><h1>${e.n}${e.star ? ' ⭐' : ''}</h1></div>
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
  P.innerHTML = `<div class="stage"><canvas id="pc"></canvas><div class="fade"></div><div class="ov"><div class="row between"><button class="ib" data-pclose aria-label="طلّع">${I.x}</button><div class="row"><button class="ib" data-swap="${x.id}" aria-label="بدّل التمرين">⇄</button><button class="ib" data-slow aria-label="أبطأ">${I.slow}</button><button class="ib" data-info="${x.id}" aria-label="الشرح">${I.info}</button></div></div>
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
  show(`${confetti()}<div class="col" style="min-height:75vh;justify-content:center;align-items:center;text-align:center;gap:18px"><div class="medal pop" style="width:auto;padding:20px 28px"><span class="c" style="width:84px;height:84px">${I.trophy}</span></div><h1>عاشت إيدك يا بطل!</h1><span class="pill g num">+${AR(sets * 10 + 50)} نقطة</span><p class="mut">خلصت اليوم ${AR(i + 1)} من الشهر ${AR(S.month.n)}${sets ? ' • ' + AR(sets) + ' سِت' : ''}</p><div class="card" style="text-align:right;width:100%"><p class="sm">${dayType(i) === 'R' ? 'باچر تمرين، نام زين الليلة.' : 'هسه: سكوب البروتين خلال ساعتين، وجبة زينة، ونوم 8 ساعات.'}</p></div><button class="btn wide" data-close>رجوع</button></div>`);
  SES = null;
}

/* ================= تقييم الشهر ================= */
let EV = null;
function openEval() {
  const comp = [...new Set(Object.values(S.month.plan).flat().filter(x => EX[x.id].c).map(x => x.id))];
  EV = { weak: [], feel: 'ok' };
  show(`<div class="row"><button class="ib" data-close aria-label="رجوع">${I.back}</button><h2>تقييم الشهر ${AR(S.month.n)}</h2></div>
  <div class="card"><p class="sm">جاوب بصراحة. من أجوبتك أبنيلك الشهر الجاي: الأوزان، والعدّات، وأي عضلة نركّز عليها.</p></div>
  <div class="card"><h3>وزنك هسه</h3><label class="f">بالكيلو<input class="field" id="evW" inputmode="decimal" value="${curW()}"></label></div>
  <div class="card"><h3>أثقل وزن شلته بكل تمرين</h3><p class="xs mut">الوزن والعدّات بأحسن سِت. معبّية من الي سجلته، عدّلها إذا تريد.</p>
   ${comp.map(id => `<div class="row"><img src="img/ex3d/${id}.jpg" alt="" style="width:46px;height:46px;border-radius:12px;object-fit:cover"><span class="grow sm">${EX[id].n}</span><input class="field" style="width:76px;text-align:center" inputmode="decimal" data-evw="${id}" value="${S.best[id]?.w ?? ''}" placeholder="كغم" aria-label="الوزن"><input class="field" style="width:62px;text-align:center" inputmode="numeric" data-evr="${id}" value="${S.best[id]?.r ?? ''}" placeholder="×" aria-label="العدّات"></div>`).join('')}</div>
  <div class="card"><h3>أي عضلة تحسها ضعيفة أو تريدها تكبر أكثر؟</h3><div class="chips" id="evWeak">${['chest', 'back', 'shoulders', 'biceps', 'triceps', 'quads', 'hamstrings', 'calves'].map(m => `<button data-weak="${m}">${MN[m]}</button>`).join('')}</div></div>
  <div class="card"><h3>شلون كان الشهر عليك؟</h3><div class="chips" id="evFeel"><button data-feel="easy">سهل</button><button data-feel="ok" class="on">مناسب</button><button data-feel="hard">صعب ومتعب</button></div></div>
  <button class="btn wide" data-evsubmit>ابني الشهر الجاي</button>`);
}
function submitEval() {
  const w = +$('#evW').value; if (w > 25 && w < 200) { const t = today(), x = S.weights.find(z => z.d === t); if (x) x.w = w; else S.weights.push({ d: t, w }); }
  document.querySelectorAll('[data-evw]').forEach(inp => { const id = inp.dataset.evw, wv = +inp.value, r = +document.querySelector(`[data-evr="${id}"]`).value; if (wv || r) S.best[id] = { w: wv || 0, r: r || 0 }; });
  const prevW = S.evals.length ? S.evals[S.evals.length - 1].w : (S.weights[0]?.w || +S.w), gain = curW() - prevW;
  const kcalAdj = (S.evals.length ? S.evals[S.evals.length - 1].kcalAdj || 0 : 0) + (gain < .8 ? 200 : gain > 2.5 ? -150 : 0);
  const ev = { d: today(), month: S.month.n, w: curW(), gain, weak: EV.weak, feel: EV.feel, kcalAdj };
  S.evals.push(ev); const old = S.month; S.month = buildMonth(old.n + 1, ev); save();
  const ch = []; if (EV.weak.length) ch.push('سِت زيادة لـ ' + EV.weak.map(m => MN[m]).join(' و')); if (EV.feel === 'easy') ch.push('سِت زيادة للتمارين الكبيرة'); if (EV.feel === 'hard') ch.push('سِت أقل حتى ترتاح'); ch.push(gain < .8 ? 'وزنك زاد قليل، زدنا 200 سعرة على أكلك' : gain > 2.5 ? 'وزنك زاد بسرعة، نقّصنا 150 سعرة' : 'وزنك يزيد بالسرعة الصحيحة'); ch.push('الأوزان زادت للتمارين الي خلصت عدّاتها');
  show(`<div class="col" style="gap:16px"><h1>الشهر ${AR(S.month.n)}: ${S.month.name}</h1><p class="mut">${S.month.goal}</p><div class="card"><h3>شنو تغيّر</h3><div class="good sm col">${ch.map(c => `<p>${c}</p>`).join('')}</div></div>
  ${['A', 'B', 'C'].map(d => `<div class="card"><h3>${DAY_NAMES[d]}</h3>${S.month.plan[d].map(x => `<div class="row between sm"><span>${EX[x.id].n}</span><span class="num mut">${AR(x.s)} × ${rng(x.r)}${x.w ? ' • ' + AR(x.w) + ' كغم' : ''}</span></div>`).join('')}</div>`).join('')}
  <button class="btn wide" data-close>يلا نبدي</button></div>`);
}

/* ================= الأكل ================= */
/* ================= الأكل: أقسام، وكل وجبة بجدول مكوناتها ومجموعها ================= */
let fdCat = 'market', fdQ = '';
const SLOTS = [['b', 'الفطور', '7-9 الصبح'], ['s', 'سناك', 'الضحى'], ['l', 'الغدا', '1-3 الظهر'], ['a', 'العصرونية', 'بعد التمرين'], ['d', 'العشا', 'قبل النوم بـ3 ساعات']];
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
  const extra = [['fridge', '🧊', 'شنو عندي بالبيت؟', 'اختار الي بالثلاجة وأگلك شنو تطبخ'], ['sw', '🍫', 'حلا صحي', 'حلو بدون ما يخرّب جسمك'], ['k', '🥜', 'كرزات وموالح', 'مكسرات وبذور وفوايدها'], ['sh', '🥤', 'شيكات التضخيم', 'سعرات وبروتين بگلاص'], ['drinks', '💧', 'المشروبات', 'شنو تشرب وشنو لا'], ['fdb', '🔎', 'الأطعمة والبذور', Object.keys(FOODS).length + ' أكلة بقيمها'], ['shop', '🛒', 'سلة الأسبوع', 'شنو تشتري من الماركت'], ['supps', '💊', 'المكملات', 'بروتين وكرياتين وفيتامينات وروابط الشراء'], ['ban', '⛔', 'الممنوعات', 'حرام وينفخ القولون']];
  return `${head('الأكل')}
  <div class="card"><div class="sec-h"><h2>أكلت اليوم</h2><span class="xs mut num">القائمة: ${Math.round(plan.k)} سعرة • ${Math.round(plan.p)}g بروتين</span></div>
   ${bar(tot.k, T.k, 'var(--g)', 'السعرات', 'سعرة')}${bar(tot.p, T.p, 'var(--gold)', 'البروتين', 'غم')}${bar(tot.c, Math.round(T.k * .5 / 4), 'var(--blue)', 'الكارب', 'غم')}${bar(tot.f, Math.round(T.k * .27 / 9), '#ff9f0a', 'الدهون', 'غم')}
   <p class="xs mut">هدفك للتضخيم النظيف: ${T.k} سعرة و${T.p}g بروتين.</p></div>
  <div class="sec-h"><h2>وجباتك اليوم</h2><span class="xs mut">اضغط على الوجبة تشوف كل خياراتها</span></div>
  <div class="slist">${TM.map(({ m, o }) => { const v = optVal(o), c = IC[m.k]; return `<div class="slot ${eaten[m.k] ? 'on' : ''}"><button class="sbody" data-sec="${SEC[m.k]}" data-forslot="${m.k}"><span class="sico" style="background:${c[1]}22;color:${c[1]}">${c[0]}</span><span class="stxt"><span class="xs mut">${m.n} • ${m.t}</span><b>${o.n}</b><span class="xs num"><b style="color:var(--gold)">${Math.round(v.p)}g</b> بروتين • <b>${Math.round(v.k)}</b> سعرة • ${Math.round(v.c)}g كارب • ${Math.round(v.f)}g دهون</span></span>${I.chev}</button><button class="ib sm ${eaten[m.k] ? 'on' : ''}" data-eat="${m.k}" aria-label="أكلتها">${I.check}</button></div>`; }).join('')}</div>
  <div class="sec-h"><h2>أقسام ثانية</h2></div>
  <div class="slist">${extra.map(([k, ic, n, sub]) => { const at = k === 'ban' || k === 'supps' ? `href="#${k}"` : ['drinks', 'fdb', 'shop', 'fridge'].includes(k) ? `data-${k}` : `data-sec="${k}"`; const tag = k === 'ban' || k === 'supps' ? 'a' : 'button'; return `<${tag} class="slot ex" ${at}><span class="sico">${ic}</span><span class="stxt"><b>${n}</b><span class="xs mut">${sub}${['sw', 'k', 'sh'].includes(k) ? ' • ' + RECIPES.filter(r => r.s === k).length + ' وصفة' : ''}</span></span>${I.chev}</${tag}>`; }).join('')}</div>`;
}
function openSection(k, forSlot) {
  const sec = SECTIONS.find(x => x[0] === k), L = RECIPES.filter(r => r.s === k).concat(k === 'l' ? [0, 1, 2, 3, 4, 5].map(i => genMeal(dayNo() * 7 + 100 + i)) : []);
  const slot = forSlot || { b: 'b', l: 'l', d: 'd', s: 's', sh: 'a', sw: 's', k: 's' }[k], curR = pickFor(slot), cur = curR.id, slotN = (SLOTS.find(x => x[0] === slot) || [])[1];
  const cv = optVal(curR), mine = curR.s === k || (k === 'sh' && slot === 'a');
  const html = `<div class="row"><button class="ib" data-close aria-label="رجوع">${I.back}</button><div class="grow"><h1>${sec[1]}</h1><p class="xs mut">${sec[2]} • ${L.length} وصفة</p></div></div>
  ${mine ? `<button class="curmeal" data-rec="${cur}" data-slot="${slot}"><img src="${recImg(curR)}" alt="" class="${isCut(curR) ? 'cut' : ''}"><div><span class="xs">✓ ${slotN} اليوم</span><b>${curR.n}</b>${macroRow(cv)}<span class="xs" style="opacity:.85">اضغط تشوف المكونات بالغرام وشلون تسويها</span></div></button>` : ''}
  <div class="sec-h"><h2>${mine ? 'بدّل بوحدة من هاي' : 'كل الوصفات'}</h2><span class="xs mut">الأعلى بروتين أول</span></div>
  <div class="col">${L.filter(r => r.id !== cur).map(r => [r, optVal(r)]).sort((a, b) => b[1].p - a[1].p).map(([r, v]) => `<div class="rrow"><button class="rmain" data-rec="${r.id}" data-slot="${slot}"><span class="rimg2"><img src="${recImg(r)}" alt="" loading="lazy" class="${isCut(r) ? 'cut' : ''}">${r.gen ? '<em>✨ جديدة</em>' : ''}</span><span class="grow col" style="gap:3px"><b>${r.n}</b><span class="xs mut clamp">${r.tag || ''}</span><span class="pmac num"><span><b style="color:var(--gold)">${Math.round(v.p)}g</b> بروتين</span><span><b>${Math.round(v.k)}</b> سعرة</span><span>⏱ ${r.t || 15}د</span></span></span></button><button class="pick" data-userec="${r.id}:${slot}:${k}">اختارها</button></div>`).join('')}</div>`;
  const s = $('#screen'); if (!s.hidden && s.querySelector('.curmeal,.rrow')) { const y = s.scrollTop; s.innerHTML = `<div class="in">${html}</div>`; s.scrollTop = y; } else show(html);
}
function openRecipe(id, slot) {
  calcScale(); const o = forMe(recById(id)), v = optVal(o), sl = SLOTS.find(x => x[0] === slot) || SLOTS.find(x => POOL[x[0]].includes(o.s)) || SLOTS[2], cur = pickFor(sl[0]).id === id, sc = score(o), my = (S.rate || {})[id] || 0;
  const bar5 = (n, x) => `<div class="sc"><span class="xs">${n}</span><span class="dots5">${[1, 2, 3, 4, 5].map(i => `<i class="${i <= x ? 'on' : ''}"></i>`).join('')}</span></div>`;
  show(`<div class="row"><button class="ib" data-back aria-label="رجوع">${I.back}</button><div class="grow"><p class="xs mut">${sl[1]}</p></div><span class="pill num">⏱ ${o.t || 15} دقيقة</span></div>
  <div class="dishhero ${isCut(o) ? 'cut' : ''}"><img src="${recImg(o)}" alt=""><div><h1>${o.n}</h1></div></div>
  ${o.tag ? `<p class="sm">${o.tag}</p>` : ''}
  ${o.scaled ? `<div class="warm">🧠 الكميات معدّلة على هدفك (×${o.scaled.toFixed(2)})، حتى توصل ${targets().k} سعرة باليوم.</div>` : ''}
  <div class="card"><h3>مجموع الوجبة</h3>${macroRow(v, 1)}</div>
  <div class="card"><h3>المكونات وشكد بكل وحدة</h3>
   <div class="itab"><div class="ih"><span>المكوّن</span><span>بروتين</span><span>كارب</span><span>دهون</span><span>سعرة</span></div>
   ${o.it.map(([k, a]) => { const iv = itemVal(k, a), A = amt(k, a); return `<button class="ir" data-food="${k}">${fthumb(k, 40)}<span class="inm"><b>${FOODS[k].n}</b><small class="num">${A.g}${A.h ? ' • ' + A.h : ''}</small></span><span class="num">${r1(iv.p)}</span><span class="num">${r1(iv.c)}</span><span class="num">${r1(iv.f)}</span><span class="num">${Math.round(iv.k)}</span></button>`; }).join('')}
   <div class="ir tot"><span class="inm"><b>المجموع</b></span><span class="num">${r1(v.p)}</span><span class="num">${r1(v.c)}</span><span class="num">${r1(v.f)}</span><span class="num">${Math.round(v.k)}</span></div></div>
   ${o.it.some(([k]) => FOODS[k].cat === 'meat') ? '<p class="xs" style="color:var(--gold)">اللحم والدجاج من محل حلال.</p>' : ''}</div>
  <div class="card"><h3>شلون تسويها</h3><div class="steps sm">${o.prep.map(p => `<p>${p}</p>`).join('')}</div></div>
  <div class="card"><h3>تقييم NEXFIT</h3>${bar5('البروتين', sc.pro)}${bar5('السهولة', sc.ease)}${bar5('راحة القولون', sc.ibs)}<p class="xs mut">محسوب من مكونات الوجبة ووكتها.</p>
   <h3 style="margin-top:6px">تقييمك إنت للطعم</h3><div class="stars">${[1, 2, 3, 4, 5].map(i => `<button data-rate="${id}:${i}" class="${i <= my ? 'on' : ''}" aria-label="${i}">★</button>`).join('')}</div><p class="xs mut">${my ? (my >= 4 ? 'راح أطلعلك ياها أكثر 😋' : my <= 2 ? 'راح أقللها من قائمتك' : 'انحفظ تقييمك') : 'بعد ما تاكلها قيّمها، والقائمة تتعلم ذوقك.'}</p></div>
  <div class="card"><h3>شلون حسيت بطنك بعدها؟</h3><div class="row"><button class="btn ghost grow" data-fx="${id}:1">😌 ريّحتني</button><button class="btn ghost grow" data-fx="${id}:-1">😣 نفختني</button></div>${(S.fx || {})[id] < 0 ? '<p class="xs" style="color:var(--gold)">⚠ هاي نفختك قبل، فما راح تطلعلك بالقائمة.</p>' : ''}</div>
  <button class="btn wide ${cur ? 'ghost' : ''}" data-userec="${id}:${sl[0]}">${cur ? 'هاي أكلتك اليوم ✓' : 'خليها ' + sl[1] + ' اليوم'}</button>`, true);
}
function openDB() {
  const q = fdQ.trim(), keys = Object.keys(FOODS).filter(k => q ? (FOODS[k].n + ' ' + FOODS[k].fi).toLowerCase().includes(q.toLowerCase()) : FOODS[k].cat === fdCat).sort((a, b) => FOODS[b].v[1] - FOODS[a].v[1]);
  const html = `<div class="row"><button class="ib" data-close aria-label="رجوع">${I.back}</button><h1 class="grow">الأطعمة والبذور</h1></div>
  <input class="field" id="fdq" type="search" placeholder="🔎 دوّر: دجاج، برتقال، شيا..." value="${esc(fdQ)}">
  ${q ? '' : `<div class="cats">${CATS.map(([k, n, ic]) => `<button class="${fdCat === k ? 'on' : ''}" data-fcat="${k}"><span>${ic}</span>${n}</button>`).join('')}<button class="${fdCat === 'fin' ? 'on' : ''}" data-fcat="fin"><span>🇫🇮</span>منتجات بيتك</button></div>`}
  ${!q && fdCat === 'fin' ? `<div class="pgrid">${Object.keys(INFO).map(k => { const f = FD[k], i = INFO[k]; return `<button class="pcard" data-prod="${k}"><span class="pimg"><img src="img/${f.img}.webp" alt="" loading="lazy"></span><b>${f.n}</b><span class="fi">${f.b || ''}</span><span class="badges"><i class="ok">حلال</i>${i.lac === 'yes' ? '<i class="no">لاكتوز</i>' : '<i class="ok">بدون لاكتوز</i>'}</span></button>`; }).join('')}</div>`
  : `<p class="xs mut">${keys.length} • مرتّبة من الأعلى بروتين. الأرقام للحصة العادية.</p><div class="col">${keys.map(k => { const f = FOODS[k], s = itemVal(k, f.srv); return `<button class="frow" data-food="${k}">${fthumb(k, 64)}<div class="grow"><b>${f.n}</b><span class="fi">${f.fi}</span>${f.ben ? `<span class="xs mut clamp">${f.ben}</span>` : ''}<span class="badges">${ibsB(f.ibs)}<i class="mid" style="background:var(--s2);color:var(--mut)">🗓 ${freqOf(k)}</i></span></div><div class="qty"><b class="num">${r1(s.p)}g</b><span>بروتين</span><span class="num">${Math.round(s.k)} سعرة</span><span>${f.sn || f.srv + ' غم'}</span></div></button>`; }).join('') || '<p class="mut">ما لگيت شي. جرّب كلمة ثانية.</p>'}</div>`}`;
  const s = $('#screen'); if (!s.hidden && s.querySelector('#fdq')) { s.innerHTML = `<div class="in">${html}</div>`; } else show(html);
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
  <div class="verd">${f.ibs === 'ok' ? '<div class="ok"><b>✓ يناسب القولون</b></div>' : f.ibs === 'limit' ? `<div class="mid"><b>⚠ للقولون: كمية قليلة</b><span>${f.note || ''}</span></div>` : `<div class="no"><b>✕ ينفخ القولون</b><span>${f.note || ''}</span></div>`}${f.cat === 'meat' ? '<div class="mid"><b>اشتريه من محل حلال</b><span>مكتوب Halal</span></div>' : ''}</div>
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
  const s = $('#screen'); if (!s.hidden && s.querySelector('.fchips')) { const y = s.scrollTop; s.innerHTML = `<div class="in">${html}</div>`; s.scrollTop = y; } else show(html);
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
const tags = ok => `<span class="badges">${ok.map(([c, t]) => `<i class="${c}">${c === 'no' ? '✕ ' : c === 'mid' ? '⚠ ' : '✓ '}${t}</i>`).join('')}</span>`;

/* ================= المكملات ================= */
let suppCat = 'protein';
function vSupps() {
  const d = S.supp[today()] || {}, minor = +S.age && +S.age < 18, C = SUPP_LIB.find(c => c.id === suppCat) || SUPP_LIB[0];
  return `${head('المكملات')}
  <div class="card"><div class="sec-h"><h2>حبوبك اليوم</h2><span class="xs mut">اضغط لما تاخذها</span></div>
   <div class="pills">${SUPPS.filter(s => s.id !== 'mag').map(s => `<button class="${d[s.id] ? 'on' : ''}" data-took="${s.id}"><img src="img/supp/${s.img}.webp" alt=""><b>${s.n.split(' (')[0].replace('الكرياتين', 'كرياتين').replace('بروتين أيزوليت', 'بروتين')}</b><span>${d[s.id] ? 'أخذته ✓' : s.when.split('،')[0]}</span></button>`).join('')}</div>
   <details class="sched"><summary class="sm">جدول اليوم بالوكت</summary><div class="timeline">${SCHEDULE.map(([t, w, ic]) => `<div class="tl"><span class="ic">${I[ic]}</span><div><b class="d">${t}</b><p class="sm mut">${w}</p></div></div>`).join('')}</div></details></div>
  ${minor ? '<div class="warn"><b>عمرك أقل من 18:</b> لا تاخذ كرياتين ولا بروتين قبل ما تسأل طبيب.</div>' : ''}
  <div class="cats">${SUPP_LIB.map(c => `<button class="${c.id === C.id ? 'on' : ''}" data-scat="${c.id}"><span>${c.ic}</span>${c.n}</button>`).join('')}</div>
  <div class="card"><h2>${C.ic} ${C.n}</h2><p class="sm">${C.intro}</p>${C.helps ? `<div class="chips">${C.helps.map(h => `<span class="pill">${h}</span>`).join('')}</div>` : ''}<div class="feel">💪 <b>شكد يساعدك:</b> ${C.help}</div></div>
  <div class="col">${C.items.map(x => `<button class="scard ${x.bad ? 'bad' : ''}" data-supp="${C.id}:${x.id}"><span class="pimg"><img src="img/${x.img}.webp" alt="" loading="lazy">${x.best ? '<em>⭐ الأفضل إلك</em>' : ''}${x.bad ? '<i>✕</i>' : ''}</span>
    <div class="grow col" style="gap:6px"><div><h3>${x.n}</h3><span class="fi">${esc(x.b)}</span></div>${x.buy ? '<span class="xs" style="color:#34c759">🛒 يتشرى أونلاين</span>' : ''}<span class="xs mut">${x.srv}${x.nut.k ? `: <b class="num" style="color:var(--gold)">${AR(x.nut.p)} غ بروتين</b> • ${AR(x.nut.k)} سعرة` : ' • ما بيه سعرات'}</span>${tags(x.ok)}</div></button>`).join('')}</div>
  ${C.skip.length ? `<div class="card" style="border-color:rgba(255,77,94,.4)"><h3>ليش ما اخترنا غيرها</h3><div class="bad sm col">${C.skip.map(t => `<p>${t}</p>`).join('')}</div></div>` : ''}
  <p class="xs mut">تثقيف عام مو وصفة طبية. اسأل الطبيب أو الصيدلي قبل أي مكمّل، خصوصاً ويا القولون. الأحسن تسوي فحص دم: فيتامين د، B12، الحديد.</p>`;
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
let zxP = null, zxR = null;
const loadZX = () => zxP || (zxP = new Promise((res, rej) => { const s = document.createElement('script'); s.src = 'vendor/zxing.min.js'; s.onload = () => res(window.ZXing); s.onerror = rej; document.head.append(s); }));
function stopScan() { try { zxR && zxR.reset(); } catch (e) {} zxR = null; }
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
  const v = n => n == null || n === '' ? '—' : Math.round(n * 10) / 10;
  const verdict = x.v === 'no' ? `<div class="danger"><span>${I.warn}</span><div><b>⛔ حرام، لا تشتريه</b><p class="sm">لگينا بالمكونات: ${x.h.join('، ')}</p></div></div>`
    : x.v === 'mid' ? `<div class="danger mid"><span>⚠</span><div><b>مشكوك، الأحسن تتركه</b><p class="sm">${x.d.join('، ')}</p></div></div>`
    : x.v === 'ok' ? `<div class="okbox"><b>✓ ما لگينا بيه خنزير ولا جيلاتين ولا خمر</b><p class="xs">حسب المكونات المكتوبة. ${x.hl ? 'وعليه علامة حلال ✓' : 'اللحم والدجاج لازم يكون مذبوح حلال حتى لو المكونات نظيفة.'}</p></div>`
    : '<div class="warn">المكونات مو مكتوبة بالقاعدة. اقراها من الغلاف، أو صوّر الباركود من جديد.</div>';
  const fit = x.v === 'ok' && !(x.i || []).length ? ['🟢', 'يناسبك: حلال حسب المكونات وما بيه شي ينفخ'] : x.v === 'ok' ? ['🟡', 'حلال حسب المكونات، بس انتبه للقولون'] : x.v === 'mid' ? ['🟠', 'الأحسن تتركه'] : x.v === 'no' ? ['🔴', 'ما يناسبك'] : ['⚪', 'ما نعرف'];
  return `<div class="row"><button class="ib" data-back aria-label="رجوع">${I.back}</button><h2 class="grow">${esc(x.n || 'منتج')}</h2></div>
  ${x.img ? `<div class="prod big"><img src="${x.img.replace('.400.jpg', '.full.jpg')}" onerror="this.src='${x.img}'" alt=""></div>` : ''}
  <span class="fi" style="font-size:14px">${esc(x.b || '')} ${esc(x.q || '')} ${code ? '• ' + code : ''}</span>
  <div class="fitbig"><span>${fit[0]}</span><b>${fit[1]}</b></div>
  ${verdict}
  ${x.v !== 'unk' ? ((x.i || []).length ? `<div class="danger mid"><span>🫃</span><div><b>للقولون: انتبه</b><p class="sm">بيه ${x.i.join('، ')}</p></div></div>` : '<div class="okbox"><b>✓ ما بيه أشياء معروفة تنفخ القولون</b></div>') : ''}
  <div class="card"><h3>بكل 100 غم</h3>${nutTiles({ k: v(x.k), p: v(x.p), c: v(x.cb), f: v(x.f) })}${x.p >= 10 ? '<p class="xs" style="color:var(--gold)">💪 بروتين عالي</p>' : ''}</div>
  ${x.ing ? `<details class="card"><summary class="sm">المكونات كما مكتوبة</summary><p class="fi" style="font-size:13px;line-height:1.7;margin-top:8px">${esc(x.ing.slice(0, 1400))}</p></details>` : ''}
  <p class="xs mut">الفحص يقرا المكونات المكتوبة بالقاعدة. إذا الغلاف بإيدك يختلف، صدّق الغلاف.</p>
  <button class="btn ghost wide" data-scan>📷 افحص منتج ثاني</button>`;
}
function vScan() {
  const sc = (S.scans || []).slice(0, 10);
  return `${head('الماركت')}
  <button class="scanhero" data-scan><span class="ring">📷</span><b>افحص منتج</b><small>وجّه الكاميرا على الباركود، ويگلك حلال لو لا، ويناسب القولون لو لا، وشكد بيه بروتين</small></button>
  <div class="row"><label class="btn ghost grow" style="font-size:15px">🖼 صورة الباركود<input type="file" accept="image/*" capture="environment" id="bcImg" hidden></label><button class="btn ghost grow" style="font-size:15px" data-bctype>⌨ اكتب الرقم</button></div>
  <div class="card"><h3>🔎 دوّر على منتج بالاسم</h3><div class="row"><input class="field" id="mq" type="search" placeholder="مثلاً: Shin Ramyun، Pocky، Indomie"><button class="btn sm" data-msearch>دوّر</button></div><div id="mres"></div></div>
  <div class="sec-h"><h2>محلات العالم</h2><span class="xs mut">منتجات مفحوصة</span></div>
  <div class="stores">${(window.__STORES || []).map(([k, f, n, sub]) => `<button class="store" data-store="${k}"><span>${f}</span><b>${n}</b><small>${sub}</small></button>`).join('') || '<p class="xs mut">دا يحمّل...</p>'}</div>
  ${sc.length ? `<div class="sec-h"><h2>آخر الي فحصته</h2></div><div class="slist">${sc.map(x => `<button class="slot ex" data-bc="${x.c}"><span class="sico">${x.r === 'no' ? '⛔' : x.r === 'mid' ? '⚠' : '✓'}</span><span class="stxt"><b>${esc(x.n || x.c)}</b><span class="xs mut">${x.t}</span></span>${I.chev}</button>`).join('')}</div>` : ''}
  <a class="banlink" href="#ban"><span>${I.warn}</span><div class="grow"><b>الممنوعات المعروفة</b><p class="xs">96 منتج بفنلندا بيهم خنزير أو جيلاتين</p></div>${I.chev}</a>`;
}
mk().then(m => { window.__STORES = m.STORES; if (location.hash === '#scan') reroute(); });
async function openStore(k) {
  const { MARKET, STORES } = await mk(), st = STORES.find(s => s[0] === k), all = MARKET[k] || [];
  const L = all.filter(x => mkFilter === 'all' || x.v === mkFilter || (mkFilter === 'pro' && x.p >= 8 && x.v === 'ok'));
  const cnt = v => all.filter(x => x.v === v).length;
  const html = `<div class="row"><button class="ib" data-close aria-label="رجوع">${I.back}</button><div class="grow"><h1>${st[1]} ${st[2]}</h1><p class="xs mut">${all.length} منتج مفحوص • ${st[3]}</p></div></div>
  <div class="chips">${[['all', 'الكل'], ['ok', '✓ حلال ' + cnt('ok')], ['mid', '⚠ مشكوك ' + cnt('mid')], ['no', '⛔ حرام ' + cnt('no')], ['pro', '💪 بروتين عالي']].map(([f, n]) => `<button class="${mkFilter === f ? 'on' : ''}" data-mkf="${f}:${k}">${n}</button>`).join('')}</div>
  <div class="mgrid2">${L.map(x => `<button class="mcard ${x.v}" data-mitem="${k}:${all.indexOf(x)}"><span class="pimg"><img src="${x.img}" alt="" loading="lazy"><i class="vb">${VB[x.v][0]}</i></span><b>${esc(x.n)}</b><span class="xs mut">${esc(x.b)}</span><span class="xs"><span class="vt ${x.v}">${VB[x.v][1]}</span>${x.p != null ? ` • <b class="num" style="color:var(--gold)">${x.p}g</b> بروتين` : ''}</span></button>`).join('') || '<p class="mut">ماكو منتجات بهالفلتر.</p>'}</div>`;
  const s = $('#screen'); if (!s.hidden && s.querySelector('.mgrid2')) { const y = s.scrollTop; s.innerHTML = `<div class="in">${html}</div>`; s.scrollTop = y; } else show(html);
}
async function openMItem(k, i) { const { MARKET } = await mk(); const x = MARKET[k][i]; show(productView(x, x.c), true); }
async function nameSearch() {
  const q = ($('#mq') || {}).value?.trim(); if (!q) return; const box = $('#mres'); box.innerHTML = '<p class="xs mut">دا أدوّر...</p>';
  const { MARKET } = await mk(), loc = Object.entries(MARKET).flatMap(([k, L]) => L.map((x, i) => [k, i, x])).filter(([, , x]) => (x.n + ' ' + x.b).toLowerCase().includes(q.toLowerCase())).slice(0, 12);
  let on = [];
  const qs = { search_terms: q, page_size: 15, fields: 'code,product_name,brands,image_front_url' };
  const cg = 'https://world.openfoodfacts.org/cgi/search.pl?' + new URLSearchParams(Object.assign({ search_simple: 1, json: 1, action: 'process' }, qs)); for (const u of [cg, cg, cg]) {  try { const r = await fetch(u); if (!r.ok) { await new Promise(z => setTimeout(z, 1500)); continue; } on = ((await r.json()).products || []).filter(h => h.product_name && h.code); if (on.length) break; } catch (e) {} }
  box.innerHTML = (loc.length || on.length) ? `<div class="slist" style="margin-top:10px">${loc.map(([k, i, x]) => `<button class="slot ex" data-mitem="${k}:${i}"><span class="sico">${VB[x.v][0]}</span><span class="stxt"><b>${esc(x.n)}</b><span class="xs mut">${esc(x.b)} • ${VB[x.v][1]}</span></span>${I.chev}</button>`).join('')}${on.map(h => `<button class="slot ex" data-bc="${h.code}">${h.image_front_url ? `<img src="${h.image_front_url}" alt="" style="width:46px;height:46px;object-fit:contain;background:#fff;border-radius:12px">` : '<span class="sico">🔎</span>'}<span class="stxt"><b>${esc(h.product_name)}</b><span class="xs mut">${esc([].concat(h.brands || []).join(', '))} • اضغط حتى أفحصه</span></span>${I.chev}</button>`).join('')}</div>` : '<p class="xs mut">ما لگيت شي. جرّب اسم ثاني أو صوّر الباركود.</p>';
}
async function decodeImage(file) {
  toast('دا أقرا الصورة...');
  try { const ZX = await loadZX(), r = new ZX.BrowserMultiFormatReader(), u = URL.createObjectURL(file); const res = await r.decodeFromImageUrl(u); URL.revokeObjectURL(u); lookupBC(res.getText()); }
  catch (e) { toast('ما گدرت أقرا الباركود. صوّره قريب وواضح'); }
}
function openScan() {
  show(`<div class="row"><button class="ib" data-back aria-label="رجوع">${I.back}</button><h2 class="grow">افحص منتج</h2></div>
  <div class="scanbox"><video id="scv" playsinline muted></video><div class="scanline"></div><p id="scmsg">وجّه الكاميرا على الباركود (الخطوط السودة)</p></div>
  <div class="card"><h3>أو اكتب رقم الباركود</h3><div class="row"><input class="field num" id="bcIn" inputmode="numeric" placeholder="6408430043019" dir="ltr"><button class="btn sm" data-bcgo>افحص</button></div></div>
  <p class="xs mut">المعلومات من قاعدة المنتجات المفتوحة (Open Food Facts). إذا المنتج مو موجود، اقرا المكونات بنفسك من خانة "اقرا الغلاف".</p>`, true);
  loadZX().then(ZX => {
    const v = $('#scv'); if (!v) return;
    zxR = new ZX.BrowserMultiFormatReader();
    zxR.decodeFromConstraints({ video: { facingMode: 'environment' } }, v, (r) => { if (r) { stopScan(); lookupBC(r.getText()); } }).catch(() => { const m = $('#scmsg'); if (m) m.textContent = 'ما گدرت أفتح الكاميرا. اسمح للكاميرا من إعدادات سفاري، أو اكتب الرقم.'; });
  }).catch(() => { const m = $('#scmsg'); if (m) m.textContent = 'الكاميرا ما اشتغلت. اكتب الرقم تحت.'; });
}
async function lookupBC(code) {
  code = String(code).replace(/\D/g, ''); if (code.length < 8) { toast('الرقم قصير'); return; }
  stopScan(); show(`<div class="row"><button class="ib" data-back aria-label="رجوع">${I.back}</button><h2>دا أفحص...</h2></div><div class="card"><p class="sm">رقم ${code}</p><div class="bar"><i style="width:60%" class="loading"></i></div></div>`, true);
  let p = null;
  try { const r = await fetch(`https://world.openfoodfacts.org/api/v2/product/${code}?fields=product_name,product_name_en,brands,image_front_url,ingredients_text,ingredients_text_fi,ingredients_text_en,ingredients_text_sv,ingredients_text_de,ingredients_text_fr,ingredients_tags,labels_tags,nutriments,quantity`); const j = await r.json(); if (j.status === 1 || j.product) p = j.product; } catch (e) {}
  if (!p || !(p.product_name || p.product_name_en || p.ingredients_text)) { const { MARKET } = await mk(); const hit = Object.entries(MARKET).flatMap(([k, L]) => L.map((x, i) => [k, i, x])).find(([, , x]) => x.c === code); if (hit) { openMItem(hit[0], hit[1]); return; }
    show(`<div class="row"><button class="ib" data-back aria-label="رجوع">${I.back}</button><h2>ما لگيته</h2></div><div class="warn">هذا المنتج مو موجود بالقاعدة العالمية، أو النت ضعيف. اقرا المكونات (Ainesosat / Ingredients) ودوّر على الكلمات الممنوعة.</div><button class="btn wide" data-banwords>شوف الكلمات الممنوعة</button>`, true); return; }
  const A = await analyzeP(p), n = p.nutriments || {};
  const x = { n: p.product_name_en || p.product_name, b: [].concat(p.brands || []).join(', '), img: p.image_front_url, q: p.quantity, v: A.v, h: A.h, d: A.d, i: A.i, hl: A.hl, k: n['energy-kcal_100g'], p: n.proteins_100g, cb: n.carbohydrates_100g, f: n.fat_100g, ing: A.ing };
  S.scans = [{ c: code, n: x.n || '', t: today(), r: x.v }].concat((S.scans || []).filter(z => z.c !== code)).slice(0, 30); save();
  show(productView(x, code), true);
}
function openBan(i) {
  const b = BAN[i];
  show(`<div class="row"><button class="ib" data-back aria-label="رجوع">${I.back}</button><h2 class="grow">${b.n}</h2></div>
  <div class="prod" style="height:280px;position:relative"><img src="img/${b.img}.webp" alt="" style="max-height:260px"><span class="stamp">ممنوع</span></div>
  <div class="danger"><span>${I.warn}</span><div><b>ليش ممنوع؟</b><p class="sm">${b.why}</p></div></div>
  <div class="card"><h3>المكتوب بالمكونات</h3><span class="fi" style="font-size:18px">${b.fi}</span><p class="xs mut">${b.b}</p></div>`, true);
}

/* ================= أنا ================= */
const VERSION = '18';
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
  const th = S.theme || 'light', hd = (S.health || {})[today()];
  show(`<div class="row"><button class="ib" data-close aria-label="رجوع">${I.back}</button><h1>الإعدادات</h1></div>
  <button class="sprof" data-profile><div class="ava big">${esc((S.name || 'ب')[0])}</div><div class="grow"><b>${esc(S.name || 'اكتب اسمك')}</b><small>${S.age ? AR(S.age) + ' سنة • ' : ''}${AR(S.h)} سم • هدفك ${AR(weightInfo().goal)} كغم</small></div>${I.chev}</button>
  <p class="sh">المظهر</p>
  <div class="sgrp"><div class="themes">${[['dark', 'غامق', I.moon], ['light', 'فاتح', I.sun], ['auto', 'تلقائي', '◐']].map(([k, n, ic]) => `<button class="${th === k ? 'on' : ''}" data-theme="${k}"><span class="tprev ${k}"><i></i><i></i></span>${n}</button>`).join('')}</div>
   ${row('✨', '#8e5cf7', 'حركة بين الخانات', 'حركة بسيطة لما تتنقل', 'data-anim', tgl(!S.noAnim))}</div>
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
/* ================= المظهر ================= */
function applyTheme() {
  const t = S.theme || 'light', dark = t === 'auto' ? matchMedia('(prefers-color-scheme: dark)').matches : t === 'dark';
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
const V = { home: vHome, course: vCourse, food: vFood, scan: vScan, supps: vSupps, ban: vBan, me: vMe };
const TABS = Object.keys(V); let lastTab = null;
function route() { if (SUS === null) refreshSus(); let h = location.hash.slice(1); if (h.startsWith('hk')) { const r = parseHK(decodeURIComponent(h.slice(3))); if (r) { saveHK(r); toast('وصلت أرقام الساعة ✓'); } history.replaceState(null, '', '#home'); h = 'home'; } if (!V[h]) h = 'home'; $('#app').innerHTML = V[h](); if (h === 'me') loadPhotos(); const a = $('#app'); a.classList.remove('fade', 'sl', 'sr'); if (lastTab !== h) { void a.offsetWidth; a.classList.add(lastTab == null ? 'fade' : TABS.indexOf(h) > TABS.indexOf(lastTab) ? 'sl' : 'sr'); } lastTab = h; document.querySelectorAll('nav a').forEach(a => a.classList.toggle('on', a.dataset.t === h)); }
let stack = [];
function show(html, push) { const sh = $('.sheet'); if (sh) sh.remove(); const s = $('#screen'); if (push && !s.hidden && s.innerHTML) stack.push(s.innerHTML); else { killAnims(); stack = []; } s.hidden = false; s.innerHTML = `<div class="in">${html}</div>`; s.scrollTop = 0; document.body.style.overflow = 'hidden'; }
function closeScreen(keep) { stopScan(); killAnims(); stack = []; const s = $('#screen'); s.hidden = true; s.innerHTML = ''; if (!keep) { document.body.style.overflow = ''; route(); } }
function back() { stopScan(); killAnims(); const s = $('#screen'); if (stack.length) { s.innerHTML = stack.pop(); s.scrollTop = 0; if (!$('#player').hidden) { s.hidden = true; renderPlayer(); } } else { closeScreen(!$('#player').hidden); if (!$('#player').hidden) renderPlayer(); } }
window.addEventListener('hashchange', () => { const s = $('#screen'); if (!s.hidden) { stopScan(); killAnims(); stack = []; s.hidden = true; s.innerHTML = ''; document.body.style.overflow = ''; } route(); });
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
  if (d.yt) { b.outerHTML = `<div class="video"><iframe src="https://www.youtube-nocookie.com/embed/${d.yt}?autoplay=1&playsinline=1&rel=0" title="فيديو شرح" allow="autoplay; encrypted-media; picture-in-picture; fullscreen" allowfullscreen></iframe></div>`; return; }
  if (d.eval != null) { openEval(); return; }
  if (d.weak) { b.classList.toggle('on'); const m = d.weak; EV.weak = EV.weak.includes(m) ? EV.weak.filter(x => x !== m) : [...EV.weak, m]; return; }
  if (d.feel) { document.querySelectorAll('[data-feel]').forEach(x => x.classList.toggle('on', x === b)); EV.feel = d.feel; return; }
  if ('evsubmit' in d) { submitEval(); return; }
  if (d.rec) { openRecipe(d.rec, d.slot); return; }
  if (d.food) { openFood(d.food); return; }
  if (d.fcat) { fdCat = d.fcat; openDB(); return; }
  if (d.sec) { openSection(d.sec, d.forslot); return; }
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
document.addEventListener('change', async e => { if (e.target.id === 'bcImg' && e.target.files[0]) { decodeImage(e.target.files[0]); e.target.value = ''; return; } if (e.target.id === 'impIn' && e.target.files[0]) { try { const o = JSON.parse(await e.target.files[0].text()); if (!o || !o.month) throw 0; S = Object.assign(def(), o); save(); applyTheme(); closeScreen(); toast('رجعت معلوماتك ✓'); } catch (er) { toast('الملف مو صحيح'); } return; } if (e.target.id === 'photoIn' && e.target.files[0]) { await savePhoto(e.target.files[0]); toast('انحفظت الصورة'); loadPhotos(); } });
document.addEventListener('input', e => { const t = e.target; if (t.id === 'fdq') { fdQ = t.value; const pos = t.selectionStart; openDB(); const n = $('#fdq'); if (n) { n.focus(); try { n.setSelectionRange(pos, pos); } catch (er) {} } return; } if (!SES) return; if (t.dataset.w != null) SES.sets[SES.k][+t.dataset.w].w = t.value; if (t.dataset.r != null) SES.sets[SES.k][+t.dataset.r].r = t.value; });
route();

/* ================= التحديث التلقائي ================= */
if ('serviceWorker' in navigator) {
  navigator.serviceWorker.register('sw.js', { updateViaCache: 'none' }).then(reg => {
    reg.update();
    document.addEventListener('visibilitychange', () => { if (document.visibilityState === 'visible') reg.update(); });
  }).catch(() => {});
  let reloaded = false;
  navigator.serviceWorker.addEventListener('controllerchange', () => { if (reloaded || SES) return; reloaded = true; location.reload(); });
}
