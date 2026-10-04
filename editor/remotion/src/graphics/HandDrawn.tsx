import React from 'react';
import {interpolate, random, useCurrentFrame, useVideoConfig} from 'remotion';
import {ease} from '../style';

// Vox-style marks drawn by hand that "boil": the line is redrawn with a new wobble ~8 times a second.
const BOIL = 4;           // frames per wobble at 30 fps

const wobble = (seed: string, n: number, amp: number) => Array.from({length: n}, (_, i) => (random(`${seed}-${i}`) - 0.5) * 2 * amp);

/** A loose ellipse that overshoots where it closes, like a marker circle around a word. */
export const ScribbleCircle: React.FC<{w: number; h: number; color: string; draw: number; seed: string}> = ({w, h, color, draw, seed}) => {
  const pts = 40, turns = 1.12;
  const j = wobble(seed, pts + 1, Math.min(w, h) * 0.035);
  const d = Array.from({length: pts + 1}, (_, i) => {
    const t = (i / pts) * turns * Math.PI * 2 - 0.5;
    const rx = w / 2 + j[i], ry = h / 2 + j[(i + 7) % pts];
    return `${i ? 'L' : 'M'}${(w / 2 + Math.cos(t) * rx).toFixed(1)},${(h / 2 + Math.sin(t) * ry).toFixed(1)}`;
  }).join(' ');
  return (
    <svg width={w} height={h} style={{overflow: 'visible'}}>
      <path d={d} fill="none" stroke={color} strokeWidth={9} strokeLinecap="round" strokeLinejoin="round"
        pathLength={1} strokeDasharray={1} strokeDashoffset={1 - draw} />
    </svg>
  );
};

export const ScribbleLine: React.FC<{w: number; color: string; draw: number; seed: string; arrow?: boolean; dx?: number; dy?: number}> =
  ({w, color, draw, seed, arrow, dx = w, dy = 0}) => {
    const j = wobble(seed, 6, 6);
    const d = `M0,${j[0]} Q${dx * 0.5 + j[1]},${dy * 0.5 - 18 + j[2]} ${dx + j[3]},${dy + j[4]}`;
    const ang = Math.atan2(dy, dx);
    const hx = dx + j[3], hy = dy + j[4];
    const head = (a: number) => `${hx - Math.cos(ang + a) * 34},${hy - Math.sin(ang + a) * 34}`;
    return (
      <svg width={Math.abs(dx) + 40} height={Math.abs(dy) + 40} style={{overflow: 'visible'}}>
        <path d={d} fill="none" stroke={color} strokeWidth={9} strokeLinecap="round" pathLength={1}
          strokeDasharray={1} strokeDashoffset={1 - draw} />
        {arrow && draw > 0.92 && <path d={`M${head(0.5)} L${hx},${hy} L${head(-0.5)}`} fill="none" stroke={color}
          strokeWidth={9} strokeLinecap="round" strokeLinejoin="round" />}
      </svg>
    );
  };

/** Shared timing: draw on over ~0.45 s from `start`, then boil. Returns [draw progress, boil seed]. */
export const useDraw = (start: number, key: string): [number, string] => {
  const f = useCurrentFrame();
  const {fps} = useVideoConfig();
  const draw = interpolate(f - start, [0, 0.45 * fps], [0, 1], {extrapolateLeft: 'clamp', extrapolateRight: 'clamp', easing: ease});
  return [draw, `${key}-${Math.floor(f / BOIL)}`];
};
