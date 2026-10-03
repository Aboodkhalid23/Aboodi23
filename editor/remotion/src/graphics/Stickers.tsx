import React from 'react';
import {interpolate, spring, useCurrentFrame, useVideoConfig} from 'remotion';
import {ease, StyleProps} from '../style';

export type Sticker = {type: 'stamp' | 'arrow' | 'burst' | 'tape' | 'circle'; text?: string; at?: number;
  x?: number; y?: number; rotate?: number};

type Spots = Record<Sticker['type'], [number, number]>;
// Default spots (fraction of the frame) that keep stickers off the presenter's face (centre-top)…
export const FACE_SPOTS: Spots = {
  stamp: [0.8, 0.72], arrow: [0.27, 0.42], burst: [0.18, 0.25], tape: [0.5, 0.86], circle: [0.5, 0.36],
};
// …and, in the subscribe / TV scenes, off the shrunken player and the channel bar.
export const SCENE_SPOTS: Spots = {
  stamp: [0.9, 0.3], arrow: [0.1, 0.55], burst: [0.1, 0.28], tape: [0.5, 0.95], circle: [0.5, 0.33],
};

const BURST = Array.from({length: 24}, (_, i) => {
  const a = (i / 24) * Math.PI * 2;
  const r = i % 2 ? 0.36 : 0.5;
  return `${50 + Math.cos(a) * r * 100}% ${50 + Math.sin(a) * r * 100}%`;
}).join(', ');

/** One sticker: pops in with a spring at `at` seconds, settles, then holds (a tiny wobble keeps it alive). */
const One: React.FC<{s: Sticker; style: StyleProps; W: number; H: number; spots: Spots}> = ({s, style, W, H, spots}) => {
  const f = useCurrentFrame();
  const {fps} = useVideoConfig();
  const start = Math.round((s.at ?? 0.3) * fps);
  if (f < start) return null;
  const k = spring({frame: f - start, fps, config: {damping: 11, stiffness: 170}});
  const wobble = Math.sin((f - start) / fps * 2.2) * 1.2;
  const [dx, dy] = spots[s.type];
  const x = (s.x ?? dx) * W;
  const y = (s.y ?? dy) * H;
  const p = style.palette as Record<string, string>;
  const red = p.red ?? '#C4382E';
  const base: React.CSSProperties = {position: 'absolute', left: x, top: y, direction: 'rtl',
    transform: `translate(-50%, -50%) scale(${k}) rotate(${(s.rotate ?? -8) + wobble}deg)`};
  const draw = interpolate(f - start, [0, 0.45 * fps], [0, 1], {extrapolateRight: 'clamp', easing: ease});

  switch (s.type) {
    case 'stamp':
      return (
        <div style={{...base, border: `10px solid ${red}`, borderRadius: 18, padding: '14px 40px', color: red,
          fontFamily: 'Lalezar', fontSize: 110, lineHeight: 1.1, opacity: 0.94,
          background: 'rgba(255,255,255,.85)', boxShadow: `inset 0 0 0 4px ${red}`}}>{s.text}</div>
      );
    case 'burst':
      return (
        <div style={{...base, width: 380, height: 380, clipPath: `polygon(${BURST})`, background: style.palette.accent,
          display: 'flex', alignItems: 'center', justifyContent: 'center', filter: 'drop-shadow(0 10px 18px rgba(0,0,0,.35))'}}>
          <span style={{fontFamily: 'Lalezar', fontSize: 84, color: style.palette.ink, textAlign: 'center', maxWidth: 230,
            lineHeight: 1.05}}>{s.text}</span>
        </div>
      );
    case 'tape':
      return (
        <div style={{...base, background: 'rgba(242,235,221,.94)', padding: '16px 60px', fontFamily: 'Tajawal', fontWeight: 900,
          fontSize: 64, color: style.palette.ink, boxShadow: '0 8px 16px rgba(0,0,0,.25)',
          clipPath: 'polygon(2% 0, 98% 4%, 100% 50%, 97% 100%, 3% 96%, 0 50%)'}}>{s.text}</div>
      );
    case 'circle':
      return (
        <svg style={{...base, overflow: 'visible'}} width={520} height={360} viewBox="0 0 520 360">
          <ellipse cx={260} cy={180} rx={240} ry={160} fill="none" stroke={red} strokeWidth={12} strokeLinecap="round"
            strokeDasharray={1300} strokeDashoffset={1300 * (1 - draw)} transform="rotate(-6 260 180)" />
        </svg>
      );
    case 'arrow':
      return (
        <div style={{...base, display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 6}}>
          {s.text && <span style={{fontFamily: 'Aref Ruqaa', fontWeight: 700, fontSize: 96, color: '#fff',
            textShadow: '0 4px 12px rgba(0,0,0,.7)'}}>{s.text}</span>}
          <svg width={300} height={160} viewBox="0 0 300 160" style={{overflow: 'visible'}}>
            <path d="M20 30 C 110 10, 200 40, 260 120" fill="none" stroke="#fff" strokeWidth={12} strokeLinecap="round"
              strokeDasharray={340} strokeDashoffset={340 * (1 - draw)} style={{filter: 'drop-shadow(0 4px 8px rgba(0,0,0,.6))'}} />
            <path d="M220 118 L262 124 L258 82" fill="none" stroke="#fff" strokeWidth={12} strokeLinecap="round"
              strokeLinejoin="round" opacity={draw > 0.9 ? 1 : 0} />
          </svg>
        </div>
      );
  }
};

export const Stickers: React.FC<{stickers: Sticker[]; style: StyleProps; W: number; H: number; spots?: Spots}> =
  ({stickers, spots = FACE_SPOTS, ...rest}) => <>{stickers.map((s, i) => <One key={i} s={s} spots={spots} {...rest} />)}</>;
