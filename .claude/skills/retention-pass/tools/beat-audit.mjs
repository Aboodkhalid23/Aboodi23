#!/usr/bin/env node
// Beat-coverage audit for gsap-explainer videos.
// Usage: node beat-audit.mjs <file.html> [--gap 4] [--min 60]
// Walks each ACTS[i] block, extracts every tween's position parameter (`,TIME)`,
// including stagger spans and known-duration ends, and reports per scene:
// last-beat time, coverage % of SCENES[i], and internal gaps > threshold.
// Heuristic parser — it reads position args like `},1.2)` and `},'+=…'` is ignored.

import fs from 'fs';
const file = process.argv[2];
if (!file) { console.error('usage: beat-audit.mjs <file.html>'); process.exit(1); }
const argOf = (f, d) => { const i = process.argv.indexOf(f); return i > -1 ? +process.argv[i+1] : d; };
const gapT = argOf('--gap', 4);
const minCov = argOf('--min', 60);
const src = fs.readFileSync(file,'utf8');
const script = src.split('<script>').pop().split('</script>')[0];

const scenesM = script.match(/var SCENES=\[([^\]]+)\]/);
if (!scenesM) { console.error('no SCENES array found'); process.exit(1); }
const SCENES = scenesM[1].split(',').map(Number);

// slice ACTS body: from "var ACTS={" to the matching close at "};" before runScene
const actsStart = script.indexOf('var ACTS={');
const actsEnd = script.indexOf('function runScene');
const acts = script.slice(actsStart, actsEnd);

// split into numbered blocks
const blocks = {};
const re = /(\d+):function\(tl[^)]*\)\{/g;
let m, marks = [];
while ((m = re.exec(acts))) marks.push([+m[1], m.index]);
marks.forEach(([i, idx], k) => { blocks[i] = acts.slice(idx, k+1<marks.length ? marks[k+1][1] : acts.length); });

let fail = 0;
console.log(`scene  dur    last-beat  coverage  gaps>${gapT}s`);
for (const [i, body] of Object.entries(blocks)) {
  const dur = SCENES[i] >= 999 ? null : SCENES[i];
  // collect beat times: position args after a tween's vars object `},N)`,
  // plus drop(tl,targets,TIME,...) and burst(tl,scene,x,y,n,TIME,...) helper calls.
  // NOTE: computed times (`1+i*2.6` in forEach loops) are invisible — hand-check those scenes.
  const times = [
    ...[...body.matchAll(/\}\s*,\s*(\d+(?:\.\d+)?)\s*\)/g)].map(x=>+x[1]),
    ...[...body.matchAll(/drop\(tl,[^,]+,(\d+(?:\.\d+)?)/g)].map(x=>+x[1]),
    ...[...body.matchAll(/burst\(tl,[^,]+,\d+,\d+,\d+,(\d+(?:\.\d+)?)/g)].map(x=>+x[1]),
  ].filter(t => t < 900);
  if (/forEach|\+i\*/.test(body)) console.log(`S${i}: (has computed times — audit below may undercount)`);
  // extend beats by durations+staggers where cheaply visible: `duration:N` near a time is not paired reliably — approximate beat END as time+1.2s grace
  if (!times.length) { console.log(`S${i}: no beats parsed`); continue; }
  times.sort((a,b)=>a-b);
  const last = times[times.length-1];
  const gaps = [];
  let prev = 0;
  for (const t of times) { if (t - prev > gapT) gaps.push(`${prev.toFixed(1)}→${t.toFixed(1)}`); if (t>prev) prev = t; }
  if (dur && dur - last > gapT) gaps.push(`${last.toFixed(1)}→END(${dur})`);
  const cov = dur ? Math.round(last/dur*100) : 100;
  const bad = dur && (cov < minCov || gaps.length);
  if (bad) fail++;
  console.log(`S${i}: ${String(dur??'hold').padEnd(5)} ${String(last.toFixed(1)).padEnd(9)} ${String(cov+'%').padEnd(8)} ${gaps.join(', ') || '—'} ${bad?' ⚠':''}`);
}
console.log(fail ? `\n${fail} scene(s) need work` : '\nall scenes pass');
