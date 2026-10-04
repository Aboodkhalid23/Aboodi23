/** Picture treatments from style update 1 (the owner's reference folder, editor/styles/updates/2026-10-04-drive-refs.md):
 * the investigation desk (style أ), the black-and-white halftone cut-out over a giant year or word (ب + ج),
 * and the archive photo whose people turn into white silhouettes and come back one by one (و). */
import React from 'react';
import {AbsoluteFill, Img, interpolate, random, spring, staticFile} from 'remotion';
import {appear, ease, StyleProps, useFonts} from '../style';

export type Inner = {style: StyleProps; src: string; caption: string; f: number; fps: number; dur: number; fg?: string;
  title?: string; titleY?: number; titleFront?: boolean; parts?: string[]; face?: number[] | null};

const FOCUS = '50% 22%';
const YELLOW = '#F2C230';
const pal = (s: StyleProps) => s.palette as Record<string, string>;
const isArabic = (t: string) => /[؀-ۿ]/.test(t);

/** Soft shadow of a window falling across the scene (reference: light through panes on the paper). */
export const WindowLight: React.FC<{opacity?: number; drift?: number}> = ({opacity = 0.32, drift = 0}) => (
  <svg style={{position: 'absolute', inset: 0, pointerEvents: 'none', mixBlendMode: 'multiply'}} width={1920} height={1080}>
    <defs>
      <filter id="wl-blur"><feGaussianBlur stdDeviation={22} /></filter>
      <mask id="wl-mask">
        <rect width={1920} height={1080} fill="white" />
        <g filter="url(#wl-blur)" transform={`translate(${620 + drift} -60) rotate(-14) skewX(-16)`}>
          {[0, 1].map((r) => [0, 1, 2].map((c) => (
            <rect key={`${r}${c}`} x={c * 330} y={r * 470} width={300} height={440} fill="black" />
          )))}
        </g>
      </mask>
    </defs>
    <rect width={1920} height={1080} fill={`rgba(40,22,6,${opacity})`} mask="url(#wl-mask)" />
  </svg>
);

/** Style ب + ج: cream paper, a giant year / word behind, an accent disc, and the person cut out in black and white
 * with printing dots and a yellow paper edge, standing in front of it. Without a cut-out: the photo in the disc. */
export const HalftoneCutout: React.FC<Inner> = ({style, src, fg, title, caption, f, fps, dur, face}) => {
  useFonts();
  const word = title || caption;
  const big = spring({frame: f, fps, config: {damping: 18, stiffness: 80}});
  const disc = spring({frame: f - Math.round(0.15 * fps), fps, config: {damping: 13, stiffness: 120}});
  const rise = spring({frame: f - Math.round(0.3 * fps), fps, config: {damping: 16, stiffness: 100}});
  const push = interpolate(f, [0, dur * fps], [1, 1.05], {easing: ease});
  const accent = style.palette.accent || YELLOW;
  const digits = /^[\d٠-٩,.$%+\-\s]+$/.test(word);
  const size = Math.min(digits ? 620 : 420, 3000 / Math.max(3, word.length));
  // disc behind head and shoulders (face found in Python), else the middle
  // a close-up would hide the word: the person shrinks towards the bottom middle (face ≈ 32% of the height at most)
  const k = face ? Math.max(0.5, Math.min(1, 0.32 / face[3])) : 1;
  const fx = face ? 960 + (face[0] * 1920 - 960) * k : 960, fy = face ? 1080 - (1080 - face[1] * 1080) * k : 540;
  const fh = face ? face[3] * 1080 * k : 0;
  const D = face ? Math.min(900, Math.max(560, fh * 2.3)) : 640;
  const cx = fx, cy = face ? Math.min(760, fy + fh * 0.45) : 570;
  // a year may hide behind him (the look of the references); a word must be read: above the head when it fits
  const wordY = digits || !face ? 475 : Math.max(size * 0.5, Math.min(475, fy - fh * 0.75 - size * 0.45));
  const bw: React.CSSProperties = {position: 'absolute', inset: 0, width: '100%', height: '100%', objectFit: 'cover', objectPosition: FOCUS};
  return (
    <AbsoluteFill style={{background: '#EFE8D8', overflow: 'hidden'}}>
      <AbsoluteFill style={{backgroundImage: `url(${staticFile('paper-noise.png')})`, backgroundSize: '512px 512px', mixBlendMode: 'multiply', opacity: 0.45}} />
      <AbsoluteFill style={{backgroundImage: 'radial-gradient(rgba(0,0,0,.09) 30%, transparent 33%)', backgroundSize: '14px 14px'}} />
      <AbsoluteFill style={{alignItems: 'center', justifyContent: 'center', transform: `scale(${push})`}}>
        <div style={{position: 'absolute', top: wordY, left: 0, right: 0, textAlign: 'center', transform: `translateY(-50%) scale(${0.9 + 0.1 * big})`,
          opacity: big, fontFamily: digits ? 'DM Serif Display' : 'Blaka, Lalezar', fontSize: size, lineHeight: 1, color: '#151515',
          letterSpacing: digits ? -8 : 0, direction: isArabic(word) ? 'rtl' : 'ltr', whiteSpace: 'nowrap'}}>{word}</div>
        <div style={{position: 'absolute', width: D, height: D, left: cx - D / 2, top: cy - D / 2, borderRadius: '50%', background: accent,
          transform: `scale(${disc})`, mixBlendMode: 'multiply'}} />
        {fg ? (   /* printed in Python (masks.halftone_cutout): B&W, dots, accent paper edge */
          <Img src={staticFile(fg)} style={{...bw, transform: `translateY(${(1 - rise) * 140}px) scale(${k})`, transformOrigin: '50% 100%', opacity: rise,
            filter: 'drop-shadow(0 18px 24px rgba(0,0,0,.35))'}} />
        ) : (
          <div style={{position: 'absolute', width: 600, height: 600, left: 660, top: 270, borderRadius: '50%', overflow: 'hidden',
            transform: `scale(${disc})`, boxShadow: '0 24px 40px rgba(0,0,0,.3)'}}>
            <Img src={staticFile(src)} style={{...bw, filter: 'grayscale(1) contrast(1.4)'}} />
          </div>
        )}
      </AbsoluteFill>
      {title && caption && title !== caption && (
        <div style={{position: 'absolute', bottom: 70, right: 110, background: '#151515', color: '#F5F0E4', padding: '10px 26px',
          fontFamily: 'Alexandria', fontWeight: 700, fontSize: 46, direction: 'rtl', opacity: appear(f, Math.round(0.7 * fps), 10)}}>{caption}</div>
      )}
    </AbsoluteFill>
  );
};

const Paperclip: React.FC<{x: number; y: number; r: number}> = ({x, y, r}) => (
  <svg style={{position: 'absolute', left: x, top: y, transform: `rotate(${r}deg)`, filter: 'drop-shadow(2px 4px 3px rgba(0,0,0,.35))'}}
    width={60} height={150} viewBox="0 0 60 150">
    <path d="M18 120 V30 a12 12 0 0 1 24 0 V125 a18 18 0 0 1 -36 0 V20 a24 24 0 0 1 48 0 V110" fill="none" stroke="#9aa3ad" strokeWidth={6}
      strokeLinecap="round" />
  </svg>
);

/** Style أ, the investigation desk seen from above: the picture as a print taped down with yellow tape, a sticky note
 * with the caption in handwriting, a red stamp (the beat's `title`), a pen, a paper clip, red string to the note,
 * window light across it all, and the camera sliding slowly over the desk. */
export const Desk: React.FC<Inner> = ({style, src, caption, title, f, fps, dur}) => {
  useFonts();
  const t = interpolate(f, [0, dur * fps], [0, 1], {easing: ease});
  const photo = spring({frame: f, fps, config: {damping: 15, stiffness: 110}});
  const note = spring({frame: f - Math.round(0.45 * fps), fps, config: {damping: 12, stiffness: 140}});
  const stamp = spring({frame: f - Math.round(0.9 * fps), fps, config: {damping: 9, stiffness: 220}});
  const string = appear(f, Math.round(0.7 * fps), Math.round(0.4 * fps));
  const red = pal(style).red ?? '#C4382E';
  const tape = (x: number, y: number, r: number) => (
    <div style={{position: 'absolute', left: x, top: y, width: 190, height: 52, background: 'rgba(242,194,48,.85)',
      transform: `rotate(${r}deg)`, boxShadow: '0 2px 4px rgba(0,0,0,.18)',
      clipPath: 'polygon(0 6%, 4% 0, 96% 4%, 100% 0, 98% 50%, 100% 100%, 3% 96%, 0 100%, 2% 50%)'}} />
  );
  return (
    <AbsoluteFill style={{background: '#6b4a2f', overflow: 'hidden'}}>
      <AbsoluteFill style={{transform: `translate(${-50 + 90 * t}px, ${-20 + 30 * t}px) scale(${1.08 - 0.03 * t}) rotate(${-1 + t}deg)`}}>
        {/* wood */}
        <AbsoluteFill style={{background: 'repeating-linear-gradient(92deg, #7a5536 0 34px, #6e4b2f 34px 61px, #82593a 61px 97px, #6a472c 97px 130px)'}} />
        <AbsoluteFill style={{backgroundImage: `url(${staticFile('paper-noise.png')})`, backgroundSize: '512px 512px', mixBlendMode: 'multiply', opacity: 0.6}} />
        {/* the print */}
        <div style={{position: 'absolute', left: 300, top: 120, transform: `rotate(${-4 + photo * 1.5}deg) translateY(${(1 - photo) * -80}px)`,
          opacity: photo, filter: 'drop-shadow(0 22px 26px rgba(0,0,0,.45))'}}>
          <div style={{background: '#F6F1E6', padding: '22px 22px 90px'}}>
            <Img src={staticFile(src)} style={{width: 860, height: 600, objectFit: 'cover', objectPosition: FOCUS, display: 'block',
              filter: 'contrast(1.08) saturate(.8) sepia(.12)'}} />
          </div>
          {tape(-60, -20, -28)}
          {tape(760, -14, 24)}
        </div>
        {/* pen and paper clip */}
        <div style={{position: 'absolute', left: 1380, top: 760, width: 430, height: 26, borderRadius: 13, transform: 'rotate(-32deg)',
          background: 'linear-gradient(#1f2a44, #121a2e 60%, #0b1120)', boxShadow: '6px 10px 10px rgba(0,0,0,.4)'}}>
          <div style={{position: 'absolute', right: -34, top: 5, width: 0, height: 0, borderTop: '8px solid transparent',
            borderBottom: '8px solid transparent', borderLeft: '36px solid #c9b48a'}} />
        </div>
        <Paperclip x={1180} y={95} r={12} />
        {/* sticky note with the caption */}
        {caption && (
          <div style={{position: 'absolute', left: 1240, top: 240, width: 470, minHeight: 400, transform: `rotate(${5 - (1 - note) * 12}deg) scale(${note})`,
            opacity: note, background: 'linear-gradient(170deg, #FFE97A, #F7D84F)', padding: '56px 40px', direction: 'rtl', display: 'flex',
            alignItems: 'center', justifyContent: 'center', textAlign: 'center', fontFamily: 'Alkalami', fontSize: caption.length > 18 ? 58 : 76,
            lineHeight: 1.35, color: '#1f1f1f', boxShadow: '0 18px 24px rgba(0,0,0,.35)'}}>{caption}</div>
        )}
        {/* red string from the photo's pin to the note's pin */}
        <svg style={{position: 'absolute', inset: 0}} width={1920} height={1080}>
          <path d={`M 1160 180 Q ${1160 + 150 * string} ${230 + 40 * string} ${1160 + 320 * string} ${260 + 20 * string}`} stroke={red}
            strokeWidth={5} fill="none" />
          <circle cx={1160} cy={180} r={15} fill={red} />
          {note > 0.5 && <circle cx={1480} cy={262} r={15} fill={red} />}
        </svg>
        {/* stamp */}
        {title && (
          <div style={{position: 'absolute', left: 420, top: 640, transform: `rotate(-12deg) scale(${2.2 - 1.2 * stamp})`, opacity: Math.min(1, stamp * 1.4),
            border: `9px solid ${red}`, borderRadius: 14, padding: '6px 36px', color: red, fontFamily: 'Lalezar', fontSize: 104,
            direction: 'rtl', mixBlendMode: 'multiply', background: 'rgba(255,255,255,.05)'}}>{title}</div>
        )}
      </AbsoluteFill>
      <WindowLight drift={60 * t} />
      <AbsoluteFill style={{background: 'radial-gradient(ellipse at 45% 40%, transparent 50%, rgba(0,0,0,.45) 100%)'}} />
    </AbsoluteFill>
  );
};

/** Style و: everyone in an archive photo turns into a white silhouette, then they come back one by one
 * (right to left), each with a short flash — "who is who". `parts` = one white silhouette PNG per person. */
export const Silhouette: React.FC<Inner> = ({src, parts = [], caption, f, fps, dur}) => {
  useFonts();
  const kb = interpolate(f, [0, dur * fps], [1.02, 1.08]);
  const pic: React.CSSProperties = {position: 'absolute', inset: 0, width: '100%', height: '100%', objectFit: 'cover', objectPosition: FOCUS,
    transform: `scale(${kb})`};
  const first = 0.9, gap = Math.max(0.5, Math.min(1.1, (dur - 1.6) / Math.max(1, parts.length)));
  return (
    <AbsoluteFill style={{background: '#000', overflow: 'hidden'}}>
      <Img src={staticFile(src)} style={{...pic, filter: 'grayscale(1) contrast(1.15) brightness(.9)'}} />
      {parts.map((p, k) => {
        const at = Math.round((first + k * gap) * fps);
        const gone = interpolate(f, [at, at + 6], [1, 0], {extrapolateLeft: 'clamp', extrapolateRight: 'clamp'});
        const flash = interpolate(f, [at, at + 3, at + 9], [0, 1, 0], {extrapolateLeft: 'clamp', extrapolateRight: 'clamp'});
        const wob = (random(`sil${k}`) - 0.5) * 2;
        return (
          <React.Fragment key={p}>
            <Img src={staticFile(p)} style={{...pic, opacity: gone, filter: `drop-shadow(0 0 ${6 + wob}px rgba(255,255,255,.6))`}} />
            <Img src={staticFile(p)} style={{...pic, opacity: flash * 0.8, filter: 'blur(6px)'}} />
          </React.Fragment>
        );
      })}
      <AbsoluteFill style={{background: 'radial-gradient(ellipse at center, transparent 55%, rgba(0,0,0,.55) 100%)'}} />
      {caption && (
        <div style={{position: 'absolute', bottom: 80, left: 0, right: 0, textAlign: 'center', direction: 'rtl', fontFamily: 'Amiri',
          fontStyle: 'italic', fontWeight: 700, fontSize: 64, color: '#fff', opacity: appear(f, 6, 12)}}>
          <span style={{background: 'rgba(242,194,48,.9)', color: '#111', padding: '2px 22px'}}>{caption}</span>
        </div>
      )}
    </AbsoluteFill>
  );
};
