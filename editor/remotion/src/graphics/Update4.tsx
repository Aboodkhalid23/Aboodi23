/** Pieces from the owner's reference reel (update 4, editor/styles/updates/2026-10-05-reel-insult.md):
 *  - KineticType   the sentence lands word by word, each word printing in from pale grey to ink as it is said,
 *                  stacked lines, short words big ("that's / HOW / ONE / insult")
 *  - BandScene     the picture fills the top band, a paper page below where the caption types itself, a
 *                  hand-drawn circle boils around the key word
 *  - RoundedFootage archive film in a rounded frame on black, its line of narration typed in yellow serif
 *  - TypeOn        letters appear one after another (the reel types almost every word it shows) */
import React from 'react';
import {AbsoluteFill, Img, interpolate, OffthreadVideo, spring, staticFile, useCurrentFrame, useVideoConfig} from 'remotion';
import {BaseProps, boil, ease, useFonts} from '../style';
import {ScribbleCircle, useDraw} from './HandDrawn';

const isAr = (t: string) => /[؀-ۿ]/.test(t);

/** `text` typed from `start` (frames) at `cps` characters a second; the caret blinks while typing. */
export const TypeOn: React.FC<{text: string; start: number; cps?: number; style?: React.CSSProperties; caret?: boolean}> = ({text, start, cps = 22, style, caret = false}) => {
  const f = useCurrentFrame();
  const {fps} = useVideoConfig();
  const n = Math.max(0, Math.min(text.length, Math.floor(((f - start) / fps) * cps)));
  const typing = n < text.length && f >= start;
  return (
    <span style={{direction: isAr(text) ? 'rtl' : 'ltr', ...style}}>
      {text.slice(0, n)}
      {caret && typing && Math.floor(f / 8) % 2 === 0 ? <span style={{opacity: 0.7}}>|</span> : null}
    </span>
  );
};

/** Lines for kinetic type: short words share a line, long ones stand alone, at most 4 lines. */
const lines = (words: string[]) => {
  const out: number[][] = [];
  const cap = words.length > 4 ? 13 : 8;
  words.forEach((w, i) => {
    const last = out[out.length - 1];
    const len = last ? last.reduce((s, j) => s + words[j].length + 1, 0) + w.length : 0;
    if (last && (len <= cap || out.length >= 4)) last.push(i);
    else out.push([i]);
  });
  return out;
};

export const KineticType: React.FC<BaseProps & {text: string; times?: number[]; highlight?: string}> = ({style, durationSec, text, times, highlight}) => {
  useFonts();
  const f = useCurrentFrame();
  const {fps} = useVideoConfig();
  const words = text.split(/\s+/).filter(Boolean);
  const at = words.map((_, i) => Math.round(((times && times[i] != null) ? (times[i] as number) : 0.15 + i * Math.min(0.45, (durationSec * 0.7) / words.length)) * fps));
  const ar = isAr(text);
  const push = interpolate(f, [0, durationSec * fps], [1, 1.05], {easing: ease});
  const ink = style.palette.ink;
  return (
    <AbsoluteFill style={{background: '#E9E6E0', overflow: 'hidden'}}>
      <AbsoluteFill style={{backgroundImage: `url(${staticFile('paper-noise.png')})`, backgroundSize: '512px 512px', mixBlendMode: 'multiply',
        opacity: 0.5, backgroundPosition: boil(f)}} />
      <AbsoluteFill style={{alignItems: 'center', justifyContent: 'center', transform: `scale(${push})`}}>
        <div style={{direction: ar ? 'rtl' : 'ltr', textAlign: ar ? 'right' : 'left', lineHeight: 1.0}}>
          {lines(words).map((ln, li) => {
            const len = ln.reduce((s, i) => s + words[i].length, 0);
            const rows = lines(words).length;
            const size = Math.min(300, 880 / rows, Math.max(110, 1500 / Math.max(3, len)));   // fits the frame
            return (
              <div key={li} style={{fontFamily: ar ? 'Alexandria' : 'IBM Plex Mono, Archivo Black', fontWeight: 800, fontSize: size,
                whiteSpace: 'nowrap', marginTop: li ? (ar ? size * 0.12 : -size * 0.08) : 0}}>
                {ln.map((i, k) => {
                  const p = interpolate(f, [at[i], at[i] + 6], [0, 1], {extrapolateLeft: 'clamp', extrapolateRight: 'clamp', easing: ease});
                  const hl = highlight && words[i].includes(highlight);
                  return (
                    <span key={i} style={{opacity: f < at[i] ? 0 : 0.25 + 0.75 * p, color: hl && p > 0.9 ? (style.palette as Record<string, string>).red ?? '#C4382E' : ink,
                      display: 'inline-block', transform: `translateY(${(1 - p) * 18}px)`}}>{words[i]}{k < ln.length - 1 ? ' ' : ''}</span>
                  );
                })}
              </div>
            );
          })}
        </div>
      </AbsoluteFill>
    </AbsoluteFill>
  );
};

/** Inner props shared with ImageCard treatments. */
type Inner = {style: BaseProps['style']; src: string; caption: string; f: number; fps: number; dur: number; title?: string};

export const BandScene: React.FC<Inner> = ({style, src, caption, title, f, fps, dur}) => {
  useFonts();
  const kb = interpolate(f, [0, dur * fps], [1.02, 1.1], {easing: ease});
  const drop = spring({frame: f, fps, config: {damping: 16, stiffness: 120}});
  const word = title || '';
  const [ink, seed] = useDraw(Math.round(0.9 * fps), `band${word}`);
  const ar = isAr(caption);
  return (
    <AbsoluteFill style={{background: '#F4F1EA', overflow: 'hidden'}}>
      <div style={{position: 'absolute', left: 0, right: 0, top: 0, height: '56%', overflow: 'hidden',
        transform: `translateY(${(1 - drop) * -60}px)`, boxShadow: '0 12px 24px rgba(0,0,0,.18)'}}>
        <Img src={staticFile(src)} style={{width: '100%', height: '100%', objectFit: 'cover', objectPosition: '50% 35%', transform: `scale(${kb})`}} />
      </div>
      <AbsoluteFill style={{backgroundImage: `url(${staticFile('paper-noise.png')})`, backgroundSize: '512px 512px', mixBlendMode: 'multiply',
        opacity: 0.35, backgroundPosition: boil(f)}} />
      <div style={{position: 'absolute', left: 120, right: 120, top: '62%', textAlign: 'center', fontFamily: ar ? 'Amiri' : 'DM Serif Display',
        fontStyle: ar ? 'normal' : 'italic', fontWeight: 700, fontSize: 96, color: style.palette.ink, direction: ar ? 'rtl' : 'ltr'}}>
        <TypeOn text={caption} start={Math.round(0.35 * fps)} cps={ar ? 16 : 24} caret />
      </div>
      {word && (
        <div style={{position: 'absolute', left: ar ? '74%' : '26%', top: '16%', transform: 'translate(-50%, -50%)', textAlign: 'center'}}>
          <div style={{fontFamily: ar ? 'Amiri' : 'DM Serif Display', fontStyle: ar ? 'normal' : 'italic', fontWeight: 700, fontSize: 130,
            color: '#141414', textShadow: '0 3px 0 #fff, 0 -3px 0 #fff, 3px 0 0 #fff, -3px 0 0 #fff', opacity: interpolate(f, [0.6 * fps, 0.8 * fps], [0, 1], {extrapolateLeft: 'clamp', extrapolateRight: 'clamp'}),
            direction: ar ? 'rtl' : 'ltr'}}>{word}</div>
          <div style={{position: 'absolute', left: '50%', top: '50%', transform: 'translate(-50%, -50%)'}}>
            <ScribbleCircle w={Math.max(420, word.length * 70)} h={220} color="#F2C230" draw={ink} seed={seed} />
          </div>
        </div>
      )}
    </AbsoluteFill>
  );
};

export const RoundedFootage: React.FC<BaseProps & {src: string; caption?: string}> = ({src, caption = ''}) => {
  useFonts();
  const f = useCurrentFrame();
  const {fps} = useVideoConfig();
  const k = spring({frame: f, fps, config: {damping: 15, stiffness: 140}});
  const ar = isAr(caption);
  return (
    <AbsoluteFill style={{background: '#000', alignItems: 'center', justifyContent: 'center'}}>
      <div style={{width: 1240, height: 930, borderRadius: 56, overflow: 'hidden', position: 'relative', transform: `scale(${0.86 + 0.14 * k})`,
        opacity: k, boxShadow: '0 0 0 3px rgba(255,255,255,.08), 0 30px 80px rgba(0,0,0,.8)'}}>
        <OffthreadVideo src={staticFile(src)} muted style={{width: '100%', height: '100%', objectFit: 'cover', filter: 'grayscale(.85) contrast(1.15)'}} />
        <AbsoluteFill style={{background: 'radial-gradient(ellipse at center, transparent 60%, rgba(0,0,0,.45) 100%)'}} />
        {caption && (
          <div style={{position: 'absolute', left: 60, right: 60, bottom: 70, textAlign: 'center', fontFamily: ar ? 'Amiri' : 'DM Serif Display',
            fontWeight: 700, fontSize: 64, lineHeight: 1.25, color: '#F2C230', textShadow: '0 3px 12px rgba(0,0,0,.9)'}}>
            <TypeOn text={caption} start={Math.round(0.3 * fps)} cps={ar ? 14 : 22} />
          </div>
        )}
      </div>
    </AbsoluteFill>
  );
};
