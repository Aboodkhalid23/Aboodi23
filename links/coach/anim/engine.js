// محرك الأنيميشن: مجسّم عضلي أبيض ثلاثي الأبعاد يسوي التمرين، كله مرسوم بالكود ومجاني
import * as THREE from 'three';
import { RoomEnvironment } from '../vendor/addons/RoomEnvironment.js';

const V = (x = 0, y = 0, z = 0) => new THREE.Vector3(x, y, z);
const D = Math.PI / 180;
const ease = t => -(Math.cos(Math.PI * t) - 1) / 2; // حركة ناعمة مثل حركة الإنسان
const lerp = (a, b, t) => a + (b - a) * t;
const lv = (a, b, t) => a.clone().lerp(b, t);

/* ================= المواد ================= */
function materials() {
  return {
    skin: new THREE.MeshStandardMaterial({ color: 0xeef0f3, roughness: .3, metalness: .05, envMapIntensity: 1.15 }),
    glow: new THREE.MeshStandardMaterial({ color: 0xff3b4d, emissive: 0xff1430, emissiveIntensity: .8, roughness: .3 }),
    glow2: new THREE.MeshStandardMaterial({ color: 0xffe3e6, emissive: 0xff5a6a, emissiveIntensity: .12, roughness: .3 }),
    metal: new THREE.MeshStandardMaterial({ color: 0xd0d5dc, metalness: .92, roughness: .22 }),
    black: new THREE.MeshStandardMaterial({ color: 0x16181d, metalness: .25, roughness: .5 }),
    pad: new THREE.MeshStandardMaterial({ color: 0x1b1e25, metalness: .05, roughness: .55 }),
    frame: new THREE.MeshStandardMaterial({ color: 0x2c313b, metalness: .75, roughness: .32 }),
    accent: new THREE.MeshStandardMaterial({ color: 0x3d7bff, emissive: 0x1a4dff, emissiveIntensity: .5, metalness: .3, roughness: .4 }),
    cable: new THREE.LineBasicMaterial({ color: 0xdfe6f0 }),
  };
}

/* ================= أشكال ================= */
const SPH = new THREE.SphereGeometry(1, 40, 28);
function mesh(geo, mat) { const m = new THREE.Mesh(geo, mat); m.castShadow = true; m.receiveShadow = true; return m; }
function ell(mat, sx, sy, sz, x = 0, y = 0, z = 0, rx = 0, ry = 0, rz = 0) { const m = mesh(SPH, mat); m.scale.set(sx, sy, sz); m.position.set(x, y, z); m.rotation.set(rx, ry, rz); return m; }
function lathe(mat, pts, sz = 1, seg = 40) { const g = new THREE.LatheGeometry(pts.map(([r, y]) => new THREE.Vector2(r, y)), seg); g.computeVertexNormals(); const m = mesh(g, mat); m.scale.z = sz; return m; }
function box(mat, w, h, d, x = 0, y = 0, z = 0) { const m = mesh(new THREE.BoxGeometry(w, h, d), mat); m.position.set(x, y, z); return m; }
function rbox(mat, w, h, d, r, x = 0, y = 0, z = 0) { // صندوق بحواف مدورة
  const s = new THREE.Shape(); const hw = w / 2 - r, hh = h / 2 - r;
  s.moveTo(-hw, -h / 2); s.lineTo(hw, -h / 2); s.quadraticCurveTo(w / 2, -h / 2, w / 2, -hh); s.lineTo(w / 2, hh); s.quadraticCurveTo(w / 2, h / 2, hw, h / 2); s.lineTo(-hw, h / 2); s.quadraticCurveTo(-w / 2, h / 2, -w / 2, hh); s.lineTo(-w / 2, -hh); s.quadraticCurveTo(-w / 2, -h / 2, -hw, -h / 2);
  const g = new THREE.ExtrudeGeometry(s, { depth: d - 2 * r, bevelEnabled: true, bevelSize: r, bevelThickness: r, bevelSegments: 4, curveSegments: 6 }); g.translate(0, 0, -(d - 2 * r) / 2);
  const m = mesh(g, mat); m.position.set(x, y, z); return m;
}
function rod(mat, a, b, r = .022) { const m = mesh(new THREE.CylinderGeometry(r, r, 1, 14), mat); setRod(m, a, b); return m; }
function setRod(m, a, b) { m.position.copy(a).add(b).multiplyScalar(.5); m.scale.set(1, Math.max(1e-4, a.distanceTo(b)), 1); m.quaternion.setFromUnitVectors(V(0, 1, 0), b.clone().sub(a).normalize()); }

/* ================= المجسّم ================= */
function buildBody(M) {
  const mus = {};
  const reg = (n, m) => { (mus[n] = mus[n] || []).push(m); return m; };
  // الجذع السفلي (الحوض والبطن) — الأصل بمستوى مفصل الورك
  const lower = new THREE.Group(); lower.rotation.order = 'YXZ';
  lower.add(lathe(M.skin, [[0, -.12], [.09, -.105], [.132, -.06], [.142, .01], [.13, .09], [.12, .16], [.122, .21], [0, .215]], .7));
  for (const s of [-1, 1]) {
    lower.add(reg('glutes', ell(M.skin, .074, .078, .064, s * .064, -.03, -.06)));
    lower.add(reg('obliques', ell(M.skin, .03, .07, .05, s * .105, .08, .012, 0, 0, s * -.15)));
  }
  for (let r = 0; r < 3; r++) for (const s of [-1, 1]) lower.add(reg('abs', ell(M.skin, .029, .024, .011, s * .031, .03 + r * .055, .082)));
  lower.add(reg('abs', ell(M.skin, .07, .12, .025, 0, .07, .07)));
  lower.add(reg('lowerback', ell(M.skin, .07, .075, .03, 0, .08, -.075)));
  // الجذع العلوي (القفص والكتف والراس)
  const upper = new THREE.Group(); upper.position.y = .2; lower.add(upper);
  upper.add(lathe(M.skin, [[0, -.02], [.122, -.01], [.135, .06], [.155, .14], [.17, .21], [.183, .26], [.168, .305], [.12, .335], [.06, .35], [0, .355]], .66));
  for (const s of [-1, 1]) {
    upper.add(reg('chest', ell(M.skin, .084, .058, .034, s * .07, .19, .094, .2, s * -.28, s * .25)));
    upper.add(reg('back', ell(M.skin, .05, .13, .055, s * .128, .12, -.035, 0, 0, s * .18)));
  }
  upper.add(reg('back', ell(M.skin, .13, .1, .038, 0, .2, -.087)));
  upper.add(reg('traps', ell(M.skin, .11, .045, .06, 0, .31, -.035)));
  upper.add(lathe(M.skin, [[0, .32], [.045, .33], [.046, .4], [.05, .43], [0, .435]]));
  upper.add(ell(M.skin, .079, .104, .09, 0, .49, .012));
  upper.add(ell(M.skin, .056, .04, .062, 0, .43, .032));
  upper.add(ell(M.skin, .012, .02, .012, 0, .48, .1));
  // الأطراف (كل طرف محوره -Y، و+Z صوب اتجاه الثني)
  const arm = () => {
    const up = new THREE.Group(), lo = new THREE.Group();
    up.add(lathe(M.skin, [[0, -.3], [.03, -.295], [.034, -.27], [.04, -.22], [.045, -.16], [.047, -.1], [.05, -.05], [.048, -.01], [.03, .02], [0, .03]]));
    up.add(reg('shoulders', ell(M.skin, .062, .07, .062, 0, -.028, 0)));
    up.add(reg('biceps', ell(M.skin, .036, .082, .035, 0, -.15, -.024)));
    up.add(reg('triceps', ell(M.skin, .038, .09, .036, 0, -.135, .024)));
    up.add(ell(M.skin, .031, .031, .031, 0, -.29, 0));
    lo.add(lathe(M.skin, [[0, -.275], [.022, -.27], [.024, -.24], [.028, -.18], [.036, -.11], [.041, -.06], [.038, -.02], [.03, 0], [0, .01]]));
    lo.add(reg('forearms', ell(M.skin, .034, .07, .031, 0, -.07, -.008)));
    lo.add(ell(M.skin, .031, .05, .018, 0, -.315, 0));
    lo.add(ell(M.skin, .011, .028, .011, .028, -.29, -.012, 0, 0, .5));
    return { up, lo };
  };
  const leg = (side) => {
    const up = new THREE.Group(), lo = new THREE.Group();
    up.add(lathe(M.skin, [[0, -.44], [.04, -.43], [.046, -.39], [.055, -.32], [.064, -.24], [.071, -.15], [.074, -.07], [.07, -.01], [.05, .03], [0, .04]]));
    const q = reg('quads', ell(M.skin, .05, .17, .04, 0, -.18, .035)); up.add(q);
    up.add(reg('quads', ell(M.skin, .036, .06, .032, side * -.025, -.35, .03)));
    up.add(reg('hamstrings', ell(M.skin, .05, .16, .04, 0, -.2, -.035)));
    if (side === -1) up.add(reg('hipflex', ell(M.skin, .046, .09, .036, 0, -.07, .045)));
    up.add(ell(M.skin, .044, .044, .044, 0, -.43, .01));
    lo.add(lathe(M.skin, [[0, -.43], [.026, -.42], [.028, -.38], [.03, -.3], [.04, -.2], [.048, -.12], [.046, -.06], [.04, -.01], [0, .01]]));
    lo.add(reg('calves', ell(M.skin, .042, .09, .038, 0, -.12, -.03)));
    return { up, lo };
  };
  const foot = () => { const g = new THREE.Group(); g.add(ell(M.skin, .042, .03, .105, 0, 0, .03)); g.add(ell(M.skin, .036, .034, .04, 0, .005, -.05)); return g; };
  return { lower, upper, mus, armL: arm(), armR: arm(), legL: leg(1), legR: leg(-1), footL: foot(), footR: foot() };
}

/* ================= الحل العكسي للأطراف ================= */
const _x = V(), _y = V(), _z = V(), _m = new THREE.Matrix4();
function orient(g, from, to, pole) {
  _y.subVectors(from, to).normalize();
  _z.copy(pole).addScaledVector(_y, -pole.dot(_y));
  if (_z.lengthSq() < 1e-6) _z.set(0, 0, 1).addScaledVector(_y, -_y.z);
  _z.normalize(); _x.crossVectors(_y, _z).normalize();
  _m.makeBasis(_x, _y, _z); g.position.copy(from); g.quaternion.setFromRotationMatrix(_m);
}
function ik(root, target, a, b, pole) {
  const d0 = target.clone().sub(root); const d = Math.min(a + b - 1e-4, Math.max(Math.abs(a - b) + 1e-3, d0.length()));
  const u = d0.normalize(); const p = pole.clone().addScaledVector(u, -pole.dot(u)); if (p.lengthSq() < 1e-6) p.set(0, 0, 1); p.normalize();
  const c = (a * a + d * d - b * b) / (2 * a * d), s = Math.sqrt(Math.max(0, 1 - c * c));
  const mid = root.clone().addScaledVector(u, a * c).addScaledVector(p, a * s);
  return { mid, end: mid.clone().addScaledVector(target.clone().sub(mid).normalize(), b) };
}

/* ================= المعدّات ================= */
function dumbbell(M, size = 1) {
  const g = new THREE.Group();
  const h = mesh(new THREE.CylinderGeometry(.015, .015, .19, 16), M.metal); h.rotation.z = Math.PI / 2; g.add(h);
  for (const s of [-1, 1]) {
    const p = mesh(new THREE.CylinderGeometry(.062 * size, .062 * size, .055, 6), M.black); p.rotation.z = Math.PI / 2; p.position.x = s * .1; g.add(p);
    const c = mesh(new THREE.CylinderGeometry(.018, .018, .058, 16), M.metal); c.rotation.z = Math.PI / 2; c.position.x = s * .1; g.add(c);
  }
  return g;
}
function plates(M, x, y, z, n = 3) { const g = new THREE.Group(); for (let i = 0; i < n; i++) { const p = mesh(new THREE.CylinderGeometry(.16 - i * .02, .16 - i * .02, .035, 32), M.black); p.rotation.z = Math.PI / 2; p.position.set(x + i * .04, y, z); g.add(p); } return g; }
function stack(M, x, y, z, h = .9) { const g = new THREE.Group(); g.add(box(M.frame, .32, h + .1, .04, x, y + h / 2, z - .1)); for (let i = 0; i < 12; i++) g.add(box(M.black, .26, .055, .1, x, y + .04 + i * .065, z)); g.add(rod(M.metal, V(x, y, z + .07), V(x, y + h, z + .07), .01)); return g; }
function cableLine(M) { const g = new THREE.BufferGeometry().setFromPoints([V(), V(), V()]); const l = new THREE.Line(g, M.cable); l.frustumCulled = false; l.set = (...pts) => { const a = l.geometry.attributes.position; pts.forEach((p, i) => a.setXYZ(i, p.x, p.y, p.z)); for (let i = pts.length; i < a.count; i++) a.setXYZ(i, pts[pts.length - 1].x, pts[pts.length - 1].y, pts[pts.length - 1].z); a.needsUpdate = true; }; return l; }
function pulley(M, p) { const m = mesh(new THREE.TorusGeometry(.045, .015, 10, 24), M.metal); m.position.copy(p); return m; }

const EQ = {
  flatBench(M, h = .44) { const g = new THREE.Group(); g.add(rbox(M.pad, .3, .07, 1.2, .025, 0, h, 0)); g.add(rod(M.frame, V(0, .02, -.5), V(0, h - .04, -.4), .028)); g.add(rod(M.frame, V(0, .02, .5), V(0, h - .04, .4), .028)); g.add(rod(M.frame, V(-.22, .02, -.5), V(.22, .02, -.5), .028)); g.add(rod(M.frame, V(-.22, .02, .5), V(.22, .02, .5), .028)); return { g }; },
  adjBench(M, ang) { // ang: زاوية المسند عن الأرض (90 = عمودي)
    const g = new THREE.Group(); const a = ang * D;
    g.add(rbox(M.pad, .31, .07, .36, .025, 0, .45, .1));
    const back = rbox(M.pad, .3, .07, .8, .025); back.rotation.x = a; back.position.set(0, .45 + Math.sin(a) * .4, -.08 - Math.cos(a) * .4); g.add(back);
    g.add(rod(M.frame, V(0, .03, .45), V(0, .03, -.8), .03)); g.add(rod(M.frame, V(0, .03, .25), V(0, .41, .1))); g.add(rod(M.frame, V(0, .03, -.55), V(0, .4 + Math.sin(a) * .28, -.08 - Math.cos(a) * .28)));
    g.add(rod(M.frame, V(-.22, .03, .45), V(.22, .03, .45), .03)); g.add(rod(M.frame, V(-.24, .03, -.8), V(.24, .03, -.8), .03));
    return { g };
  },
  seatMachine(M, back = -8) { // كرسي جهاز ومسند ظهر
    const g = new THREE.Group(); g.add(rbox(M.pad, .38, .08, .4, .03, 0, .46, .06));
    const b = rbox(M.pad, .36, .7, .08, .03); b.rotation.x = back * D; b.position.set(0, .86, -.2); g.add(b);
    g.add(rod(M.frame, V(0, .02, .05), V(0, .42, .05), .035)); g.add(rod(M.frame, V(0, .02, -.3), V(0, 1.2, -.3), .035)); g.add(box(M.frame, .7, .04, 1.2, 0, .02, .1));
    return { g };
  },
  mat(M) { return { g: box(new THREE.MeshStandardMaterial({ color: 0x0f1013, roughness: .9 }), 1.4, .014, 2.4, 0, .007, 0) }; },
};

/* ================= التمارين ================= */
// أدوات للوضعيات
const fromTorso = (P, v) => v.clone().applyEuler(new THREE.Euler(P.pitch || 0, P.yaw || 0, P.roll || 0, 'YXZ')).add(P.hip);
const arc = (center, r, a0, a1, t, plane = 'yz', side = 1) => { const a = lerp(a0, a1, t) * D; return plane === 'yz' ? center.clone().add(V(0, -Math.cos(a) * r, Math.sin(a) * r)) : center.clone().add(V(side * Math.sin(a) * r, -Math.cos(a) * r, 0)); };
const SH = (P, s) => fromTorso(P, V(s * .185, .45, -.01).applyAxisAngle(V(1, 0, 0), 0)); // تقريبي، يتصحح بالمحرك
const STAND = { hip: V(0, .93, 0), pitch: 0, feet: [V(.11, .08, .02), V(-.11, .08, .02)], kneePole: () => V(0, 0, 1), footDir: [V(.08, -.1, 1), V(-.08, -.1, 1)] };
const SEAT = (z = .42) => ({ feet: [V(.17, .08, z), V(-.17, .08, z)], kneePole: s => V(s * .15, .4, 1), footDir: [V(.1, -.15, 1), V(-.1, -.15, 1)] });

export const EXERCISES = {
  /* ---------- اليوم ١: صدر + أمامية ---------- */
  chestpress: {
    title: 'جهاز ضغط الصدر', prim: ['chest'], sec: ['shoulders', 'triceps'], tempo: [1, .35, 2, .5], phases: ['ادفع لگدام', 'رجّع ببطء'],
    pose(t) { const P = { hip: V(0, .55, 0), pitch: -9 * D, spine: -4 * D, ...SEAT(.45) };
      P.hands = [lv(V(.25, .97, .1), V(.17, .99, .6), t), lv(V(-.25, .97, .1), V(-.17, .99, .6), t)]; P.armPole = s => V(s * .9, -.7, -.5); P.hold = ['grip', 'grip']; return P; },
    equip(M) { const s = EQ.seatMachine(M, -9); const g = s.g; g.add(box(M.frame, .08, 1.6, .08, .45, .8, -.35), box(M.frame, .08, 1.6, .08, -.45, .8, -.35), box(M.frame, .98, .08, .08, 0, 1.6, -.35));
      const arms = [rod(M.metal, V(), V(), .025), rod(M.metal, V(), V(), .025)]; g.add(...arms); g.add(stack(M, .0, .02, -.6, 1.1));
      return { g, update(S) { [1, -1].forEach((s, i) => setRod(arms[i], V(s * .42, .62, -.22), S.hands[i].clone().add(V(0, -.09, 0)))); } }; },
    cam: { target: V(0, .85, .15), r: 3.2, h: 1.45, yaw: [35, 80] }, path: 1,
  },
  incline: {
    title: 'ضغط الصدر المائل بالدمبل', prim: ['chest'], sec: ['shoulders', 'triceps'], tempo: [1, .35, 2, .55], phases: ['ادفع لفوگ', 'نزّل ببطء'],
    pose(t) { const P = { hip: V(0, .56, .04), pitch: -52 * D, spine: -3 * D, feet: [V(.21, .08, .66), V(-.21, .08, .66)], kneePole: s => V(s * .2, .6, 1), footDir: [V(.1, -.25, 1), V(-.1, -.25, 1)] };
      P.hands = [lv(V(.34, .98, -.26), V(.16, 1.36, -.36), t), lv(V(-.34, .98, -.26), V(-.16, 1.36, -.36), t)]; P.armPole = s => V(s, -.55, -.35); P.hold = ['db', 'db']; return P; },
    equip(M) { return EQ.adjBench(M, 38); }, cam: { target: V(0, .82, -.15), r: 3.1, h: 1.85, yaw: [25, 70] }, path: 1,
  },
  dbbench: {
    title: 'ضغط الصدر المستوي بالدمبل', prim: ['chest'], sec: ['shoulders', 'triceps'], tempo: [1, .35, 2, .55], phases: ['ادفع لفوگ', 'نزّل ببطء'],
    pose(t) { const P = { hip: V(0, .57, .25), pitch: -90 * D, feet: [V(.28, .08, .62), V(-.28, .08, .62)], kneePole: s => V(s * .3, .6, .6), footDir: [V(.1, -.2, 1), V(-.1, -.2, 1)] };
      P.hands = [lv(V(.34, .72, -.18), V(.15, 1.17, -.2), t), lv(V(-.34, .72, -.18), V(-.15, 1.17, -.2), t)]; P.armPole = s => V(s, -.7, .15); P.hold = ['db', 'db']; return P; },
    equip(M) { const b = EQ.flatBench(M, .45); b.g.position.z = -.05; return b; }, cam: { target: V(0, .7, -.05), r: 3.1, h: 1.7, yaw: [30, 75] }, path: 1,
  },
  pecdeck: {
    title: 'جهاز تجميع الصدر', prim: ['chest'], sec: ['shoulders'], tempo: [1, .5, 2, .5], phases: ['جمّع واعصر', 'رجّع ببطء'],
    pose(t) { const P = { hip: V(0, .55, 0), pitch: -4 * D, ...SEAT(.42) };
      const f = lerp(98, 14, t) * D; P.hands = [1, -1].map(s => V(s * .185, 1.0, -.03).add(V(s * Math.sin(f) * .5, -.02, Math.cos(f) * .5))); P.armPole = s => V(0, -1, -.4); P.hold = ['grip', 'grip']; return P; },
    equip(M) { const s = EQ.seatMachine(M, -4); const g = s.g; g.add(box(M.frame, .1, 1.9, .1, 0, .95, -.4), box(M.frame, .7, .08, .1, 0, 1.86, -.4)); g.add(stack(M, 0, .02, -.65, 1.1));
      const arms = [rod(M.metal, V(), V(), .025), rod(M.metal, V(), V(), .025)], pads = [rbox(M.pad, .07, .26, .07, .02), rbox(M.pad, .07, .26, .07, .02)]; g.add(...arms, ...pads);
      return { g, update(S) { [1, -1].forEach((s, i) => { setRod(arms[i], V(s * .2, 1.6, -.4), S.hands[i].clone().add(V(0, .16, 0))); pads[i].position.copy(S.hands[i]).add(V(0, .03, 0)); }); } }; },
    cam: { target: V(0, .95, .1), r: 3.2, h: 1.9, yaw: [-25, 25] }, path: 1,
  },
  curl: {
    title: 'البايسبس بالدمبل', prim: ['biceps'], sec: ['forearms'], tempo: [1, .4, 2, .5], phases: ['ارفع واعصر', 'نزّل ببطء'],
    pose(t) { const P = { ...STAND }; P.hands = [1, -1].map(s => arc(V(s * .2, 1.11, .03), .3, 6, 138, t)); P.armPole = () => V(0, -.2, -1); P.hold = ['db', 'db']; return P; },
    equip(M) { return EQ.mat(M); }, cam: { target: V(0, 1.05, 0), r: 3.1, h: 1.35, yaw: [55, 100] }, path: 1,
  },
  hammer: {
    title: 'الهامر كيرل', prim: ['biceps', 'forearms'], sec: [], tempo: [1, .4, 2, .5], phases: ['ارفع', 'نزّل ببطء'],
    pose(t) { const P = { ...STAND }; P.hands = [1, -1].map(s => arc(V(s * .21, 1.11, .03), .3, 6, 130, t)); P.armPole = () => V(0, -.2, -1); P.hold = ['dbn', 'dbn']; return P; },
    equip(M) { return EQ.mat(M); }, cam: { target: V(0, 1.05, 0), r: 3.1, h: 1.35, yaw: [40, 90] }, path: 1,
  },
  plank: {
    title: 'البلانك', prim: ['abs'], sec: ['shoulders', 'glutes'], tempo: [1.2, 3, 1.2, .6], hold: true, phases: ['ادخل بالوضعية', 'انزل', 'اثبت وتنفّس'],
    pose(t) { const P = { hip: V(0, lerp(.27, .31, t), -.42), pitch: lerp(80, 84, t) * D, feet: [V(.1, .09, -1.26), V(-.1, .09, -1.26)], kneePole: () => V(0, -1, 0), footDir: [V(0, -1, .15), V(0, -1, .15)] };
      P.hands = [V(.11, .04, .27), V(-.11, .04, .27)]; P.elbows = [V(.17, .045, .02), V(-.17, .045, .02)]; P.armPole = () => V(0, -1, 0); return P; },
    equip(M) { return EQ.mat(M); }, cam: { target: V(0, .3, -.5), r: 3.1, h: 1.25, yaw: [75, 100] },
  },
  /* ---------- اليوم ٢: ظهر + خلفية ---------- */
  latpull: {
    title: 'السحب الأمامي', prim: ['back'], sec: ['biceps', 'shoulders'], tempo: [1, .4, 2, .5], phases: ['اسحب لتحت', 'رجّع ببطء'],
    pose(t) { const P = { hip: V(0, .55, 0), pitch: -12 * D, spine: lerp(0, -6, t) * D, ...SEAT(.46) };
      P.hands = [lv(V(.42, 1.66, .06), V(.33, 1.07, .16), t), lv(V(-.42, 1.66, .06), V(-.33, 1.07, .16), t)]; P.armPole = s => V(s, -.4, -.6); P.hold = ['bar', 'bar']; return P; },
    equip(M) { const g = new THREE.Group(); g.add(rbox(M.pad, .38, .08, .4, .03, 0, .46, .06)); g.add(rod(M.frame, V(0, .02, .05), V(0, .42, .05), .035));
      g.add(rbox(M.pad, .5, .09, .1, .03, 0, .71, .28)); g.add(rod(M.frame, V(0, .72, .28), V(0, .72, .55), .025));
      g.add(box(M.frame, .1, 2.35, .1, 0, 1.17, .6), box(M.frame, .08, .08, .7, 0, 2.3, .28)); g.add(box(M.frame, .8, .04, 1.4, 0, .02, .3)); g.add(stack(M, 0, .02, .8, 1.2));
      const p = pulley(M, V(0, 2.22, .12)); g.add(p); const c = cableLine(M); g.add(c); const bar = new THREE.Group(); bar.add(rod(M.metal, V(-.36, 0, 0), V(.36, 0, 0), .014)); bar.add(rod(M.metal, V(.36, 0, 0), V(.5, -.06, 0), .014)); bar.add(rod(M.metal, V(-.36, 0, 0), V(-.5, -.06, 0), .014)); g.add(bar);
      return { g, update(S) { const m = S.hands[0].clone().add(S.hands[1]).multiplyScalar(.5); bar.position.copy(m); c.set(V(0, 2.25, .12), m.clone().add(V(0, .02, 0))); } }; },
    cam: { target: V(0, 1.1, 0), r: 3.4, h: 1.65, yaw: [150, 210] }, path: 1, ringBack: true,
  },
  row: {
    title: 'السحب الأرضي بالكيبل', prim: ['back'], sec: ['biceps', 'shoulders'], tempo: [1, .45, 2, .5], phases: ['اسحب لبطنك', 'رجّع ببطء'],
    pose(t) { const P = { hip: V(0, .43, 0), pitch: lerp(14, -6, t) * D, feet: [V(.12, .4, .7), V(-.12, .4, .7)], kneePole: s => V(s * .2, 1, .2), footDir: [V(0, 1, .25), V(0, 1, .25)] };
      P.hands = [lv(V(.07, .66, .66), V(.09, .62, .2), t), lv(V(-.07, .66, .66), V(-.09, .62, .2), t)]; P.armPole = s => V(s * .35, -.2, -1); P.hold = ['bar', 'bar']; P.barW = .14; return P; },
    equip(M) { const g = new THREE.Group(); g.add(rbox(M.pad, .32, .07, 1.0, .025, 0, .35, -.1)); g.add(rod(M.frame, V(0, .02, -.3), V(0, .32, -.3), .03)); g.add(box(M.frame, .7, .04, 1.9, 0, .02, .25));
      g.add(rbox(M.frame, .5, .4, .05, .02, 0, .42, .8)); g.add(stack(M, 0, .02, 1.15, 1.1)); g.add(box(M.frame, .1, 1.5, .1, 0, .75, .98));
      const c = cableLine(M); g.add(c, pulley(M, V(0, .62, .86))); const h = new THREE.Group(); h.add(rod(M.metal, V(-.08, 0, 0), V(.08, 0, 0), .014), rod(M.metal, V(-.08, 0, 0), V(0, 0, .09), .012), rod(M.metal, V(.08, 0, 0), V(0, 0, .09), .012)); g.add(h);
      return { g, update(S) { const m = S.hands[0].clone().add(S.hands[1]).multiplyScalar(.5); h.position.copy(m); c.set(m.clone().add(V(0, 0, .09)), V(0, .62, .86), V(0, 1.4, .98)); } }; },
    cam: { target: V(0, .6, .2), r: 3.3, h: 1.4, yaw: [70, 110] }, path: 1,
  },
  dbrow: {
    title: 'السحب بالدمبل بإيد وحدة', prim: ['back'], sec: ['biceps', 'shoulders'], tempo: [1, .45, 2, .5], phases: ['اسحب لجنبك', 'نزّل ببطء'],
    pose(t) { const P = { hip: V(.03, .9, -.22), pitch: 78 * D, yaw: 0, feet: [V(.12, .5, -.62), V(-.3, .08, -.15)], knees: [V(.12, .5, -.22), null], kneePole: s => V(0, .1, 1), footDir: [V(0, -.3, -1), V(-.1, -.1, 1)] };
      P.hands = [V(.16, .52, .32), lv(V(-.2, .44, .24), V(-.24, .86, -.04), t)]; P.armPole = s => s > 0 ? V(.3, -1, 0) : V(-.2, 1, -.7); P.hold = [null, 'dbn']; return P; },
    equip(M) { const b = EQ.flatBench(M, .44); b.g.position.set(.13, 0, -.1); return b; }, cam: { target: V(-.05, .75, -.05), r: 3.2, h: 1.6, yaw: [-60, -110] }, path: 1, pathHand: 1,
  },
  backext: {
    title: 'تمدد الظهر', prim: ['lowerback'], sec: ['glutes', 'hamstrings'], tempo: [1.2, .5, 2, .5], phases: ['اصعد لحد الخط العدل', 'انزل ببطء'],
    pose(t) { const P = { hip: V(0, .86, .05), pitch: lerp(130, 48, t) * D, feet: [V(.1, .26, -.56), V(-.1, .26, -.56)], kneePole: () => V(0, -1, .2), footDir: [V(0, -.6, .8), V(0, -.6, .8)] };
      P.hands = [1, -1].map(s => fromTorso(P, V(s * .04, .42, .16))); P.armPole = s => fromTorso(P, V(s, 0, 0)).sub(P.hip); return P; },
    equip(M) { const g = new THREE.Group(); const pad = rbox(M.pad, .45, .08, .32, .03); pad.rotation.x = -45 * D; pad.position.set(0, .73, .02); g.add(pad);
      const fp = rbox(M.frame, .35, .03, .2, .01); fp.rotation.x = -45 * D; fp.position.set(0, .2, -.6); g.add(fp); g.add(rod(M.pad, V(-.18, .36, -.5), V(.18, .36, -.5), .045));
      g.add(rod(M.frame, V(0, .03, -.7), V(0, .7, .0), .035), rod(M.frame, V(0, .03, .25), V(0, .66, .05), .035), box(M.frame, .6, .04, 1.2, 0, .02, -.2)); return { g }; },
    cam: { target: V(0, .75, .1), r: 3.2, h: 1.3, yaw: [75, 105] }, ringBack: true,
  },
  pushdown: {
    title: 'الخلفية بالكيبل', prim: ['triceps'], sec: [], tempo: [1, .45, 2, .5], phases: ['ادفع لتحت', 'رجّع ببطء'],
    pose(t) { const P = { ...STAND, pitch: 12 * D }; const el = s => fromTorso(P, V(s * .2, .19, .05)); P.hands = [1, -1].map(s => arc(el(s).add(V(-s * .06, 0, 0)), .3, 110, 4, t)); P.elbows = [el(1), el(-1)]; P.armPole = () => V(0, 0, -1); P.hold = ['bar', 'bar']; P.barW = .18; return P; },
    equip(M) { const g = new THREE.Group(); g.add(box(M.frame, .45, 2.3, .12, 0, 1.15, .62)); g.add(stack(M, 0, .02, .82, 1.2)); const c = cableLine(M); g.add(c, pulley(M, V(0, 2.12, .5)));
      const bar = rod(M.metal, V(-.12, 0, 0), V(.12, 0, 0), .015); g.add(bar);
      return { g, update(S) { const m = S.hands[0].clone().add(S.hands[1]).multiplyScalar(.5); bar.position.copy(m); c.set(m, V(0, 2.12, .5)); } }; },
    cam: { target: V(0, 1.15, .1), r: 3.2, h: 1.5, yaw: [50, 95] }, path: 1, ringBack: true,
  },
  ohtri: {
    title: 'الخلفية فوگ الراس', prim: ['triceps'], sec: [], tempo: [1, .4, 2, .5], phases: ['ادفع لفوگ', 'نزّل ورا راسك'],
    pose(t) { const P = { ...STAND }; const el = s => V(s * .1, 1.66, -.02); const a = lerp(150, 6, t) * D;
      P.hands = [1, -1].map(s => el(s).add(V(-s * .07, Math.cos(a) * .3, -Math.sin(a) * .3))); P.elbows = [el(1), el(-1)]; P.armPole = () => V(0, 0, 1); P.hold = ['single', null]; return P; },
    equip(M) { return EQ.mat(M); }, cam: { target: V(0, 1.4, 0), r: 3.2, h: 1.6, yaw: [110, 150] }, path: 1, ringBack: true,
  },
  /* ---------- اليوم ٣: أكتاف + رجل ---------- */
  legpress: {
    title: 'دفع الرجل بالجهاز', prim: ['quads', 'glutes'], sec: ['hamstrings'], tempo: [1, .3, 2, .5], phases: ['ادفع بكعبك', 'رجّع ببطء'],
    pose(t) { const P = { hip: V(0, .46, 0), pitch: -58 * D, hands: [V(.3, .5, .12), V(-.3, .5, .12)], armPole: s => V(s, 0, -1), hold: ['grip', 'grip'] };
      P.feet = [lv(V(.16, .8, .4), V(.16, 1.03, .63), t), lv(V(-.16, .8, .4), V(-.16, 1.03, .63), t)]; P.kneePole = s => V(s * .35, 1, -.3); P.footDir = [V(0, .7, -.7), V(0, .7, -.7)]; return P; },
    equip(M) { const g = new THREE.Group(); const seat = rbox(M.pad, .42, .08, .42, .03, 0, .37, .05); g.add(seat); const b = rbox(M.pad, .42, .08, .75, .03); b.rotation.x = 58 * D; b.position.set(0, .7, -.32); g.add(b);
      const dir = V(0, .707, .707); for (const x of [-.32, .32]) g.add(rod(M.frame, V(x, .35, .15), V(x, 1.7, 1.5), .035)); g.add(box(M.frame, .9, .04, 2.2, 0, .02, .5)); g.add(rod(M.frame, V(0, .03, .05), V(0, .33, .05), .04));
      const sled = new THREE.Group(); sled.add(rbox(M.frame, .62, .62, .05, .02)); sled.add(plates(M, .32, 0, -.15, 3)); sled.add(plates(M, -.4, 0, -.15, 3)); g.add(sled);
      return { g, update(S) { const m = S.ankles[0].clone().add(S.ankles[1]).multiplyScalar(.5).addScaledVector(dir, .07).add(V(0, .03, 0)); sled.position.copy(m); sled.quaternion.setFromUnitVectors(V(0, 0, 1), dir.clone().negate()); } }; },
    cam: { target: V(0, .75, .3), r: 3.8, h: 1.9, yaw: [55, 95] }, path: 0, pathFoot: true,
  },
  legext: {
    title: 'الفخذ الأمامي بالجهاز', prim: ['quads'], sec: [], tempo: [1, .6, 2, .5], phases: ['ارفع واعصر', 'نزّل ببطء'],
    pose(t) { const P = { hip: V(0, .62, 0), pitch: -10 * D, hands: [V(.28, .6, .05), V(-.28, .6, .05)], armPole: s => V(s, 0, -1), hold: ['grip', 'grip'] }; const a = lerp(-8, 84, t) * D;
      P.knees = [V(.11, .6, .43), V(-.11, .6, .43)]; P.feet = P.knees.map(k => k.clone().add(V(0, -Math.cos(a) * .42, Math.sin(a) * .42))); P.kneePole = () => V(0, 0, 1); P.footDir = [1, 2].map(() => V(0, Math.sin(a), Math.cos(a))); return P; },
    equip(M) { const s = EQ.seatMachine(M, -10); const g = s.g; s.g.children[0].position.set(0, .53, .2); s.g.children[0].scale.set(1, 1, 1.4);
      const arm = rod(M.metal, V(), V(), .025), pad = rod(M.pad, V(-.17, 0, 0), V(.17, 0, 0), .045); g.add(arm, pad, box(M.frame, .08, .08, .08, .28, .6, .43));
      return { g, update(S) { const m = S.ankles[0].clone().add(S.ankles[1]).multiplyScalar(.5); const n = S.footDir[0].clone().multiplyScalar(-.06); pad.position.copy(m).add(S.footDir[0].clone().multiplyScalar(.05)).add(V(0, 0, 0)); setRod(arm, V(.28, .6, .43), pad.position.clone().add(V(.28, 0, 0))); } }; },
    cam: { target: V(0, .65, .3), r: 3.1, h: 1.25, yaw: [70, 105] }, path: 0, pathFoot: true,
  },
  legcurl: {
    title: 'الفخذ الخلفي بالجهاز', prim: ['hamstrings'], sec: ['calves'], tempo: [1, .5, 2, .5], phases: ['اسحب كعبك', 'نزّل ببطء'],
    pose(t) { const P = { hip: V(0, .63, 0), pitch: 90 * D, hands: [V(.22, .52, .58), V(-.22, .52, .58)], armPole: s => V(s * .3, -1, 0), hold: ['grip', 'grip'] }; const a = lerp(4, 105, t) * D;
      P.knees = [V(.1, .6, -.43), V(-.1, .6, -.43)]; P.feet = P.knees.map(k => k.clone().add(V(0, Math.sin(a) * .42, -Math.cos(a) * .42))); P.kneePole = () => V(0, -1, 0); P.footDir = [1, 2].map(() => V(0, -Math.cos(a), -Math.sin(a))); P.pad = a; return P; },
    equip(M) { const g = new THREE.Group(); g.add(rbox(M.pad, .34, .08, 1.15, .03, 0, .53, .1)); g.add(rod(M.frame, V(0, .02, .5), V(0, .5, .5), .035), rod(M.frame, V(0, .02, -.3), V(0, .5, -.3), .035), box(M.frame, .7, .04, 1.9, 0, .02, -.1));
      const pad = rod(M.pad, V(-.17, 0, 0), V(.17, 0, 0), .045), arm = rod(M.metal, V(), V(), .025); g.add(pad, arm); g.add(rod(M.frame, V(-.25, .55, .6), V(.25, .55, .6), .02));
      return { g, update(S, P) { const m = S.ankles[0].clone().add(S.ankles[1]).multiplyScalar(.5); pad.position.copy(m).add(V(0, Math.cos(P.pad) * .06, Math.sin(P.pad) * .06)); setRod(arm, V(.26, .6, -.43), pad.position.clone().add(V(.26, 0, 0))); } }; },
    cam: { target: V(0, .65, -.2), r: 3.3, h: 1.5, yaw: [70, 110] }, path: 0, pathFoot: true, ringBack: true,
  },
  shpress: {
    title: 'ضغط الكتف بالدمبل', prim: ['shoulders'], sec: ['triceps', 'traps'], tempo: [1, .35, 2, .5], phases: ['ادفع لفوگ', 'نزّل ببطء'],
    pose(t) { const P = { hip: V(0, .55, 0), pitch: -6 * D, ...SEAT(.44) }; P.hands = [lv(V(.31, 1.13, .05), V(.16, 1.58, .02), t), lv(V(-.31, 1.13, .05), V(-.16, 1.58, .02), t)]; P.armPole = s => V(s, -1, -.15); P.hold = ['db', 'db']; return P; },
    equip(M) { return EQ.adjBench(M, 84); }, cam: { target: V(0, 1.05, 0), r: 3.2, h: 1.45, yaw: [-30, 30] }, path: 1,
  },
  lateral: {
    title: 'الرفرفة الجانبية', prim: ['shoulders'], sec: ['traps'], tempo: [1, .4, 2.4, .5], phases: ['ارفع لجنب', 'نزّل ببطء'],
    pose(t) { const P = { ...STAND, pitch: 4 * D }; const f = lerp(10, 86, t) * D;
      P.hands = [1, -1].map(s => V(s * .19, 1.37, .02).add(V(s * Math.sin(f) * .53, -Math.cos(f) * .53, .06))); P.armPole = () => V(0, .35, -1); P.hold = ['dbz', 'dbz']; return P; },
    equip(M) { return EQ.mat(M); }, cam: { target: V(0, 1.15, 0), r: 3.4, h: 1.45, yaw: [-25, 25] }, path: 1,
  },
  reardelt: {
    title: 'الكتف الخلفي بالجهاز', prim: ['shoulders'], sec: ['back'], tempo: [1, .5, 2, .5], phases: ['افتح لورا', 'رجّع ببطء'],
    pose(t) { const P = { hip: V(0, .55, 0), pitch: 6 * D, ...SEAT(.36) }; const f = lerp(12, 92, t) * D;
      P.hands = [1, -1].map(s => V(s * .185, 1.0, .1).add(V(s * Math.sin(f) * .53, .0, Math.cos(f) * .53))); P.armPole = () => V(0, -1, .2); P.hold = ['grip', 'grip']; return P; },
    equip(M) { const g = new THREE.Group(); g.add(rbox(M.pad, .38, .08, .4, .03, 0, .46, .02)); const ch = rbox(M.pad, .34, .5, .08, .03, 0, .95, .27); ch.rotation.x = -6 * D; g.add(ch); g.add(rod(M.frame, V(0, .02, .05), V(0, .42, .05), .035), box(M.frame, .1, 1.9, .1, 0, .95, .62), box(M.frame, .8, .04, 1.3, 0, .02, .25));
      const arms = [rod(M.metal, V(), V(), .025), rod(M.metal, V(), V(), .025)], hs = [rod(M.black, V(0, -.08, 0), V(0, .08, 0), .02), rod(M.black, V(0, -.08, 0), V(0, .08, 0), .02)]; g.add(...arms, ...hs);
      return { g, update(S) { [1, -1].forEach((s, i) => { setRod(arms[i], V(s * .1, 1.5, .62), S.hands[i].clone().add(V(0, .08, 0))); hs[i].position.copy(S.hands[i]); }); } }; },
    cam: { target: V(0, 1, .1), r: 3.3, h: 1.9, yaw: [155, 205] }, path: 1, ringBack: true,
  },
  calf: {
    title: 'السمانة بجهاز الدفع', prim: ['calves'], sec: [], tempo: [.8, .6, 1.6, .4], phases: ['ادفع بأصابعك', 'رجّع ببطء'],
    pose(t) { const P = EXERCISES.legpress.pose(1); const dir = V(0, .707, .707); P.feet = P.feet.map(f => f.clone().addScaledVector(dir, lerp(-.03, .05, t))); const a = lerp(-30, 35, t) * D; P.footDir = [1, 2].map(() => V(0, Math.cos(a) * .707 + Math.sin(a) * .707, -Math.cos(a) * .707 + Math.sin(a) * .707)); return P; },
    equip(M) { return EXERCISES.legpress.equip(M); }, cam: { target: V(0, .8, .35), r: 3.6, h: 1.8, yaw: [55, 90] }, ringBack: true,
  },
  goblet: {
    title: 'السكوات بالدمبل', prim: ['quads', 'glutes'], sec: ['abs'], tempo: [2, .3, 1, .6], df: true, phases: ['انزل ببطء', 'اصعد بقوة'],
    pose(t) { const P = { hip: lv(V(0, .93, 0), V(0, .52, -.24), t), pitch: lerp(0, 34, t) * D, spine: lerp(0, -8, t) * D, feet: [V(.16, .08, .05), V(-.16, .08, .05)], kneePole: s => V(s * .35, 0, 1), footDir: [V(.3, -.1, 1), V(-.3, -.1, 1)] };
      P.hands = [1, -1].map(s => fromTorso(P, V(s * .05, .37, .2))); P.armPole = s => V(s * .3, -1, 0); P.hold = ['single', null]; return P; },
    equip(M) { return EQ.mat(M); }, cam: { target: V(0, .8, 0), r: 3.2, h: 1.3, yaw: [45, 90] }, path: 0, pathHip: true,
  },
  rdl: {
    title: 'الرفعة الرومانية بالدمبل', prim: ['hamstrings', 'glutes'], sec: ['lowerback'], tempo: [2, .3, 1, .6], df: true, phases: ['ارجع بمؤخرتك', 'اصعد واعصر'],
    pose(t) { const P = { hip: lv(V(0, .92, 0), V(0, .82, -.22), t), pitch: lerp(0, 68, t) * D, feet: [V(.12, .08, .05), V(-.12, .08, .05)], kneePole: () => V(0, 0, 1), footDir: [V(.08, -.1, 1), V(-.08, -.1, 1)] };
      P.hands = [1, -1].map(s => { const sh = fromTorso(P, V(s * .17, .45, .02)); return sh.add(V(0, -.54, .02)); }); P.armPole = () => V(0, 0, -1); P.hold = ['db', 'db']; return P; },
    equip(M) { return EQ.mat(M); }, cam: { target: V(0, .8, 0), r: 3.2, h: 1.25, yaw: [70, 105] }, ringBack: true,
  },
  /* ---------- الساعد والبطن ---------- */
  wristcurl: {
    title: 'لف الرسغ بالدمبل', prim: ['forearms'], sec: [], tempo: [.8, .4, 1.4, .4], phases: ['لف لفوگ', 'نزّل ببطء'],
    pose(t) { const P = { hip: V(0, .52, 0), pitch: 28 * D, ...SEAT(.42) }; P.elbows = [V(.11, .64, .14), V(-.11, .64, .14)]; P.hands = [1, -1].map(s => V(s * .11, lerp(.55, .69, t), .44)); P.armPole = () => V(0, -1, 0); P.hold = ['db', 'db']; return P; },
    equip(M) { const b = EQ.flatBench(M, .44); b.g.rotation.y = Math.PI / 2; b.g.position.z = -.05; return b; }, cam: { target: V(0, .6, .25), r: 2.6, h: 1.1, yaw: [50, 95] }, path: 1,
  },
  revcurl: {
    title: 'كيرل بالقبضة المقلوبة', prim: ['forearms', 'biceps'], sec: [], tempo: [1, .4, 2, .5], phases: ['ارفع', 'نزّل ببطء'],
    pose(t) { const P = { ...STAND }; P.hands = [1, -1].map(s => arc(V(s * .2, 1.11, .03), .3, 6, 128, t)); P.armPole = () => V(0, -.2, -1); P.hold = ['bar', 'bar']; return P; },
    equip(M) { const g = EQ.mat(M).g; const bar = new THREE.Group(); bar.add(rod(M.metal, V(-.42, 0, 0), V(.42, 0, 0), .014)); for (const x of [-.36, .36]) { const p = mesh(new THREE.CylinderGeometry(.09, .09, .035, 24), M.black); p.rotation.z = Math.PI / 2; p.position.x = x; bar.add(p); } g.add(bar); return { g, update(S) { bar.position.copy(S.hands[0]).add(S.hands[1]).multiplyScalar(.5); } }; },
    cam: { target: V(0, 1.05, 0), r: 3.1, h: 1.35, yaw: [45, 95] }, path: 1,
  },
  farmer: {
    title: 'مشي المزارع', prim: ['forearms', 'traps'], sec: ['abs'], tempo: [.6, .1, .6, .1], phases: ['خطوة', 'خطوة'],
    pose(t) { const P = { ...STAND, hip: V(0, .93 + Math.sin(t * Math.PI) * .01, 0) }; const l = Math.sin(t * Math.PI);
      P.feet = [V(.11, .08 + .12 * (1 - t) * l * 2, .02 + .15 * (1 - t)), V(-.11, .08 + .12 * t * l * 2, .02 + .15 * t)];
      P.hands = [V(.24, .45, .03), V(-.24, .45, .03)]; P.armPole = () => V(0, 0, -1); P.hold = ['dbn', 'dbn']; return P; },
    equip(M) { return EQ.mat(M); }, cam: { target: V(0, .9, 0), r: 3.4, h: 1.4, yaw: [20, 70] },
  },
  kneeraise: {
    title: 'رفع الركب بالعقلة', prim: ['abs'], sec: ['forearms'], tempo: [1, .5, 1.8, .5], phases: ['ارفع ركبك', 'نزّل ببطء'],
    pose(t) { const P = { hip: V(0, 1.11, lerp(0, .05, t)), pitch: lerp(0, -10, t) * D, kneePole: () => V(0, 0, 1), footDir: [V(0, -.6, .6), V(0, -.6, .6)] };
      P.knees = [1, -1].map(s => lv(V(s * .1, .69, .03), V(s * .1, 1.08, .4), t)); P.feet = [1, -1].map(s => lv(V(s * .1, .27, -.04), V(s * .1, .66, .48), t));
      P.hands = [V(.27, 2.1, 0), V(-.27, 2.1, 0)]; P.armPole = s => V(s, 0, -.3); P.hold = ['grip', 'grip']; return P; },
    equip(M) { return EXERCISES.hang.equip(M); }, cam: { target: V(0, 1.25, 0), r: 3.8, h: 1.5, yaw: [55, 95] }, path: 0, pathFoot: true,
  },
  crunch: {
    title: 'الكرنش', prim: ['abs'], sec: [], tempo: [1, .6, 1.6, .4], phases: ['ارفع كتوفك واعصر', 'نزّل ببطء'],
    pose(t) { const P = { hip: V(0, .13, .05), pitch: -90 * D, spine: lerp(0, 34, t) * D, feet: [V(.13, .07, .5), V(-.13, .07, .5)], kneePole: () => V(0, 1, .3), footDir: [V(0, -.2, 1), V(0, -.2, 1)] };
      P.hands = [1, -1].map(s => lv(V(s * .2, .14, -.12), V(s * .17, .42, .2), t)); P.armPole = s => V(s, .2, -.3); return P; },
    equip(M) { return EQ.mat(M); }, cam: { target: V(0, .25, -.05), r: 2.9, h: 1.05, yaw: [60, 100] },
  },
  /* ---------- القوام بيوم الراحة ---------- */
  hipflex: {
    title: 'إطالة الورك', prim: ['hipflex'], sec: [], tempo: [1.5, 3, 1.5, .8], hold: true, phases: ['ادفع وركك لگدام', 'ارجع', 'اثبت وتنفّس'],
    pose(t) { const P = { hip: lv(V(0, .56, -.08), V(0, .53, .05), t), pitch: lerp(0, -6, t) * D, feet: [V(.12, .08, .52), V(-.13, .1, -.78)], knees: [null, V(-.13, .06, -.36)], kneePole: () => V(0, .5, 1), footDir: [V(0, -.15, 1), V(0, -.1, -1)] };
      P.hands = [1, -1].map(s => V(s * .15, .62, .3)); P.armPole = s => V(s, 0, -.5); return P; },
    equip(M) { return EQ.mat(M); }, cam: { target: V(0, .55, -.1), r: 3.2, h: 1.2, yaw: [-78, -102] },
  },
  cat: {
    title: 'القطة', prim: ['back'], sec: ['abs'], tempo: [1.6, .8, 1.6, .8], phases: ['قوّس ظهرك لفوگ', 'نزّله ببطء'],
    pose(t) { const P = { hip: V(0, .5, -.3), pitch: lerp(84, 100, t) * D, spine: lerp(-18, 22, t) * D, feet: [V(.1, .08, -.72), V(-.1, .08, -.72)], knees: [V(.1, .06, -.3), V(-.1, .06, -.3)], kneePole: () => V(0, -1, 0), footDir: [V(0, -.2, -1), V(0, -.2, -1)] };
      P.hands = [V(.17, .03, .3), V(-.17, .03, .3)]; P.armPole = () => V(0, 0, -1); return P; },
    equip(M) { return EQ.mat(M); }, cam: { target: V(0, .45, 0), r: 3, h: 1.1, yaw: [70, 105] }, ringBack: true,
  },
  chest: {
    title: 'فتح الصدر والكتف', prim: ['chest'], sec: ['shoulders'], tempo: [1.5, 3, 1.5, .8], hold: true, phases: ['افتح صدرك', 'ارتخي', 'اثبت وتنفّس'],
    pose(t) { const P = { ...STAND, pitch: lerp(0, -6, t) * D, spine: lerp(0, -10, t) * D }; P.hands = [1, -1].map(s => lv(V(s * .05, .82, -.22), V(s * .04, .92, -.4), t)); P.armPole = s => V(s, 0, -.3); return P; },
    equip(M) { return EQ.mat(M); }, cam: { target: V(0, 1.1, 0), r: 3.2, h: 1.4, yaw: [40, 80] },
  },
  hang: {
    title: 'التعلّگ بالعقلة', prim: ['back', 'forearms'], sec: ['shoulders'], tempo: [1.2, 3, 1.2, .8], hold: true, phases: ['تعلّگ', 'انزل', 'ارتخي وتنفّس'],
    pose(t) { const P = { hip: V(0, lerp(1.08, 1.13, t), 0), pitch: 0, feet: [V(.1, .26, -.08), V(-.1, .26, -.08)], kneePole: () => V(0, 0, 1), footDir: [V(0, -.6, .6), V(0, -.6, .6)] };
      P.hands = [V(.27, 2.1, 0), V(-.27, 2.1, 0)]; P.armPole = s => V(s, 0, -.3); P.hold = ['grip', 'grip']; return P; },
    equip(M) { const g = new THREE.Group(); g.add(rod(M.metal, V(-.7, 2.12, 0), V(.7, 2.12, 0), .018)); for (const x of [-.7, .7]) g.add(box(M.frame, .09, 2.3, .09, x, 1.15, 0)); g.add(box(M.frame, 1.6, .04, .6, 0, .02, 0)); return { g }; },
    cam: { target: V(0, 1.3, 0), r: 3.8, h: 1.6, yaw: [155, 205] }, ringBack: true,
  },
  child: {
    title: 'وضعية الطفل', prim: ['back'], sec: [], tempo: [1.5, 3, 1.5, .8], hold: true, phases: ['مد إيدك لگدام', 'ارتاح', 'تنفّس ببطء'],
    pose(t) { const P = { hip: V(0, .34, -.34), pitch: lerp(112, 122, t) * D, spine: lerp(0, 8, t) * D, feet: [V(.11, .06, -.72), V(-.11, .06, -.72)], knees: [V(.13, .06, .02), V(-.13, .06, .02)], kneePole: () => V(0, 1, 0), footDir: [V(0, .1, -1), V(0, .1, -1)] };
      P.hands = [V(.17, .035, lerp(.42, .55, t)), V(-.17, .035, lerp(.42, .55, t))]; P.armPole = () => V(0, 1, 0); return P; },
    equip(M) { return EQ.mat(M); }, cam: { target: V(0, .3, 0), r: 3, h: 1.2, yaw: [65, 105] }, ringBack: true,
  },
};

/* ================= المشهد ================= */
export function createAnimator(canvas, exId, opts = {}) {
  const ex = EXERCISES[exId];
  if (opts.theme === 'green') Object.assign(opts, { bg2: '#2b4a36', bg1: '#13261b', bg0: '#040806', floor: 0x0f1c14, fog: 0x0a140e, rimC: 0x8dffb0 });
  if (opts.theme === 'brand') Object.assign(opts, { bg2: '#3a3c44', bg1: '#18191d', bg0: '#060607', floor: 0x141518, fog: 0x0c0c0e, rimC: 0xff4d4d });
  const renderer = new THREE.WebGLRenderer({ canvas, antialias: true, preserveDrawingBuffer: !!opts.capture });
  renderer.setPixelRatio(Math.min(1.6, window.devicePixelRatio || 1));
  renderer.shadowMap.enabled = true; renderer.shadowMap.type = THREE.PCFShadowMap;
  renderer.toneMapping = THREE.ACESFilmicToneMapping; renderer.toneMappingExposure = 1.05; renderer.outputColorSpace = THREE.SRGBColorSpace;
  const scene = new THREE.Scene();
  const bg = document.createElement('canvas'); bg.width = 512; bg.height = 512; const bx = bg.getContext('2d');
  const gr = bx.createRadialGradient(256, 200, 20, 256, 260, 380); gr.addColorStop(0, opts.bg2 || '#2a46c0'); gr.addColorStop(.55, opts.bg1 || '#14268a'); gr.addColorStop(1, opts.bg0 || '#070d38'); bx.fillStyle = gr; bx.fillRect(0, 0, 512, 512);
  scene.background = new THREE.CanvasTexture(bg); scene.background.colorSpace = THREE.SRGBColorSpace;
  const pm = new THREE.PMREMGenerator(renderer); scene.environment = pm.fromScene(new RoomEnvironment(), .04).texture;
  scene.fog = new THREE.Fog(opts.fog || 0x101d6a, 6, 12);
  const camera = new THREE.PerspectiveCamera(32, 1, .05, 50);
  scene.add(new THREE.HemisphereLight(0xc9dcff, 0x0a1033, .85));
  const key = new THREE.DirectionalLight(0xffffff, 2.3); key.position.set(2.5, 4.5, 3); key.castShadow = true; key.shadow.mapSize.set(768, 768);
  Object.assign(key.shadow.camera, { left: -2.2, right: 2.2, top: 2.6, bottom: -1.5, near: .5, far: 12 }); key.shadow.radius = 5; key.shadow.bias = -.0004; scene.add(key);
  const rim = new THREE.DirectionalLight(opts.rimC || 0x6fb0ff, 1.8); rim.position.set(-3, 2.5, -3); scene.add(rim);
  const fill = new THREE.PointLight(0x8fbcff, 5, 7); fill.position.set(-1.5, 1.6, 2.2); scene.add(fill);
  const floor = mesh(new THREE.CircleGeometry(9, 64), new THREE.MeshStandardMaterial({ color: opts.floor || 0x121c5a, roughness: .85 })); floor.rotation.x = -Math.PI / 2; scene.add(floor);
  const M = materials();
  if (exId !== 'hang') { const mat = box(new THREE.MeshStandardMaterial({ color: 0x0e0f12, roughness: .88 }), 1.45, .012, 2.5, 0, .006, 0); mat.castShadow = false; scene.add(mat); }
  const E = ex.equip(M); scene.add(E.g);
  const B = buildBody(M);
  scene.add(B.lower, B.armL.up, B.armL.lo, B.armR.up, B.armR.lo, B.legL.up, B.legL.lo, B.legR.up, B.legR.lo, B.footL, B.footR);
  for (const m of ex.sec) (B.mus[m] || []).forEach(x => x.material = M.glow2);
  for (const m of ex.prim) (B.mus[m] || []).forEach(x => x.material = M.glow);
  // الأشياء المحمولة
  const held = [0, 1].map(() => { const d = dumbbell(M); d.visible = false; scene.add(d); return d; });
  // دائرة الهدف
  const ringTex = (() => { const c = document.createElement('canvas'); c.width = c.height = 128; const x = c.getContext('2d'); x.strokeStyle = '#fff'; x.lineWidth = 7; x.beginPath(); x.arc(64, 64, 52, 0, 7); x.stroke(); x.lineWidth = 5; x.beginPath(); x.arc(64, 64, 30, 0, 7); x.stroke(); x.fillStyle = '#fff'; x.beginPath(); x.arc(64, 64, 9, 0, 7); x.fill(); return new THREE.CanvasTexture(c); })();
  const ring = new THREE.Sprite(new THREE.SpriteMaterial({ map: ringTex, color: 0xff6070, transparent: true, depthTest: false })); ring.renderOrder = 20; scene.add(ring);
  const L = { ua: .29, fa: .305, th: .43, sh: .42 };
  // حل الوضعية
  const E1 = new THREE.Euler(0, 0, 0, 'YXZ');
  function solve(t) {
    const P = ex.pose(t);
    B.lower.position.copy(P.hip); B.lower.rotation.set(P.pitch || 0, P.yaw || 0, P.roll || 0, 'YXZ'); B.upper.rotation.x = P.spine || 0;
    B.lower.updateMatrixWorld(true);
    const S = { P, hands: [], ankles: [], elbows: [], footDir: P.footDir.map(f => f.clone().normalize()) };
    [[B.armL, 0, 1], [B.armR, 1, -1]].forEach(([arm, i, s]) => {
      const sh = V(s * .185, .25, -.01).applyMatrix4(B.upper.matrixWorld);
      const pole = P.armPole(s);
      let el, end;
      if (P.elbows && P.elbows[i]) { el = P.elbows[i]; end = el.clone().addScaledVector(P.hands[i].clone().sub(el).normalize(), L.fa); }
      else { const r = ik(sh, P.hands[i], L.ua, L.fa, pole); el = r.mid; end = r.end; }
      orient(arm.up, sh, el, pole); arm.up.scale.y = Math.min(1.15, sh.distanceTo(el) / L.ua);
      orient(arm.lo, el, end, pole.clone().negate());
      S.hands[i] = end; S.elbows[i] = el;
    });
    [[B.legL, B.footL, 0, 1], [B.legR, B.footR, 1, -1]].forEach(([leg, foot, i, s]) => {
      const hp = V(s * .085, -.02, .01).applyMatrix4(B.lower.matrixWorld);
      const pole = P.kneePole(s);
      let kn, an;
      if (P.knees && P.knees[i]) { kn = P.knees[i]; an = kn.clone().addScaledVector(P.feet[i].clone().sub(kn).normalize(), L.sh); }
      else { const r = ik(hp, P.feet[i], L.th, L.sh, pole); kn = r.mid; an = r.end; }
      orient(leg.up, hp, kn, pole); leg.up.scale.y = Math.min(1.15, hp.distanceTo(kn) / L.th);
      orient(leg.lo, kn, an, pole.clone().negate());
      foot.position.copy(an).add(V(0, -.035, 0)); foot.quaternion.setFromUnitVectors(V(0, 0, 1), S.footDir[i]);
      S.ankles[i] = an;
    });
    // الدمبلات
    const tx = V(1, 0, 0).applyQuaternion(B.lower.quaternion);
    held.forEach(h => h.visible = false);
    (P.hold || []).forEach((k, i) => {
      if (!k || k === 'grip' || k === 'bar') return; const h = held[i]; h.visible = true;
      const f = S.hands[i].clone().sub(S.elbows[i]).normalize();
      if (k === 'single') { const m = S.hands[0].clone().add(S.hands[1]).multiplyScalar(.5); h.position.copy(m); h.quaternion.setFromUnitVectors(V(1, 0, 0), f.clone().negate()); return; }
      h.position.copy(S.hands[i]).addScaledVector(f, -.01);
      let ax = tx.clone();
      if (k === 'dbn') { ax = f.clone().cross(tx).normalize(); if (ax.lengthSq() < .1) ax.set(0, 0, 1); }
      if (k === 'dbz') ax = V(0, 0, 1);
      h.quaternion.setFromUnitVectors(V(1, 0, 0), ax);
    });
    if (E.update) E.update(S, P);
    return S;
  }
  // مسار الحركة (سهم منقّط منحني)
  const arrows = [];
  if (ex.path != null && !opts.clean) {
    const keyOf = (S, i) => ex.pathFoot ? S.ankles[i] : ex.pathHip ? B.lower.position.clone().add(V(.25, 0, 0)) : S.hands[i];
    const idx = ex.pathHand != null ? [ex.pathHand] : (ex.pathHip ? [0] : [0, 1]);
    const pts = idx.map(() => []);
    for (let k = 0; k <= 20; k++) { const S = solve(k / 20); idx.forEach((i, j) => pts[j].push(keyOf(S, i).clone())); }
    pts.forEach(pp => {
      const off = V(0, 0, 0); const curve = new THREE.CatmullRomCurve3(pp.map(p => p.clone().add(off)));
      const geo = new THREE.BufferGeometry().setFromPoints(curve.getPoints(40).slice(3, -4));
      const line = new THREE.Line(geo, new THREE.LineDashedMaterial({ color: 0xaee0ff, dashSize: .035, gapSize: .025, transparent: true, depthTest: false })); line.computeLineDistances(); line.renderOrder = 15;
      const end = curve.getPoint(.9), dir = curve.getTangent(.9);
      const head = new THREE.Mesh(new THREE.ConeGeometry(.026, .065, 16), new THREE.MeshBasicMaterial({ color: 0xaee0ff, transparent: true, depthTest: false })); head.position.copy(end); head.quaternion.setFromUnitVectors(V(0, 1, 0), dir); head.renderOrder = 15;
      scene.add(line, head); arrows.push({ line, head });
    });
  }
  const ringMeshes = B.mus[ex.prim[0]] || [];
  const [tUp, tHold, tDown, tRest] = ex.tempo, T = tUp + tHold + tDown + tRest;
  let time = 0, last = 0, playing = true, raf = 0;
  const _w = V();
  function renderTime(time) {
    const k = time % T; let t, ph;
    if (k < tUp) { t = ease(k / tUp); ph = 0 } else if (k < tUp + tHold) { t = 1; ph = 2 } else if (k < tUp + tHold + tDown) { t = 1 - ease((k - tUp - tHold) / tDown); ph = 1 } else { t = 0; ph = 3 }
    const micro = ph === 2 ? (ex.hold ? Math.abs(Math.sin(time * 2.4)) * .04 : Math.abs(Math.sin(time * 5)) * .015) : ph === 3 ? Math.abs(Math.sin(time * 3)) * .01 : 0;
    solve(Math.min(1, Math.max(0, ph === 3 ? t + micro : t - micro)));
    B.upper.scale.set(1 + Math.sin(time * 2.2) * .006, 1, 1 + Math.sin(time * 2.2) * .01);
    const c = ex.cam, yaw = (c.yaw[0] + (c.yaw[1] - c.yaw[0]) * (.5 - .5 * Math.cos(time * .22))) * D;
    camera.position.set(c.target.x + Math.sin(yaw) * c.r, c.h, c.target.z + Math.cos(yaw) * c.r); camera.lookAt(c.target);
    const act = ex.df ? t : (ex.hold ? 1 : t);
    M.glow.emissiveIntensity = .45 + .95 * act * (.75 + .25 * Math.sin(time * 6));
    // الدائرة على أقرب جزء من العضلة للكاميرا
    let best = null, bd = 1e9; ringMeshes.forEach(m => { m.getWorldPosition(_w); const d = _w.distanceTo(camera.position); if (d < bd) { bd = d; best = _w.clone(); } });
    if (best) { ring.position.copy(best).add(camera.position.clone().sub(best).normalize().multiplyScalar(.06)); ring.scale.setScalar(.1 + .04 * act); ring.material.opacity = .45 + .5 * act; }
    const show = ph === 0 || ph === 3; arrows.forEach(a => { a.line.material.opacity = show ? .95 : .2; a.head.material.opacity = show ? 1 : .2; a.line.material.dashOffset = -time * .25; });
    if (opts.onPhase) opts.onPhase(ph, Math.floor(time / T));
    renderer.render(scene, camera);
  }
  function frame(ts) { if (!playing) return; if (document.hidden) { last = 0; raf = requestAnimationFrame(frame); return; } if (last) time += Math.min(.05, (ts - last) / 1000) * (opts.speed || 1); last = ts; renderTime(time); raf = requestAnimationFrame(frame); }
  function resize() { const w = canvas.clientWidth || 300, h = canvas.clientHeight || 300; renderer.setSize(w, h, false); camera.aspect = w / h; camera.updateProjectionMatrix(); }
  resize(); const ro = window.ResizeObserver ? new ResizeObserver(resize) : null; ro ? ro.observe(canvas) : window.addEventListener('resize', resize);
  if (opts.manual) playing = false; else raf = requestAnimationFrame(frame);
  return {
    ex, renderAt: renderTime,
    stop() { playing = false; cancelAnimationFrame(raf); },
    play() { if (!playing) { playing = true; last = 0; raf = requestAnimationFrame(frame); } },
    toggle() { playing ? this.stop() : this.play(); return playing; },
    setSpeed(s) { opts.speed = s; },
    dispose() { this.stop(); ro && ro.disconnect(); renderer.dispose(); renderer.forceContextLoss && renderer.forceContextLoss(); },
  };
}
