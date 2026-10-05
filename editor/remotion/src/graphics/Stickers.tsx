import React from 'react';
import {interpolate, spring, useCurrentFrame, useVideoConfig} from 'remotion';
import {ease, StyleProps} from '../style';
import {Img, staticFile} from 'remotion';
import {Lottie, LottieAnimationData} from '@remotion/lottie';
import {ScribbleCircle, ScribbleLine, useDraw} from './HandDrawn';

export type Sticker = {type: 'stamp' | 'arrow' | 'burst' | 'tape' | 'circle' | 'scribble_circle' | 'scribble_arrow'
  | 'scribble_underline' | 'censor' | 'name_tag' | 'emoji' | 'icon'; text?: string; data?: LottieAnimationData; src?: string; at?: number; x?: number; y?: number; rotate?: number;
  w?: number; h?: number; to?: [number, number]; color?: string};

type Spots = Record<Sticker['type'], [number, number]>;
// Default spots (fraction of the frame) that keep stickers off the presenter's face (centre-top)…
export const FACE_SPOTS: Spots = {
  stamp: [0.8, 0.72], arrow: [0.27, 0.42], burst: [0.18, 0.25], tape: [0.5, 0.86], circle: [0.5, 0.36],
  scribble_circle: [0.5, 0.4], scribble_arrow: [0.25, 0.5], scribble_underline: [0.5, 0.75], censor: [0.5, 0.35], name_tag: [0.5, 0.8], emoji: [0.86, 0.17], icon: [0.14, 0.17],
};
// …and, in the subscribe / TV scenes, off the shrunken player and the channel bar.
export const SCENE_SPOTS: Spots = {
  stamp: [0.9, 0.3], arrow: [0.1, 0.55], burst: [0.1, 0.28], tape: [0.5, 0.95], circle: [0.5, 0.33],
  scribble_circle: [0.5, 0.4], scribble_arrow: [0.25, 0.5], scribble_underline: [0.5, 0.75], censor: [0.5, 0.35], name_tag: [0.5, 0.8], emoji: [0.88, 0.2], icon: [0.12, 0.2],
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
  const [ink, seed] = useDraw(start, `${s.type}${s.x}${s.y}`);   // hooks before any early return
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

  const pen = s.color ?? (s.type === 'scribble_circle' ? '#2B4BDB' : red);
  const at = (w: number, h: number): React.CSSProperties => ({position: 'absolute', left: x - w / 2, top: y - h / 2});
  switch (s.type) {
    case 'scribble_circle': {
      const w = (s.w ?? 0.22) * W, h = (s.h ?? 0.12) * H;
      return <div style={at(w, h)}><ScribbleCircle w={w} h={h} color={pen} draw={ink} seed={seed} /></div>;
    }
    case 'scribble_underline': {
      const w = (s.w ?? 0.3) * W;
      return <div style={at(w, 20)}><ScribbleLine w={w} color={pen} draw={ink} seed={seed} /></div>;
    }
    case 'scribble_arrow': {
      const [tx, ty] = s.to ?? [(s.x ?? dx) + 0.12, (s.y ?? dy) - 0.1];
      return <div style={{position: 'absolute', left: x, top: y}}>
        <ScribbleLine w={0} color={pen} draw={ink} seed={seed} arrow dx={tx * W - x} dy={ty * H - y} />
        {s.text && <div style={{position: 'absolute', left: -40, top: 20, transform: 'translateX(-100%)', whiteSpace: 'nowrap',
          fontFamily: 'Alkalami', fontSize: 64, color: pen, direction: 'rtl'}}>{s.text}</div>}
      </div>;
    }
    case 'censor': {
      const w = (s.w ?? 0.2) * W, h = (s.h ?? 0.065) * H;   // sized to the face when Python found it
      return <div style={{...at(w, h), width: w, height: h, background: '#0A0A0A', transform: `rotate(${s.rotate ?? -2}deg) scaleX(${k})`,
        display: 'flex', alignItems: 'center', justifyContent: 'center', color: '#fff', fontFamily: 'Archivo Black, Blaka', fontSize: h * 0.62,
        direction: /[\u0600-\u06FF]/.test(s.text ?? '') ? 'rtl' : 'ltr', letterSpacing: 1}}>{s.text}</div>;
    }
    case 'emoji': {   // Google Noto animated emoji (Lottie): it moves by itself, the spring pops it in
      const w = (s.w ?? 0.12) * W;
      return s.data ? <div style={{...base, width: w, height: w}}><Lottie animationData={s.data} loop style={{width: w, height: w}} /></div> : null;
    }
    case 'icon': {    // Iconify SVG (free-licence sets only, kits.py)
      const w = (s.w ?? 0.1) * W;
      return s.src ? <div style={{...base, width: w, height: w, filter: 'drop-shadow(0 10px 14px rgba(0,0,0,.3))'}}>
        <Img src={staticFile(s.src)} style={{width: '100%', height: '100%'}} /></div> : null;
    }
    case 'name_tag':
      return <div style={{position: 'absolute', left: x, top: y, transform: `translate(-50%, -50%) rotate(${s.rotate ?? -3}deg) scale(${k})`,
        background: '#FBF8F1', padding: '10px 30px', fontFamily: 'Aref Ruqaa Ink', fontWeight: 700, fontSize: 54, color: style.palette.ink,
        direction: 'rtl', whiteSpace: 'nowrap', boxShadow: '0 8px 16px rgba(0,0,0,.3)', borderBottom: `6px solid ${red}`}}>{s.text}</div>;
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
