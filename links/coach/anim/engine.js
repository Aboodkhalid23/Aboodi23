// محرك الأنيميشن: مجسّم عضلي أبيض ثلاثي الأبعاد يسوي التمرين، كله مرسوم بالكود
import * as THREE from 'three';
import { RoomEnvironment } from '../vendor/addons/RoomEnvironment.js';

const V = (x, y, z) => new THREE.Vector3(x, y, z);
const D2R = Math.PI / 180;
const ease = t => t < .5 ? 4 * t * t * t : 1 - Math.pow(-2 * t + 2, 3) / 2;

/* ---------- المواد ---------- */
function materials() {
  const skin = new THREE.MeshPhysicalMaterial({ color: 0xeef1f5, roughness: .32, metalness: 0, clearcoat: 1, clearcoatRoughness: .18, sheen: .3, sheenColor: 0xbfd4ff });
  const glow = new THREE.MeshPhysicalMaterial({ color: 0xff3347, emissive: 0xff1030, emissiveIntensity: .8, roughness: .3, clearcoat: 1 });
  const glow2 = new THREE.MeshPhysicalMaterial({ color: 0xd8ecff, emissive: 0x2a8cff, emissiveIntensity: .12, roughness: .3, clearcoat: 1 });
  const metal = new THREE.MeshStandardMaterial({ color: 0xc9ced6, metalness: .9, roughness: .25 });
  const black = new THREE.MeshStandardMaterial({ color: 0x15171c, metalness: .2, roughness: .55 });
  const pad = new THREE.MeshStandardMaterial({ color: 0x1c1f26, metalness: .05, roughness: .6 });
  const frame = new THREE.MeshStandardMaterial({ color: 0x2b2f38, metalness: .7, roughness: .35 });
  return { skin, glow, glow2, metal, black, pad, frame };
}

/* ---------- أشكال مساعدة ---------- */
const SPH = new THREE.SphereGeometry(1, 40, 28);
function ell(mat, sx, sy, sz, x = 0, y = 0, z = 0, rx = 0, ry = 0, rz = 0) {
  const m = new THREE.Mesh(SPH, mat); m.scale.set(sx, sy, sz); m.position.set(x, y, z); m.rotation.set(rx, ry, rz); m.castShadow = true; m.receiveShadow = true; return m;
}
function cap(mat, r, len, y0) { // كبسولة على محور -Y تبدي من y0
  const g = new THREE.CapsuleGeometry(r, len, 8, 24); const m = new THREE.Mesh(g, mat); m.position.y = y0 - len / 2; m.castShadow = true; return m;
}

/* ---------- المجسّم ----------
   كل طرف مجموعة منفصلة؛ محوره -Y على طول العظم، و+Z صوب اتجاه الثني (pole) */
function buildBody(M) {
  const B = { parts: {}, muscles: {} };
  const reg = (name, mesh) => { (B.muscles[name] = B.muscles[name] || []).push(mesh); return mesh; };
  // الجذع: الأصل بالحوض، +Y للأعلى، +Z للصدر
  const torso = new THREE.Group();
  torso.add(ell(M.skin, .145, .1, .11, 0, .02, 0));                    // حوض
  torso.add(ell(M.skin, .125, .15, .09, 0, .18, .0));                 // بطن
  for (let r = 0; r < 3; r++) for (const s of [-1, 1]) torso.add(reg('abs', ell(M.skin, .03, .024, .012, s * .033, .12 + r * .058, .088)));
  torso.add(ell(M.skin, .165, .165, .115, 0, .35, -.005));               // قفص صدري
  for (const s of [-1, 1]) {
    torso.add(reg('chest', ell(M.skin, .088, .062, .045, s * .074, .385, .093, .15, s * -.25, s * .2)));
    torso.add(reg('back', ell(M.skin, .06, .15, .075, s * .125, .31, -.035, 0, 0, s * .12)));        // اللاتس
    torso.add(reg('glutes', ell(M.skin, .075, .078, .068, s * .065, -.01, -.065)));
    torso.add(reg('obliques', ell(M.skin, .035, .08, .05, s * .11, .16, .015)));
  }
  torso.add(reg('traps', ell(M.skin, .13, .05, .075, 0, .495, -.03)));
  torso.add(reg('back', ell(M.skin, .15, .12, .06, 0, .4, -.075)));
  torso.add(reg('lowerback', ell(M.skin, .09, .08, .05, 0, .12, -.075)));
  const neck = cap(M.skin, .048, .07, .6); torso.add(neck);
  torso.add(ell(M.skin, .082, .108, .094, 0, .68, .008));                // راس
  torso.add(ell(M.skin, .06, .045, .07, 0, .615, .03));                  // فك
  B.torso = torso;
  // الأطراف
  function limb(kind, side) {
    const up = new THREE.Group(), lo = new THREE.Group();
    if (kind === 'arm') {
      up.add(cap(M.skin, .036, .25, 0));
      up.add(reg('shoulders', ell(M.skin, .062, .07, .062, 0, -.025, 0)));
      up.add(reg('biceps', ell(M.skin, .038, .085, .042, 0, -.15, -.022)));
      up.add(reg('triceps', ell(M.skin, .04, .095, .042, 0, -.14, .024)));
      lo.add(cap(M.skin, .029, .22, 0));
      lo.add(reg('forearms', ell(M.skin, .038, .09, .037, 0, -.075, 0)));
      lo.add(ell(M.skin, .036, .055, .022, 0, -.29, 0));                   // كف
    } else {
      up.add(cap(M.skin, .05, .36, 0));
      up.add(reg('quads', ell(M.skin, .064, .19, .064, 0, -.19, .016)));
      up.add(reg('hamstrings', ell(M.skin, .056, .17, .054, 0, -.2, -.02)));
      lo.add(cap(M.skin, .034, .36, 0));
      lo.add(reg('calves', ell(M.skin, .046, .1, .047, 0, -.12, -.026)));
    }
    return { up, lo };
  }
  B.armL = limb('arm', 1); B.armR = limb('arm', -1); B.legL = limb('leg', 1); B.legR = limb('leg', -1);
  B.footL = ell(M.skin, .045, .035, .115); B.footR = ell(M.skin, .045, .035, .115);
  return B;
}

/* ---------- حركة الطرف بطريقة "الحل العكسي" ---------- */
const _x = new THREE.Vector3(), _y = new THREE.Vector3(), _z = new THREE.Vector3(), _m = new THREE.Matrix4();
function orient(group, from, to, pole) {
  _y.subVectors(from, to).normalize();                         // +Y صوب البداية (الطرف ممتد على -Y)
  _z.copy(pole).addScaledVector(_y, -pole.dot(_y)).normalize(); // +Z صوب اتجاه الثني
  _x.crossVectors(_y, _z).normalize();
  _m.makeBasis(_x, _y, _z); group.position.copy(from); group.quaternion.setFromRotationMatrix(_m);
}
function ik(root, target, a, b, pole) {
  const d0 = target.clone().sub(root); let d = Math.min(a + b - 1e-4, Math.max(Math.abs(a - b) + 1e-3, d0.length()));
  const u = d0.normalize(); const p = pole.clone().addScaledVector(u, -pole.dot(u)).normalize();
  const c = (a * a + d * d - b * b) / (2 * a * d), s = Math.sqrt(Math.max(0, 1 - c * c));
  const elbow = root.clone().addScaledVector(u, a * c).addScaledVector(p, a * s);
  const end = elbow.clone().addScaledVector(target.clone().sub(elbow).normalize(), b);
  return { elbow, end };
}

/* ---------- المعدّات ---------- */
function dumbbell(M) {
  const g = new THREE.Group();
  const h = new THREE.Mesh(new THREE.CylinderGeometry(.016, .016, .2, 16), M.metal); h.rotation.z = Math.PI / 2; g.add(h);
  for (const s of [-1, 1]) {
    const p = new THREE.Mesh(new THREE.CylinderGeometry(.065, .065, .055, 6), M.black); p.rotation.z = Math.PI / 2; p.position.x = s * .1; p.castShadow = true; g.add(p);
    const c = new THREE.Mesh(new THREE.CylinderGeometry(.02, .02, .06, 16), M.metal); c.rotation.z = Math.PI / 2; c.position.x = s * .1; g.add(c);
  }
  return g;
}
function inclineBench(M, angle) {
  const g = new THREE.Group();
  const seat = new THREE.Mesh(new THREE.BoxGeometry(.32, .07, .36), M.pad); seat.position.set(0, .45, .08); seat.castShadow = seat.receiveShadow = true; g.add(seat);
  const back = new THREE.Mesh(new THREE.BoxGeometry(.3, .07, .82), M.pad); back.castShadow = back.receiveShadow = true;
  back.rotation.x = angle * D2R; back.position.set(0, .44 + Math.sin(angle * D2R) * .38, -.05 - Math.cos(angle * D2R) * .38); g.add(back);
  const bar = (x1, y1, z1, x2, y2, z2, r = .022) => { const a = V(x1, y1, z1), b = V(x2, y2, z2); const m = new THREE.Mesh(new THREE.CylinderGeometry(r, r, a.distanceTo(b), 12), M.frame); m.position.copy(a.clone().add(b).multiplyScalar(.5)); m.quaternion.setFromUnitVectors(V(0, 1, 0), b.clone().sub(a).normalize()); m.castShadow = true; g.add(m); };
  bar(0, .02, .45, 0, .02, -.75, .03); bar(0, .02, .2, 0, .41, .1); bar(0, .02, -.5, 0, .58, -.42);
  bar(-.2, .02, .45, .2, .02, .45, .03); bar(-.22, .02, -.75, .22, .02, -.75, .03);
  return g;
}

/* ---------- التمارين ---------- */
export const EXERCISES = {
  incline: {
    title: 'ضغط الصدر المائل بالدمبل', sets: '٣ × ٨-١٠', prim: ['chest'], sec: ['shoulders', 'triceps'],
    tempo: [1, .35, 2, .55], phases: ['ادفع لفوگ', 'نزّل ببطء'],
    setup(scene, M) { const b = inclineBench(M, 38); scene.add(b); },
    pose(t) { // t = 0 بالأسفل، 1 بالأعلى
      const hip = V(0, .56, .04);
      const torsoRot = -52 * D2R;
      const handsA = [V(.33, .97, -.27), V(-.33, .97, -.27)], handsB = [V(.17, 1.35, -.36), V(-.17, 1.35, -.36)];
      return {
        hip, torsoRot,
        hands: handsA.map((a, i) => a.clone().lerp(handsB[i], t)),
        armPole: s => V(s * 1, -.55, -.35),
        feet: [V(.21, .085, .66), V(-.21, .085, .66)], kneePole: () => V(0, .6, 1), footDir: V(0, -.25, 1),
        dumbbells: true,
      };
    },
    arrows(P0, P1) { return [[P0.hands[0], P1.hands[0]], [P0.hands[1], P1.hands[1]]]; },
    cam: { target: V(0, .82, -.15), radius: 3.1, height: 1.85, yaw: [25, 70] },
  },
};

/* ---------- المشهد ---------- */
export function createAnimator(canvas, exId, opts = {}) {
  const ex = EXERCISES[exId];
  const renderer = new THREE.WebGLRenderer({ canvas, antialias: true, alpha: false, preserveDrawingBuffer: !!opts.capture });
  renderer.setPixelRatio(Math.min(2, window.devicePixelRatio || 1));
  renderer.shadowMap.enabled = true; renderer.shadowMap.type = THREE.PCFSoftShadowMap;
  renderer.toneMapping = THREE.ACESFilmicToneMapping; renderer.toneMappingExposure = 1.05;
  renderer.outputColorSpace = THREE.SRGBColorSpace;
  const scene = new THREE.Scene();
  // خلفية زرقة متدرجة
  const bg = document.createElement('canvas'); bg.width = 2; bg.height = 256; const bx = bg.getContext('2d');
  const gr = bx.createLinearGradient(0, 0, 0, 256); gr.addColorStop(0, '#0d1a5c'); gr.addColorStop(.55, '#1d3399'); gr.addColorStop(1, '#0a1240'); bx.fillStyle = gr; bx.fillRect(0, 0, 2, 256);
  scene.background = new THREE.CanvasTexture(bg); scene.background.colorSpace = THREE.SRGBColorSpace;
  const pm = new THREE.PMREMGenerator(renderer); scene.environment = pm.fromScene(new RoomEnvironment(), .04).texture;
  scene.fog = new THREE.Fog(0x14246e, 5, 11);
  const camera = new THREE.PerspectiveCamera(32, 1, .05, 50);
  // الإضاءة
  scene.add(new THREE.HemisphereLight(0xc9dcff, 0x0a1033, .9));
  const key = new THREE.DirectionalLight(0xffffff, 2.2); key.position.set(2.5, 4.5, 3); key.castShadow = true; key.shadow.mapSize.set(1024, 1024);
  Object.assign(key.shadow.camera, { left: -2, right: 2, top: 2, bottom: -2, near: .5, far: 12 }); key.shadow.radius = 4; key.shadow.bias = -.0004; scene.add(key);
  const rim = new THREE.DirectionalLight(0x5fa8ff, 1.6); rim.position.set(-3, 2.5, -3); scene.add(rim);
  const fill = new THREE.PointLight(0x7fb2ff, 6, 6); fill.position.set(-1.5, 1.4, 2); scene.add(fill);
  // الأرض والحصيرة
  const floor = new THREE.Mesh(new THREE.PlaneGeometry(30, 30), new THREE.MeshStandardMaterial({ color: 0x14205e, roughness: .9 })); floor.rotation.x = -Math.PI / 2; floor.receiveShadow = true; scene.add(floor);
  const M = materials();
  const mat = new THREE.Mesh(new THREE.BoxGeometry(1.5, .012, 2.3), new THREE.MeshStandardMaterial({ color: 0x101114, roughness: .85 })); mat.position.y = .006; mat.receiveShadow = true; scene.add(mat);
  ex.setup(scene, M);
  // المجسّم
  const B = buildBody(M);
  scene.add(B.torso, B.armL.up, B.armL.lo, B.armR.up, B.armR.lo, B.legL.up, B.legL.lo, B.legR.up, B.legR.lo, B.footL, B.footR);
  for (const m of ex.prim) (B.muscles[m] || []).forEach(x => x.material = M.glow);
  for (const m of ex.sec) (B.muscles[m] || []).forEach(x => x.material = M.glow2);
  const dbs = [dumbbell(M), dumbbell(M)]; dbs.forEach(d => scene.add(d));
  // دائرة الهدف على العضلة
  const ringTex = (() => { const c = document.createElement('canvas'); c.width = c.height = 128; const x = c.getContext('2d'); x.strokeStyle = '#fff'; x.lineWidth = 7; x.beginPath(); x.arc(64, 64, 52, 0, 7); x.stroke(); x.lineWidth = 5; x.beginPath(); x.arc(64, 64, 30, 0, 7); x.stroke(); x.fillStyle = '#fff'; x.beginPath(); x.arc(64, 64, 9, 0, 7); x.fill(); const t = new THREE.CanvasTexture(c); return t; })();
  const ring = new THREE.Sprite(new THREE.SpriteMaterial({ map: ringTex, color: 0xff5a6a, transparent: true, depthTest: false, opacity: .9 })); ring.scale.set(.12, .12, 1); scene.add(ring);
  // أسهم منقّطة تبيّن مسار الحركة
  const P0 = ex.pose(0), P1 = ex.pose(1);
  const arrows = ex.arrows(P0, P1).map(([a, b]) => {
    const g = new THREE.Group();
    const geo = new THREE.BufferGeometry().setFromPoints([a.clone().add(V(0, .03, 0)), b.clone().add(V(0, -.05, 0))]);
    const line = new THREE.Line(geo, new THREE.LineDashedMaterial({ color: 0x9fdcff, dashSize: .035, gapSize: .025, transparent: true, depthTest: false })); line.computeLineDistances(); g.add(line);
    const head = new THREE.Mesh(new THREE.ConeGeometry(.025, .06, 16), new THREE.MeshBasicMaterial({ color: 0x9fdcff, transparent: true, depthTest: false }));
    head.position.copy(b.clone().add(V(0, -.02, 0))); head.quaternion.setFromUnitVectors(V(0, 1, 0), b.clone().sub(a).normalize()); g.add(head);
    g.renderOrder = 10; scene.add(g); return { g, line, head };
  });

  const L = { ua: .29, fa: .27, th: .43, sh: .42 };
  function apply(t) {
    const P = ex.pose(t);
    B.torso.position.copy(P.hip); B.torso.rotation.set(P.torsoRot, 0, 0);
    B.torso.updateMatrixWorld();
    [[B.armL, 0, 1], [B.armR, 1, -1]].forEach(([arm, i, s]) => {
      const sh = V(s * .19, .455, -.005).applyMatrix4(B.torso.matrixWorld);
      const r = ik(sh, P.hands[i], L.ua, L.fa, P.armPole(s));
      orient(arm.up, sh, r.elbow, P.armPole(s)); orient(arm.lo, r.elbow, r.end, P.armPole(s));
      if (P.dumbbells) { dbs[i].position.copy(r.end); dbs[i].quaternion.copy(B.torso.quaternion); }
    });
    [[B.legL, B.footL, 0, 1], [B.legR, B.footR, 1, -1]].forEach(([leg, foot, i, s]) => {
      const hp = V(s * .085, -.01, .015).applyMatrix4(B.torso.matrixWorld).lerp(P.hip.clone().add(V(s * .085, -.02, .02)), .6);
      const r = ik(hp, P.feet[i], L.th, L.sh, P.kneePole(s));
      orient(leg.up, hp, r.elbow, P.kneePole(s)); orient(leg.lo, r.elbow, r.end, P.kneePole(s).clone().negate());
      foot.position.copy(r.end).add(P.footDir.clone().normalize().multiplyScalar(.075)).add(V(0, -.03, 0)); foot.quaternion.setFromUnitVectors(V(0, 0, 1), P.footDir.clone().normalize());
    });
    const ch = V(.075, .39, .14).applyMatrix4(B.torso.matrixWorld); ring.position.copy(ch);
  }
  // التوقيت
  const [tUp, tHold, tDown, tRest] = ex.tempo, T = tUp + tHold + tDown + tRest;
  let time = 0, last = 0, playing = true, raf = 0;
  const hud = opts.onPhase || (() => {});
  function frame(ts) {
    if (!playing) return;
    if (last) time += Math.min(.05, (ts - last) / 1000) * (opts.speed || 1); last = ts;
    renderTime(time);
    raf = requestAnimationFrame(frame);
  }
  function renderTime(time) {
    const k = time % T; let t, ph;
    if (k < tUp) { t = ease(k / tUp); ph = 0 } else if (k < tUp + tHold) { t = 1; ph = 2 } else if (k < tUp + tHold + tDown) { t = 1 - ease((k - tUp - tHold) / tDown); ph = 1 } else { t = 0; ph = 3 }
    apply(t);
    const pulse = .55 + .45 * Math.sin(time * 6);
    M.glow.emissiveIntensity = .45 + .9 * t * (.7 + .3 * pulse);
    ring.material.opacity = .5 + .5 * t; ring.scale.setScalar(.1 + .04 * t);
    const show = ph === 0 || ph === 3; arrows.forEach(a => { a.line.material.opacity = show ? .9 : .15; a.head.material.opacity = show ? 1 : .15; a.line.material.dashOffset = -time * .25; });
    hud(ph, Math.floor(time / T));
    // كاميرا تدور ببطء
    const c = ex.cam, yaw = (c.yaw[0] + (c.yaw[1] - c.yaw[0]) * (.5 - .5 * Math.cos(time * .25))) * D2R;
    camera.position.set(c.target.x + Math.sin(yaw) * c.radius, c.height, c.target.z + Math.cos(yaw) * c.radius); camera.lookAt(c.target);
    renderer.render(scene, camera);
  }
  function resize() { const w = canvas.clientWidth, h = canvas.clientHeight; renderer.setSize(w, h, false); camera.aspect = w / h; camera.updateProjectionMatrix(); }
  resize(); window.addEventListener('resize', resize);
  if (opts.manual) playing = false; else raf = requestAnimationFrame(frame);
  return {
    renderAt: renderTime,
    ex,
    stop() { playing = false; cancelAnimationFrame(raf); },
    play() { if (!playing) { playing = true; last = 0; raf = requestAnimationFrame(frame); } },
    dispose() { this.stop(); window.removeEventListener('resize', resize); renderer.dispose(); },
  };
}
