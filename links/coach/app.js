// مدرّبي: منطق التطبيق
import { EX, REST_DAY, DAY_NAMES, DAY_IMG, MONTHS, FD, MEALS, IBS, SUPPS, SCHEDULE } from './data.js';
import { BODY } from './bodymap.js';

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
  share: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M12 3v12M7.5 7.5 12 3l4.5 4.5M5 12v8h14v-8"/></svg>',
};
document.querySelectorAll('[data-i]').forEach(e => e.innerHTML = I[e.dataset.i]);

/* ================= أدوات ================= */
const $ = s => document.querySelector(s);
const AR = n => String(n).replace(/\d/g, d => '٠١٢٣٤٥٦٧٨٩'[d]);
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
function tplFor(n) { return n <= 3 ? MONTHS[n - 1] : MONTHS[n % 2 ? 1 : 2]; }
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
function setsAt(item, i) { return (S.month.n === 1 && i < 14 && !EX[item.id].sec) ? Math.min(2, item.s) : item.s; }
function dayItems(i) { const t = dayType(i); return t === 'R' ? REST_DAY.map(id => ({ id, s: 1, r: EX[id].sec ? [30, 30] : [10, 10], rest: 15, w: 0 })) : S.month.plan[t]; }

/* ================= الحسابات ================= */
const curW = () => S.weights.length ? S.weights[S.weights.length - 1].w : +S.w || 52;
function targets() { const w = curW(), h = +S.h || 168, a = +S.age || 20; let k = (10 * w + 6.25 * h - 5 * a + 5) * 1.55 + 400; const adj = S.evals.length ? S.evals[S.evals.length - 1].kcalAdj || 0 : 0; k = Math.round((k + adj) / 50) * 50; return { k, p: Math.round(w * 2), water: Math.round(w * .045 * 2) / 2 }; }
function itemVal(k, a) { const f = FD[k], m = f.pc ? a : a / 100; return { k: f.k * m, p: f.p * m, c: f.c * m, f: f.f * m }; }
function optVal(o) { return o.it.reduce((s, [k, a]) => { const v = itemVal(k, a); return { k: s.k + v.k, p: s.p + v.p, c: s.c + v.c, f: s.f + v.f }; }, { k: 0, p: 0, c: 0, f: 0 }); }
function weekHist() { const now = new Date(); now.setHours(0, 0, 0, 0); const st = new Date(now); st.setDate(st.getDate() - 6); return S.hist.filter(h => new Date(h.d + 'T12:00') >= st); }
function muscleCount() { const c = {}; weekHist().forEach(h => (h.mus || []).forEach(m => c[m] = (c[m] || 0) + 1)); return c; }
function streak() { const ds = new Set(S.hist.map(h => h.d)); let n = 0; const d = new Date(); for (let i = 0; i < 60; i++) { const k = dk(d); if (ds.has(k)) n++; else if (i > 0) { const t = dayType(curDay()); if (!(i === 1 && t === 'R')) break; } d.setDate(d.getDate() - 1); } return n; }

/* ================= خريطة العضلات ================= */
function bodySvg(side, counts, big) {
  const col = m => { const n = counts[m] || 0; return n >= 2 ? 'var(--g)' : n === 1 ? 'var(--g2)' : '#26332b'; };
  return `<svg viewBox="0 0 100 200" role="img" aria-label="${side === 'front' ? 'العضلات من گدام' : 'العضلات من ورا'}">${BODY[side].map(([m, ps]) => ps.map(p => `<polygon points="${p}" fill="${['head', 'neck', 'knees', 'adductor', 'abductor'].includes(m) ? '#1a241e' : col(m)}" stroke="#3a4a40" stroke-width=".4"/>`).join('')).join('')}</svg>`;
}

/* ================= الرئيسية ================= */
const MN = { chest: 'الصدر', back: 'الظهر', shoulders: 'الكتف', biceps: 'الأمامية', triceps: 'الخلفية', quads: 'الفخذ', hamstrings: 'الفخذ الخلفي', glutes: 'المؤخرة', calves: 'السمانة', abs: 'البطن', forearms: 'الساعد', lowerback: 'أسفل الظهر' };
function vHome() {
  const c = curDay(), t = c < MDAYS ? dayType(c) : null, cnt = muscleCount(), wh = weekHist(), T = targets();
  const sel = S.meals[today()] || {}, pro = MEALS.reduce((a, m) => sel[m.k] != null && m.o[sel[m.k]] ? a + optVal(m.o[sel[m.k]]).p : a, 0);
  const hr = new Date().getHours(), greet = hr < 12 ? 'صباح الخير' : hr < 18 ? 'هلا' : 'مساء الخير';
  const doneToday = S.hist.some(h => h.d === today());
  const hero = t === null ? `<div class="hero"><div class="wm">الشهر خلص</div><div class="txt"><span class="lab">كفو عليك</span><h1>قيّم شهرك</h1><p class="sm">حتى نبنيلك الشهر الجاي</p></div><img src="img/ex3d/month.jpg" alt=""><button class="go" data-eval aria-label="قيّم الشهر">${I.arrow}</button></div>`
    : `<div class="hero"><div class="wm">${t === 'R' ? 'راحة' : 'تمرين'}</div><div class="txt"><span class="lab">${doneToday ? 'خلصت تمرين اليوم ✓' : 'تمرين اليوم • اليوم ' + AR(c + 1)}</span><h1>${DAY_NAMES[t]}</h1><p class="sm">${t === 'R' ? 'مشي 30 دقيقة + تمارين الوگفة' : AR(dayItems(c).length) + ' تمارين • 50 دقيقة تقريباً'}</p></div><img src="img/ex3d/${DAY_IMG[t]}.jpg" alt=""><button class="go" data-day="${c}" aria-label="ابدأ">${I.arrow}</button></div>`;
  // الأسبوع
  const now = new Date(); const wd = []; const ds = new Set(S.hist.map(h => h.d));
  for (let i = 6; i >= 0; i--) { const d = new Date(now); d.setDate(d.getDate() - i); wd.push(d); }
  const DN = ['أحد', 'اثن', 'ثلا', 'أرب', 'خمي', 'جمع', 'سبت'];
  const bars = wd.map(d => { const k = dk(d), s = S.hist.filter(h => h.d === k).reduce((a, h) => a + (h.sets || 0), 0); return { k, s, n: DN[d.getDay()] }; });
  const mx = Math.max(10, ...bars.map(b => b.s));
  const medals = [[S.hist.length >= 1, 'أول تمرين', 'star'], [streak() >= 3, '3 أيام ورا بعض', 'fire'], [wh.filter(h => h.t !== 'R').length >= 3, 'أسبوع كامل', 'trophy'], [S.hist.filter(h => h.t !== 'R').length >= 10, '10 تمارين', 'bolt'], [S.evals.length >= 1, 'شهر كامل', 'trophy'], [curW() - (S.weights[0]?.w || curW()) >= 1, '+1 كيلو', 'scale'], [curW() - (S.weights[0]?.w || curW()) >= 3, '+3 كيلو', 'scale']];
  return `<div class="top"><div class="ava">${esc((S.name || 'ب')[0])}</div><div class="grow"><p class="sm mut">${greet} 👋</p><h2>${esc(S.name || 'يا بطل')}</h2></div><span class="streak">${I.fire}<span class="num">${AR(streak())}</span></span></div>
  ${installCard()}
  ${hero}
  <div class="weekchips">${wd.map(d => `<div class="wc ${ds.has(dk(d)) ? 'done' : ''} ${dk(d) === today() ? 'today' : ''}"><span>${DN[d.getDay()]}</span><b class="num">${AR(d.getDate())}</b></div>`).join('')}</div>
  <div class="tiles"><div class="tile">${I.dumb}<b class="num">${AR(wh.filter(h => h.t !== 'R').length)}</b><span>تمارين هالأسبوع</span></div><div class="tile">${I.egg}<b class="num">${AR(Math.round(pro))}</b><span>من ${AR(T.p)} غ بروتين</span></div><div class="tile">${I.scale}<b class="num">${AR(curW())}</b><span>كيلو وزنك</span></div></div>
  <div class="card"><div class="sec-h"><h2>عضلاتك هالأسبوع</h2><span class="pill g">الشهر ${AR(S.month.n)}</span></div>
   <div class="bodymap">${bodySvg('front', cnt)}${bodySvg('back', cnt)}</div>
   <div class="legend"><span><i style="background:var(--g)"></i>مرتين أو أكثر</span><span><i style="background:var(--g2)"></i>مرة وحدة</span><span><i style="background:#26332b"></i>بعد ما اشتغلت</span></div>
   ${Object.keys(cnt).length ? `<p class="xs mut">اشتغلت: ${Object.keys(cnt).filter(m => MN[m]).map(m => MN[m]).join('، ')}</p>` : '<p class="xs mut">أول ما تخلص تمرين، العضلات تتلوّن هنا.</p>'}</div>
  <div class="card"><div class="sec-h"><h2>السِتات بالأسبوع</h2><span class="xs mut num">${AR(bars.reduce((a, b) => a + b.s, 0))} سِت</span></div>
   <div class="bars">${bars.map(b => `<div><i class="${b.k === today() ? 'on' : ''}" style="height:${Math.max(6, b.s / mx * 100)}%"></i><span>${b.n}</span></div>`).join('')}</div></div>
  <div class="sec-h"><h2>ميدالياتك</h2></div>
  <div class="medals">${medals.map(([on, n, ic]) => `<div class="medal ${on ? '' : 'off'}"><span class="c">${I[ic]}</span>${n}</div>`).join('')}</div>`;
}
function installCard() {
  const sa = window.navigator.standalone || matchMedia('(display-mode: standalone)').matches;
  if (sa || S.hideInstall) return '';
  return `<div class="install"><b class="d">خلّيه تطبيق على شاشة الآيفون</b><p class="sm">افتح الرابط بسفاري ← اضغط زر المشاركة <span style="display:inline-flex;width:18px;vertical-align:-3px;color:var(--g)">${I.share}</span> ← "إضافة إلى الشاشة الرئيسية".</p><button class="btn ghost sm" data-hideinstall>سوّيتها</button></div>`;
}

/* ================= الكورس ================= */
let weekSel = null;
function vCourse() {
  const c = curDay(), M = S.month, wk = weekSel ?? Math.min(3, Math.floor(Math.min(c, MDAYS - 1) / 7)), doneN = Object.keys(M.done).length;
  let days = '';
  for (let i = wk * 7; i < wk * 7 + 7; i++) {
    const t = dayType(i), it = dayItems(i), cls = ['dcard', t === 'R' ? 'rest' : '', M.done[i] ? 'done' : '', i === c ? 'now' : ''].join(' ');
    days += `<button class="${cls}" data-day="${i}"><img src="img/ex3d/${DAY_IMG[t]}.jpg" alt="" loading="lazy"><div class="grow"><span class="n">اليوم ${AR(i + 1)}</span><h3>${DAY_NAMES[t]}</h3><p class="xs mut">${t === 'R' ? 'مشي + تمارين الوگفة' : it.map(x => EX[x.id].n).slice(0, 3).join('، ') + '...'}</p></div><span class="st">${M.done[i] ? I.check : i === c ? I.play : `<span class="xs num">${AR(it.length)}</span>`}</span></button>`;
  }
  return `<h1>الكورس</h1>
  <div class="month"><img src="img/ex3d/${DAY_IMG.A}.jpg" alt=""><span class="pill g" style="align-self:flex-start">الشهر ${AR(M.n)}</span><h1>${M.name}</h1><p class="sm mut">${M.goal}</p><div class="bar"><i style="width:${doneN / MDAYS * 100}%"></i></div><p class="xs mut num">خلصت ${AR(doneN)} من ${AR(MDAYS)} يوم</p></div>
  <div class="card"><b class="d">نظام الشهر</b><div class="steps sm"><p>صدر + أمامية</p><p>ظهر + خلفية</p><p>أكتاف + رجل</p><p>راحة، وترجع للأول</p></div><p class="xs mut">كل عضلة ترتاح 3 أيام. ${M.n === 1 ? 'أول أسبوعين سِتين بس حتى تتعلم.' : 'الأوزان مبنية على تقييم الشهر الي فات.'}</p></div>
  <div class="wtabs">${[0, 1, 2, 3].map(w => `<button class="${w === wk ? 'on' : ''}" data-wk="${w}">الأسبوع ${AR(w + 1)}</button>`).join('')}</div>
  <div class="col">${days}</div>
  <div class="card"><h3>خلصت الشهر؟</h3><p class="sm mut">قيّم شهرك (شكد شلت، وزنك، شنو العضلة الضعيفة) وأنا أبنيلك الشهر الجاي على هذا الأساس.</p><button class="btn ${c >= MDAYS ? '' : 'ghost'} wide" data-eval>قيّم الشهر وابدي الجاي</button></div>`;
}

/* ================= شاشة اليوم ================= */
let SES = null;
function openDay(i) {
  if (i >= MDAYS) { openEval(); return; }
  const t = dayType(i), it = dayItems(i);
  show(`<div class="row"><button class="ib" data-close aria-label="رجوع">${I.back}</button><div class="grow"><p class="xs mut">اليوم ${AR(i + 1)} • الشهر ${AR(S.month.n)}</p><h2>${DAY_NAMES[t]}</h2></div></div>
  <div class="month" style="min-height:200px"><img src="img/ex3d/${DAY_IMG[t]}.jpg" alt=""><h1>${DAY_NAMES[t]}</h1><p class="sm mut">${t === 'R' ? 'مشي 30 دقيقة، وهاي التمارين 10 دقايق قبل النوم.' : 'إحماء: 5 دقايق مشي سريع أو دراجة، وأول تمرين سِت خفيف بنص الوزن.'}</p></div>
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
    const a = createAnimator(canvas, id, { theme: 'green', onPhase: p => { if (phEl) phEl.textContent = p === 0 ? E.phases[0] : p === 1 ? E.phases[1] : p === 2 ? (E.hold ? E.phases[2] : 'اعصر') : 'استعد'; } });
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
  ${e.sec ? '' : `<div class="card"><p class="sm"><b>الوزن الصح:</b> تخلّص العدّات وتحس تگدر تسوي 2 بعد بس. إذا كلش سهل زيد، وإذا الحركة خربت نقّص.</p></div>`}
  ${e.yt ? `<button class="video" data-yt="${e.yt}"><img src="https://i.ytimg.com/vi/${e.yt}/hqdefault.jpg" alt=""><span class="play"><span>${I.play}</span></span><span class="cap">شرح بالعربي من مدرّب (بيه صوت)</span></button>` : ''}`;
}
function openEx(id) { killAnims(); show(`<div class="row"><button class="ib" data-back aria-label="رجوع">${I.back}</button></div>${exInfo(id)}`, true); mountAnim($('#ac'), id, $('#aph')); }

/* ================= مشغّل التمرين ================= */
function startDay(i) {
  const it = dayItems(i);
  SES = { i, k: 0, items: it, sets: it.map(x => Array.from({ length: setsAt(x, i) }, () => ({ w: x.w || '', r: EX[x.id].sec ? x.r[0] : x.r[1], ok: false }))) };
  closeScreen(true); renderPlayer();
}
function renderPlayer() {
  killAnims();
  const P = $('#player'), x = SES.items[SES.k], e = EX[x.id], sets = SES.sets[SES.k], n = SES.items.length;
  const doneEx = SES.sets.map(s => s.every(z => z.ok)); const C = 2 * Math.PI * 22, frac = (SES.k + 1) / n;
  const cur = sets.findIndex(s => !s.ok);
  P.hidden = false; document.body.style.overflow = 'hidden';
  P.innerHTML = `<div class="stage"><canvas id="pc"></canvas><div class="fade"></div><div class="ov"><div class="row between"><button class="ib" data-pclose aria-label="طلّع">${I.x}</button><div class="row"><button class="ib" data-slow aria-label="أبطأ">${I.slow}</button><button class="ib" data-info="${x.id}" aria-label="الشرح">${I.info}</button></div></div>
   <span class="ph"><i></i><span id="pph">استعد</span></span></div></div>
  <div class="ploop">
   <div class="row between"><div><h2>${e.n}${e.star ? ' ⭐' : ''}</h2><p class="xs mut">${e.gym}</p></div><span class="pill g num">${AR(sets.length)} × ${rng(x.r)}${e.sec ? ' ث' : ''}</span></div>
   ${sets.map((s, j) => `<div class="set ${s.ok ? 'done' : ''}"><span class="i ${j === cur ? 'cur' : ''}">${j === cur ? '●' : AR(j + 1)}</span>${e.sec || !x.w && !e.w0 ? `<div class="pillin"><span>${e.sec ? 'وزن الجسم' : 'بدون وزن'}</span></div>` : `<label class="pillin"><input inputmode="decimal" data-w="${j}" value="${s.w}" aria-label="الوزن"><span>كغم</span></label>`}<label class="pillin"><input inputmode="numeric" data-r="${j}" value="${s.r}" aria-label="العدّات"><span>${e.sec ? 'ث' : '×'}</span></label><button class="ok" data-ok="${j}" aria-label="خلصت السِت">${I.check}</button></div>`).join('')}
   <p class="xs mut" style="text-align:center">بعد كل سِت اضغط ✓ ويبدي وكت الراحة (${AR(x.rest)} ثانية)</p>
   ${SES.k < n - 1 ? `<button class="btn wide" data-pnext>التمرين الجاي</button>` : `<button class="btn wide" data-pfinish>خلصت اليوم 🎉</button>`}
   <div style="height:8px"></div>
  </div>
  <div class="pbar"><div class="ringp"><svg viewBox="0 0 52 52"><circle cx="26" cy="26" r="22" stroke="#1f2c23" stroke-width="5" fill="none"/><circle cx="26" cy="26" r="22" stroke="var(--g)" stroke-width="5" fill="none" stroke-linecap="round" stroke-dasharray="${C}" stroke-dashoffset="${C * (1 - frac)}"/></svg><b class="num">${AR(SES.k + 1)}/${AR(n)}</b></div>
   <div class="grow"><b class="d">${e.n}</b><p class="xs mut">${MN[e.m[0]] || ''}</p></div>
   <div class="dots">${SES.items.map((_, j) => `<button class="${j === SES.k ? 'on' : ''} ${doneEx[j] ? 'ok' : ''}" data-pgo="${j}">${AR(j + 1)}</button>`).join('')}</div></div>`;
  mountAnim($('#pc'), x.id, $('#pph'));
}
let restT, ac;
function rest(sec) {
  clearInterval(restT); let left = sec, all = sec; const o = document.createElement('div'); o.className = 'rest-ov'; document.body.append(o); const C = 2 * Math.PI * 100;
  const paint = () => { o.innerHTML = `<h2>ارتاح وتنفّس</h2><div class="ring"><svg viewBox="0 0 230 230"><circle cx="115" cy="115" r="100" stroke="#1f2c23" stroke-width="14" fill="none"/><circle cx="115" cy="115" r="100" stroke="#62e87a" stroke-width="14" fill="none" stroke-linecap="round" stroke-dasharray="${C}" stroke-dashoffset="${C * (1 - left / all)}"/></svg><b class="num">${AR(left)}</b></div><p class="mut sm">اشرب شوية مي</p><div class="row"><button class="btn ghost" data-plus>+15 ثانية</button><button class="btn" data-skip>كمّل</button></div>`; };
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
  show(`<div class="col" style="min-height:75vh;justify-content:center;align-items:center;text-align:center;gap:18px"><div class="medal" style="width:auto;padding:20px 28px"><span class="c" style="width:84px;height:84px">${I.trophy}</span></div><h1>عاشت إيدك يا بطل!</h1><p class="mut">خلصت اليوم ${AR(i + 1)} من الشهر ${AR(S.month.n)}${sets ? ' • ' + AR(sets) + ' سِت' : ''}</p><div class="card" style="text-align:right;width:100%"><p class="sm">${dayType(i) === 'R' ? 'باچر تمرين، نام زين الليلة.' : 'هسه: سكوب البروتين خلال ساعتين، وجبة زينة، ونوم 8 ساعات.'}</p></div><button class="btn wide" data-close>رجوع</button></div>`);
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
let foodView = 'meals', openOpt = {};
function plate(o, on) { const ims = [...new Set(o.it.map(([k]) => FD[k].im))].slice(0, 3); return `<div class="plate">${ims.length ? ims.map(x => `<img src="img/food/${x}.webp" alt="" loading="lazy">`).join('') : `<span style="font-size:34px">💧</span>`}${on ? `<span class="chk">${I.check}</span>` : ''}</div>`; }
function vFood() {
  const T = targets(), sel = S.meals[today()] || {};
  const tot = MEALS.reduce((a, m) => { if (sel[m.k] == null || !m.o[sel[m.k]]) return a; const v = optVal(m.o[sel[m.k]]); return { k: a.k + v.k, p: a.p + v.p }; }, { k: 0, p: 0 });
  const seg = `<div class="seg"><button class="${foodView === 'meals' ? 'on' : ''}" data-fv="meals">وجباتي</button><button class="${foodView === 'ibs' ? 'on' : ''}" data-fv="ibs">القولون</button><button class="${foodView === 'halal' ? 'on' : ''}" data-fv="halal">حلال بفنلندا</button></div>`;
  let body = '';
  if (foodView === 'meals') {
    body = `<div class="card"><div class="row between sm"><span>اخترت اليوم</span><span class="num mut">${AR(Math.round(tot.k))} / ${AR(T.k)} سعرة</span></div><div class="bar"><i style="width:${Math.min(100, tot.k / T.k * 100)}%"></i></div><div class="row between sm"><span>بروتين</span><span class="num mut">${AR(Math.round(tot.p))} / ${AR(T.p)} غم</span></div><div class="bar"><i style="width:${Math.min(100, tot.p / T.p * 100)}%;background:var(--gold)"></i></div><p class="xs mut">كل الأكل هنا مختار للقولون العصبي، وبدون لاكتوز، وحلال، وموجود بفنلندا. اختار وحدة من كل وجبة.</p></div>`;
    body += MEALS.map(m => {
      const s = sel[m.k], show = openOpt[m.k] ?? s ?? 0, o = m.o[show], v = optVal(o);
      return `<div class="col"><div class="meal-h"><span class="ic">${I[m.icon]}</span><div class="grow"><h2>${m.n}</h2><p class="xs mut">${m.t} • ${AR(m.o.length)} خيارات</p></div>${s != null ? '<span class="pill g">✓ اخترت</span>' : ''}</div>
      <div class="opts">${m.o.map((x, j) => { const xv = optVal(x); return `<button class="opt ${s === j ? 'on' : ''}" data-oo="${m.k}:${j}" style="${show === j ? 'border-color:' + (s === j ? 'var(--g)' : 'var(--mut)') : ''}">${plate(x, s === j)}<b>${x.n}</b><span class="k num">${AR(Math.round(xv.k))} سعرة • ${AR(Math.round(xv.p))} غ بروتين</span></button>`; }).join('')}</div>
      <div class="detail"><div class="row between"><h3>${o.n}</h3><button class="btn sm ${s === show ? 'ghost' : ''}" data-pick="${m.k}:${show}">${s === show ? 'اخترتها ✓' : 'اختارها'}</button></div>
       ${o.it.length ? `<div class="items">${o.it.map(([k, a]) => `<p><span>${FD[k].n}<span class="fi">${FD[k].fi}</span></span><span class="num">${AR(a)} ${FD[k].u || (FD[k].pc ? 'حبة' : 'غم')}</span></p>`).join('')}</div>` : ''}
       <div class="steps sm">${o.prep.map(p => `<p>${p}</p>`).join('')}</div>
       ${o.it.length ? `<div class="macro"><span class="pill num">${AR(Math.round(v.k))} سعرة</span><span class="pill num" style="color:var(--gold)">${AR(Math.round(v.p))} غ بروتين</span><span class="pill num">${AR(Math.round(v.c))} غ كارب</span><span class="pill num">${AR(Math.round(v.f))} غ دهون</span></div>` : ''}</div></div>`;
    }).join('');
    body += `<div class="warn">اشتري ميزان مطبخ رخيص (<span class="fi" style="display:inline">keittiövaaka</span>) ووزّن التمن والدجاج أول أسبوعين. الأرقام تقريبية.</div>`;
  } else if (foodView === 'ibs') {
    body = `<div class="card"><h2>شنو تقلل منه</h2><p class="xs mut">هاي الأشياء أكثر شي تنفخ القولون العصبي. الطريقة اسمها "قليل التخمّر" ويستعملها أطباء الهضم.</p><div class="bad sm col">${IBS.avoid.map(([a, b]) => `<p><span><b>${a}:</b> ${b}</span></p>`).join('')}</div></div>
    <div class="card"><h2>عادات تريّح بطنك</h2><div class="good sm col">${IBS.tips.map(t => `<p>${t}</p>`).join('')}</div></div>
    <div class="warn">كل جسم يختلف. إذا أكلة من الأكل المسموح نفختك، شيلها وگلي. والطبيب أو أخصائي التغذية هو الي يحدد خطتك الأخيرة.</div>`;
  } else {
    body = `<div class="card"><h2>كلمات بالغلاف معناها حرام</h2><p class="xs mut">اقرا المكونات (Ainesosat)، وإذا لگيت وحدة منها لا تشتري.</p><div class="bad sm col">${[['sianliha / sika / possu', 'لحم خنزير'], ['pekoni', 'بيكون'], ['kinkku', 'هام (خنزير)'], ['nakki / makkara', 'نقانق، أغلبها خنزير'], ['liivate / gelatiini / E441', 'جيلاتين، غالباً خنزير'], ['silava / laardi', 'شحم خنزير'], ['alkoholi / viini', 'كحول']].map(([a, b]) => `<p><span><b class="fi" style="display:inline">${a}</b> = ${b}</span></p>`).join('')}</div></div>
    <div class="card"><h2>اللحم والدجاج</h2><div class="good sm col"><p>اشتري من المحلات العربية والتركية (مكتوب Halal)</p><p>بعض فروع K-Citymarket وPrisma بيها رف حلال</p><p>السمك والبيض والرَهكا كلها حلال وبيها بروتين عالي</p></div></div>`;
  }
  return `<h1>الأكل</h1>
  <div class="tiles"><div class="tile">${I.fire}<b class="num">${AR(T.k)}</b><span>سعرة باليوم</span></div><div class="tile"><span style="color:var(--gold);width:22px;display:block">${I.egg}</span><b class="num">${AR(T.p)}</b><span>غرام بروتين</span></div><div class="tile"><span style="color:var(--blue);width:22px;display:block">${I.drop}</span><b class="num">${AR(T.water)}</b><span>لتر مي</span></div></div>
  ${seg}${body}`;
}

/* ================= المكملات ================= */
function vSupps() {
  const d = S.supp[today()] || {}, minor = +S.age && +S.age < 18;
  return `<h1>المكملات</h1>
  <div class="card"><h2>جدولك اليومي</h2><div class="timeline">${SCHEDULE.map(([t, w, ic]) => `<div class="tl"><span class="ic">${I[ic]}</span><div><b class="d">${t}</b><p class="sm mut">${w}</p></div></div>`).join('')}</div><p class="xs mut">قبل التمرين ما تحتاج أي مكمّل. كُل وجبة قبله بساعة أو ساعتين وبس.</p></div>
  ${minor ? '<div class="warn"><b>عمرك أقل من 18:</b> لا تاخذ كرياتين ولا بروتين قبل ما تسأل طبيب.</div>' : ''}
  ${SUPPS.map(s => `<div class="card"><div class="prod"><img src="img/supp/${s.img}.webp" alt="${esc(s.prod)}" loading="lazy"></div>
   <div><span class="pill" style="color:${s.col}">${s.tag}</span><h2 style="margin-top:6px">${s.n}</h2><span class="fi">${esc(s.prod)}</span></div>
   <div class="kv"><div><span>شكد</span><b>${s.dose}</b></div><div><span>وكت</span><b>${s.when}</b></div><div><span>يوم الراحة</span><b>${s.rest}</b></div><div><span>الحد</span><b>${s.max}</b></div></div>
   <p class="sm">${s.why}</p>
   <div class="row wrap">${s.where.map(w => `<span class="pill">🛒 ${w}</span>`).join('')}</div>
   ${minor && s.adult ? '' : `<button class="took ${d[s.id] ? 'on' : ''}" data-took="${s.id}">${d[s.id] ? I.check + ' أخذته اليوم' : 'اضغط لما تاخذه اليوم'}</button>`}</div>`).join('')}
  <div class="card" style="border-color:rgba(255,77,94,.4)"><h2>ابتعد عنها</h2><div class="bad sm col"><p>الإبر والهرمونات والمنشطات</p><p>حبوب فتح الشهية والتسمين</p><p>بروتين بنكهات ومحليات صناعية كثيرة (تنفخ القولون)</p><p>كبسولات جيلاتين (liivate) إذا مو مكتوب عليها حلال</p></div></div>
  <p class="xs mut">تثقيف عام مو وصفة طبية. اسأل الطبيب أو الصيدلي قبل أي مكمّل، خصوصاً ويا القولون. الأحسن تسوي فحص دم: فيتامين د، B12، الحديد.</p>`;
}

/* ================= أنا ================= */
function vMe() {
  const W = S.weights.length ? S.weights : [{ d: S.month.start, w: +S.w || 52 }], last = W[W.length - 1].w, diff = +(last - W[0].w).toFixed(1);
  return `<h1>أنا</h1>
  <div class="card"><div class="sec-h"><h2>وزني</h2><span class="pill g">الهدف ٦٢ كغم</span></div>
   <div class="tiles"><div class="tile"><span>هسه</span><b class="num">${AR(last)}</b><span>كغم</span></div><div class="tile"><span>زاد</span><b class="num" dir="ltr">${diff > 0 ? '+' : ''}${AR(diff)}</b><span>كغم</span></div><div class="tile"><span>باقي</span><b class="num">${AR(Math.max(0, +(62 - last).toFixed(1)))}</b><span>كغم</span></div></div>
   <div class="chart">${chart(W)}</div>
   <div class="row"><input class="field" id="wIn" inputmode="decimal" placeholder="وزنك اليوم" aria-label="وزنك اليوم"><button class="btn sm" data-addw>سجّل</button></div>
   <p class="xs mut">وزّن نفسك مرة بالأسبوع، الصبح قبل الأكل. الهدف ربع لنص كيلو بالأسبوع.</p></div>
  <div class="card"><h2>معلوماتي</h2><label class="f">اسمك (للترحيب)<input class="field" id="pN" value="${esc(S.name)}"></label><div class="row"><label class="f grow">عمري<input class="field" id="pA" inputmode="numeric" value="${esc(S.age)}" placeholder="مثلاً 22"></label><label class="f grow">طولي<input class="field" id="pH" inputmode="numeric" value="${S.h}"></label></div><button class="btn ghost" data-saveme>احفظ</button></div>
  ${S.evals.length ? `<div class="card"><h2>تقييماتي</h2>${S.evals.map(e => `<div class="row between sm"><span>الشهر ${AR(e.month)}</span><span class="mut num">${AR(e.w)} كغم • ${e.feel === 'easy' ? 'سهل' : e.feel === 'hard' ? 'صعب' : 'مناسب'}</span></div>`).join('')}</div>` : ''}
  <div class="card"><h2>قواعد صحتك</h2><div class="good sm col"><p>الوجع الخفيف بالعضلة بعد يومين طبيعي، والوجع الحاد بالمفصل لا: وگّف.</p><p>دوخة أو وجع صدر أو ضيق نفس: وگّف وروح للطبيب.</p><p>نام 7-9 ساعات. العضلة تكبر وانت نايم.</p><p>القولون يتأثر بالتوتر والنوم، فخلّي روتينك ثابت.</p></div></div>
  <div class="card"><h2>منين المعلومات</h2><div class="steps xs"><p>الجمعية الدولية للتغذية الرياضية: البروتين 1.6-2.2 غم لكل كيلو، والكرياتين 3-5 غم.</p><p>طريقة "قليل التخمّر" للقولون العصبي من جامعة موناش.</p><p>توصيات فيتامين د الفنلندية، وقيم الأكل التقريبية من جداول Fineli.</p><p>معلومات المنتجات من صفحاتها بمحلات Prisma وKärkkäinen.</p></div></div>
  <div class="card"><h2>نسخة احتياطية</h2><p class="xs mut">معلوماتك محفوظة بموبايلك بس. انسخ الكود واحفظه بالملاحظات.</p><textarea id="bk" readonly>${esc(JSON.stringify(S))}</textarea><button class="btn ghost sm" data-copy>انسخ الكود</button><textarea id="rs" placeholder="الصق الكود هنا حتى ترجّع معلوماتك"></textarea><button class="btn ghost sm" data-restore>رجّع معلوماتي</button></div>
  <p class="xs mut" style="text-align:center">التطبيق يتحدث لحاله كل ما تفتحه.</p>`;
}
function chart(W) {
  const p = W.slice(-10), v = p.map(x => x.w).concat([62]), lo = Math.floor(Math.min(...v) - 1), hi = Math.ceil(Math.max(...v) + 1), w = 320, h = 140, X = i => 34 + (p.length < 2 ? (w - 44) / 2 : i * (w - 44) / (p.length - 1)), Y = x => 12 + (hi - x) / (hi - lo) * (h - 24);
  let g = ''; for (let x = lo; x <= hi; x += Math.max(1, Math.round((hi - lo) / 4))) g += `<line x1="34" x2="${w - 6}" y1="${Y(x)}" y2="${Y(x)}" stroke="#22302a"/><text x="28" y="${Y(x) + 4}" fill="#8b9b92" font-size="10" text-anchor="end">${x}</text>`;
  const ln = p.map((x, i) => `${X(i)},${Y(x.w)}`).join(' ');
  return `<svg viewBox="0 0 ${w} ${h}" role="img" aria-label="رسم وزنك">${g}<line x1="34" x2="${w - 6}" y1="${Y(62)}" y2="${Y(62)}" stroke="#62e87a" stroke-dasharray="4 4" opacity=".6"/><polyline points="${ln}" fill="none" stroke="#62e87a" stroke-width="3" stroke-linejoin="round"/>${p.map((x, i) => `<circle cx="${X(i)}" cy="${Y(x.w)}" r="4" fill="#62e87a"/>`).join('')}</svg>`;
}

/* ================= التنقل ================= */
const V = { home: vHome, course: vCourse, food: vFood, supps: vSupps, me: vMe };
function route() { let h = location.hash.slice(1); if (!V[h]) h = 'home'; $('#app').innerHTML = V[h](); document.querySelectorAll('nav a').forEach(a => a.classList.toggle('on', a.dataset.t === h)); }
let stack = [];
function show(html, push) { const s = $('#screen'); if (push) stack.push(s.innerHTML); else { killAnims(); stack = []; } s.hidden = false; s.innerHTML = `<div class="in">${html}</div>`; s.scrollTop = 0; document.body.style.overflow = 'hidden'; }
function closeScreen(keep) { killAnims(); stack = []; const s = $('#screen'); s.hidden = true; s.innerHTML = ''; if (!keep) { document.body.style.overflow = ''; route(); } }
function back() { killAnims(); const s = $('#screen'); if (stack.length) { s.innerHTML = stack.pop(); s.scrollTop = 0; if (!$('#player').hidden) { s.hidden = true; renderPlayer(); } } else { closeScreen(!$('#player').hidden); if (!$('#player').hidden) renderPlayer(); } }
window.addEventListener('hashchange', route);
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
  if (d.wk != null) { weekSel = +d.wk; reroute(); return; }
  if (d.eval != null) { openEval(); return; }
  if (d.weak) { b.classList.toggle('on'); const m = d.weak; EV.weak = EV.weak.includes(m) ? EV.weak.filter(x => x !== m) : [...EV.weak, m]; return; }
  if (d.feel) { document.querySelectorAll('[data-feel]').forEach(x => x.classList.toggle('on', x === b)); EV.feel = d.feel; return; }
  if ('evsubmit' in d) { submitEval(); return; }
  if (d.fv) { foodView = d.fv; reroute(); return; }
  if (d.oo) { const [k, j] = d.oo.split(':'); openOpt[k] = +j; reroute(); return; }
  if (d.pick) { const [k, j] = d.pick.split(':'); const t = today(); S.meals[t] = S.meals[t] || {}; S.meals[t][k] = S.meals[t][k] === +j ? null : +j; save(); reroute(); return; }
  if (d.took) { const t = today(); S.supp[t] = S.supp[t] || {}; S.supp[t][d.took] = !S.supp[t][d.took]; save(); reroute(); return; }
  if ('hideinstall' in d) { S.hideInstall = 1; save(); route(); return; }
  if ('addw' in d) { const v = +$('#wIn').value; if (!(v > 25 && v < 200)) { toast('اكتب وزن صحيح'); return; } const t = today(), x = S.weights.find(z => z.d === t); if (x) x.w = v; else S.weights.push({ d: t, w: v }); save(); route(); toast('انحفظ وزنك'); return; }
  if ('saveme' in d) { S.name = $('#pN').value.trim(); S.age = $('#pA').value; S.h = +$('#pH').value || 168; save(); toast('انحفظ'); route(); return; }
  if ('copy' in d) { const t = $('#bk'); try { navigator.clipboard.writeText(t.value).then(() => toast('انسخ'), () => { t.select(); toast('محدد، انسخه'); }); } catch (er) { t.select(); } return; }
  if ('restore' in d) { try { const o = JSON.parse($('#rs').value); if (!o || !o.month) throw 0; S = Object.assign(def(), o); save(); route(); toast('رجعت معلوماتك'); } catch (er) { toast('الكود مو صحيح'); } return; }
});
function renderPlayerSets() { // تحديث السطور بدون ما نعيد الأنيميشن
  const sets = SES.sets[SES.k], cur = sets.findIndex(s => !s.ok);
  document.querySelectorAll('#player .set').forEach((row, j) => { row.classList.toggle('done', sets[j].ok); const i = row.querySelector('.i'); i.classList.toggle('cur', j === cur); i.textContent = j === cur ? '●' : AR(j + 1); });
  const done = SES.sets.map(s => s.every(z => z.ok)); document.querySelectorAll('#player .dots button').forEach((x, j) => x.classList.toggle('ok', done[j]));
}
document.addEventListener('input', e => { const t = e.target; if (!SES) return; if (t.dataset.w != null) SES.sets[SES.k][+t.dataset.w].w = t.value; if (t.dataset.r != null) SES.sets[SES.k][+t.dataset.r].r = t.value; });
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
