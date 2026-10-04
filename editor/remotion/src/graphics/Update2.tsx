/** Scenes from the research update (editor/styles/updates/2026-10-04-research.md):
 *  - HeadlineStorm: newspaper clippings slam onto the desk one after another, the camera shakes on each landing,
 *    and the last one gets the yellow marker ("the whole world was writing about it").
 *  - UnitChart: a number made visible — a grid of people, and the share the story is about lights up in the
 *    accent colour while the count runs ("1 in 5"). */
import React from 'react';
import {AbsoluteFill, interpolate, random, spring, staticFile, useCurrentFrame, useVideoConfig} from 'remotion';
import {appear, BaseProps, boil, ease, formatNumber, useFonts} from '../style';

const TORN = 'polygon(0% 3%, 8% 0%, 17% 2.5%, 29% 0.5%, 41% 2%, 55% 0%, 68% 2.5%, 81% 0.5%, 92% 2%, 100% 0%, 99% 30%, 100% 62%, 99% 100%, 86% 97.5%, 71% 100%, 57% 98%, 43% 100%, 30% 97.5%, 16% 100%, 4% 98%, 0% 100%, 1% 65%, 0% 33%)';

/** Seconds between landings: shared with Python (compose.headline_cues) so each landing gets its paper sound. */
export const stormGap = (n: number, dur: number) => Math.min(0.6, Math.max(0.25, (dur * 0.55) / Math.max(1, n)));
export const STORM_FIRST = 0.15;

type Clip = {outlet?: string; title: string};

export const HeadlineStorm: React.FC<BaseProps & {items: Clip[]; highlight?: string}> = ({style, durationSec, items, highlight}) => {
  useFonts();
  const f = useCurrentFrame();
  const {fps} = useVideoConfig();
  const n = items.length;
  const gap = stormGap(n, durationSec);
  const lands = items.map((_, i) => Math.round((STORM_FIRST + i * gap) * fps));
  // camera: slow push + a decaying shake after every landing
  let shake = 0;
  for (const at of lands) {
    const d = f - at;
    if (d >= 0 && d < 10) shake += Math.sin(d * 2.4) * 9 * Math.exp(-d / 3);
  }
  const push = interpolate(f, [0, durationSec * fps], [1, 1.09], {easing: ease});
  const last = n - 1;
  const hlStart = lands[last] + Math.round(0.35 * fps);
  const sweep = interpolate(f, [hlStart, hlStart + Math.round(0.5 * fps)], [0, 1], {extrapolateLeft: 'clamp', extrapolateRight: 'clamp', easing: ease});
  const accent = style.palette.accent;
  return (
    <AbsoluteFill style={{background: '#5b3f28', overflow: 'hidden'}}>
      <AbsoluteFill style={{transform: `translate(${shake * 0.6}px, ${shake}px) scale(${push})`}}>
        <AbsoluteFill style={{background: 'repeating-linear-gradient(91deg, #6e4b2f 0 40px, #654429 40px 75px, #74503a 75px 118px)'}} />
        <AbsoluteFill style={{backgroundImage: `url(${staticFile('paper-noise.png')})`, backgroundSize: '512px 512px', mixBlendMode: 'multiply',
          opacity: 0.55, backgroundPosition: boil(f)}} />
        {items.map((it, i) => {
          const k = spring({frame: f - lands[i], fps, config: {damping: 16, stiffness: 260, mass: 0.7}});
          if (f < lands[i]) return null;
          const r = (random(`hr${i}`) - 0.5) * 14;
          const x = 960 + (random(`hx${i}`) - 0.5) * (i === last ? 120 : 760);
          const y = 540 + (random(`hy${i}`) - 0.5) * (i === last ? 60 : 520);
          const isLast = i === last;
          const t = it.title;
          const at = isLast && highlight ? t.indexOf(highlight) : -1;
          const [a, h, b] = at < 0 ? [t, '', ''] : [t.slice(0, at), highlight as string, t.slice(at + (highlight as string).length)];
          const dim = isLast ? 1 : interpolate(f, [lands[last], lands[last] + 8], [1, 0.72], {extrapolateLeft: 'clamp', extrapolateRight: 'clamp'});
          return (
            <div key={i} style={{position: 'absolute', left: x, top: y, width: isLast ? 1180 : 860,
              transform: `translate(-50%, -50%) rotate(${r * (isLast ? 0.4 : 1)}deg) scale(${1.35 - 0.35 * k})`, opacity: Math.min(1, k * 2.5),
              filter: `drop-shadow(0 ${30 - 18 * k}px ${40 - 22 * k}px rgba(0,0,0,.45)) brightness(${dim})`}}>
              <div style={{background: '#F3EEE2', clipPath: TORN, padding: isLast ? '46px 64px 54px' : '34px 48px 40px', direction: 'rtl'}}>
                {it.outlet && (
                  <div style={{fontFamily: 'Playfair Display, DM Serif Display', fontWeight: 900, fontSize: isLast ? 34 : 26, letterSpacing: 6,
                    direction: 'ltr', textAlign: 'center', borderBottom: '3px double #1d1d1d', paddingBottom: 8, marginBottom: 16, color: '#1d1d1d',
                    textTransform: 'uppercase'}}>{it.outlet}</div>
                )}
                <div style={{fontFamily: 'Amiri', fontWeight: 700, fontSize: isLast ? 76 : 56, lineHeight: 1.3, color: '#151515', textAlign: 'center'}}>
                  {a}
                  {h && <span style={{backgroundImage: `linear-gradient(${accent}, ${accent})`, backgroundRepeat: 'no-repeat',
                    backgroundPosition: 'right 85%', backgroundSize: `${sweep * 100}% 45%`}}>{h}</span>}
                  {b}
                </div>
              </div>
            </div>
          );
        })}
      </AbsoluteFill>
      <AbsoluteFill style={{background: 'radial-gradient(ellipse at 50% 45%, transparent 55%, rgba(0,0,0,.5) 100%)'}} />
    </AbsoluteFill>
  );
};

const Person: React.FC<{color: string; size: number}> = ({color, size}) => (
  <svg width={size} height={size * 1.3} viewBox="0 0 20 26">
    <circle cx={10} cy={5.5} r={4.5} fill={color} />
    <path d="M2 26 V16 a8 8 0 0 1 16 0 V26 Z" fill={color} />
  </svg>
);

/** `total` icons (≤ 200), `highlight` of them light up; `label` explains the share. */
export const UnitChart: React.FC<BaseProps & {total?: number; highlight: number; label?: string}> = ({style, durationSec, total = 100, highlight, label = ''}) => {
  useFonts();
  const f = useCurrentFrame();
  const {fps} = useVideoConfig();
  const n = Math.max(1, Math.min(200, Math.round(total)));
  const hi = Math.max(0, Math.min(n, Math.round(highlight)));
  const cols = n <= 10 ? n : n <= 50 ? 10 : 20;
  const rows = Math.ceil(n / cols);
  const size = Math.min(1050 / cols, 760 / (rows * 1.3)) * 0.82;
  const lightStart = Math.round(1.0 * fps);
  const lightLen = Math.round(Math.min(1.2, durationSec * 0.3) * fps);
  const lit = Math.floor(interpolate(f, [lightStart, lightStart + lightLen], [0, hi], {extrapolateLeft: 'clamp', extrapolateRight: 'clamp', easing: ease}));
  const ink = style.palette.ink, accent = (style.palette as Record<string, string>).red ?? style.palette.accent;
  return (
    <AbsoluteFill style={{background: style.palette.paper, direction: 'rtl', overflow: 'hidden'}}>
      <AbsoluteFill style={{backgroundImage: `url(${staticFile('paper-noise.png')})`, backgroundSize: '512px 512px', mixBlendMode: 'multiply',
        opacity: 0.35, backgroundPosition: boil(f)}} />
      <div style={{position: 'absolute', left: 110, top: 540, transform: 'translateY(-50%)', display: 'grid',
        gridTemplateColumns: `repeat(${cols}, ${size}px)`, gap: size * 0.2, direction: 'ltr'}}>
        {Array.from({length: n}, (_, i) => {
          const r = Math.floor(i / cols), c = i % cols;
          const pop = spring({frame: f - Math.round((r + c) * 0.9), fps, config: {damping: 14, stiffness: 200}});
          const on = i < lit;
          const bump = on ? 1 + 0.25 * Math.max(0, 1 - (f - (lightStart + (i / Math.max(1, hi)) * lightLen)) / 6) : 1;
          return <div key={i} style={{transform: `scale(${pop * bump})`, opacity: pop}}><Person color={on ? accent : `${ink}38`} size={size} /></div>;
        })}
      </div>
      <div style={{position: 'absolute', right: 90, top: 540, transform: 'translateY(-50%)', width: 640, textAlign: 'right'}}>
        <div style={{fontFamily: 'DM Serif Display', fontSize: 230, lineHeight: 1, color: accent, direction: 'ltr', textAlign: 'right',
          opacity: appear(f, lightStart - 6, 8)}}>
          {formatNumber(lit)}<span style={{fontSize: 90, color: ink}}> / {formatNumber(n)}</span>
        </div>
        {label && <div style={{fontFamily: style.fonts.title, fontWeight: 900, fontSize: 70, lineHeight: 1.3, color: ink, marginTop: 24,
          opacity: appear(f, lightStart + lightLen - 4, 10)}}>{label}</div>}
      </div>
    </AbsoluteFill>
  );
};
