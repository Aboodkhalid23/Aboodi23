import type {CSSProperties, ReactElement} from 'react';
import {Video} from '@remotion/media';
import {AbsoluteFill, staticFile, useCurrentFrame} from 'remotion';
import type {Storyboard, StoryboardBeat} from '../../core/src/schema';
import type {SrtCue} from '../../core/src/types';
import {SourceDoodle} from './illustrations/SourceDoodle';

type Rect = {x: number; y: number; w: number; h: number; r: number};
type Mode = NonNullable<StoryboardBeat['liteDirection']>['mode'];
const clamp = (n: number) => Math.max(0, Math.min(1, n));
const smooth = (n: number) => {const t = clamp(n); return t * t * (3 - 2 * t);};
const out = (n: number) => 1 - (1 - clamp(n)) ** 4;
const full: Rect = {x: 0, y: 0, w: 1920, h: 886, r: 0};
const rectFor = (mode: Mode): Rect => mode === 'hero' ? {x: 96, y: 156, w: 760, h: 704, r: 24}
  : mode === 'split' ? {x: 1032, y: 156, w: 792, h: 704, r: 24}
  : mode === 'process' ? {x: 1256, y: 240, w: 568, h: 620, r: 24} : full;
export const presenterMode = (beat: StoryboardBeat, index: number, count: number): Mode =>
  beat.liteDirection?.mode ?? (index === 0 ? 'hero' : index === count - 1 ? 'closing' : beat.liteLayout === 'flow' ? 'process' : index % 2 ? 'focus' : 'split');

/** One continuously mounted media element; rectangle changes never restart its clock. */
export const presenterRectAt = (s: Storyboard, frame: number): Rect => {
  let index = s.beats.findIndex((b) => frame >= Math.round(b.start * s.fps) && frame < Math.round(b.end * s.fps));
  if (index < 0) index = s.beats.length - 1;
  const beat = s.beats[index]; const mode = presenterMode(beat, index, s.beats.length);
  const before = index ? rectFor(presenterMode(s.beats[index - 1], index - 1, s.beats.length)) : full;
  const target = rectFor(mode);
  const transitionFrames = Math.min(s.fps * .45, (beat.end - beat.start) * s.fps * .28);
  const k = smooth((frame - Math.round(beat.start * s.fps)) / Math.max(1, transitionFrames));
  return {x: before.x + (target.x - before.x) * k, y: before.y + (target.y - before.y) * k,
    w: before.w + (target.w - before.w) * k, h: before.h + (target.h - before.h) * k,
    r: before.r + (target.r - before.r) * k};
};
const weight = (text: string) => Array.from(text).reduce((n, char) => n + (char.charCodeAt(0) > 255 ? 1 : .58), 0);
const fontSize = (text: string, width: number, maximum: number) => Math.max(20, Math.min(maximum, Math.floor(width / Math.max(1, weight(text)))));
const font = '"Microsoft YaHei","Noto Sans SC",Arial,system-ui,sans-serif';

export const editorialPalette = (paper: boolean) => paper
  ? {bg: '#F3F1FA', panel: '#FFFFFF', ink: '#201D32', muted: '#615974', main: '#6342C7', sub: '#007477', result: '#A9431E', line: '#D5CEE5'}
  : {bg: '#080B16', panel: '#151A2D', ink: '#F6F7FF', muted: '#ADB6CF', main: '#C3ADFF', sub: '#73E4F0', result: '#FFC799', line: '#2B344E'};

const Emphasis = ({lines, highlight, width, size, local, fps, color, ink}: {
  lines: string[]; highlight: number; width: number; size: number; local: number; fps: number; color: string; ink: string;
}) => <div style={{width}}>{lines.map((text, index) => {
  const k = out((local - fps * (.28 + index * .11)) / (fps * .38));
  const marker = smooth((local - fps * (.54 + index * .11)) / (fps * .28));
  return <div key={index} style={{overflow: 'hidden', paddingBottom: 12}}>
    <div style={{fontSize: fontSize(text, width, size), fontWeight: 900, lineHeight: 1.2, letterSpacing: '-.035em',
      color: index === highlight ? color : ink, whiteSpace: 'nowrap', transform: `translateY(${(1 - k) * 108}%)`}}>
      <span style={{position: 'relative', display: 'inline-block'}}>{index === highlight ? <span style={{position: 'absolute', left: -4, right: -4, bottom: '3%', height: '13%',
        background: `${color}25`, transform: `scaleX(${marker})`, transformOrigin: 'left', borderRadius: 3}}/> : null}<span style={{position: 'relative'}}>{text}</span></span>
    </div>
  </div>;
})}</div>;

export const EditorialPresenterVideo = ({storyboard: s, cues}: {storyboard: Storyboard; cues: SrtCue[]}): ReactElement => {
  const frame = useCurrentFrame();
  if (s.captionsMode !== 'none' && !cues.length) throw new Error('Presenter layouts require matching SRT captions');
  let index = s.beats.findIndex((b) => frame >= Math.round(b.start * s.fps) && frame < Math.round(b.end * s.fps));
  if (index < 0) index = s.beats.length - 1;
  const beat = s.beats[index]; const mode = presenterMode(beat, index, s.beats.length);
  const local = frame - Math.round(beat.start * s.fps);
  const duration = Math.round((beat.end - beat.start) * s.fps);
  const leave = index === s.beats.length - 1 ? 1 : smooth((duration - local) / (s.fps * .16));
  const ready = out((local - s.fps * .22) / (s.fps * .28)) * leave;
  const paper = s.publicStyle === 'paper';
  const c = editorialPalette(paper);
  const rect = presenterRectAt(s, frame);
  const focus = mode === 'focus' && s.liteCamera ? .06 * Math.min(smooth(local / (s.fps * .4)), smooth((duration - 1 - local) / (s.fps * .4))) : 0;
  const sourceScale = Math.max(rect.w / 1920, rect.h / 886) * (1 + focus);
  const videoWidth = 1920 * sourceScale; const videoHeight = 1080 * sourceScale;
  const direction = beat.liteDirection;
  const doodle = direction?.doodle;
  const emphasisColor = mode === 'closing' || mode === 'process' ? c.result : c.main;
  const drawingColor = doodle?.type === 'agent-output' ? c.result : c.sub;
  const borderDraw = smooth((local - s.fps * .08) / (s.fps * .65));
  const lines = direction?.lines ?? (beat.liteLayout === 'flow' ? (beat.liteItems ?? []).map((text) => Array.from(text).slice(0, 24).join('')) : [beat.content.structure === 'thesis-and-proof' ? beat.content.thesis : beat.text]);
  const label = direction?.eyebrow ?? '';
  const cue = cues.find((q) => q.start <= frame / s.fps && q.end > frame / s.fps);
  const textStyle: CSSProperties = {position: 'absolute', opacity: ready, zIndex: 3};
  const x = mode === 'hero' ? 984 : 120;
  const width = mode === 'hero' ? 820 : mode === 'focus' || mode === 'closing' ? 500 : 820;
  return <AbsoluteFill style={{width: 1920, height: 1080, right: 'auto', bottom: 'auto', transform: `scale(${s.width / 1920})`,
    transformOrigin: '0 0', background: c.bg, overflow: 'hidden', fontFamily: font, color: c.ink}}>
    <AbsoluteFill style={{background: `radial-gradient(ellipse at ${75 + Math.sin(frame / 150) * 5}% 20%, ${c.main}20, transparent 58%), radial-gradient(ellipse at 15% 82%, ${c.sub}12, transparent 60%), radial-gradient(ellipse at 92% 82%, ${c.result}0D, transparent 46%)`}}/>
    <svg width="1920" height="886" style={{position: 'absolute', left: 0, top: 0}} aria-hidden>
      {Array.from({length: 13}, (_, i) => <line key={i} x1={i * 160} x2={i * 160} y1="0" y2="886" stroke={c.line} opacity=".3"/>)}
      <path d="M96 660 Q840 110 1824 240" fill="none" stroke={c.main} strokeWidth="1" opacity=".18"/>
      <path d="M96 790 Q1180 420 1824 770" fill="none" stroke={c.sub} strokeWidth="1" opacity=".16"/>
    </svg>
    <div style={{position: 'absolute', left: rect.x, top: rect.y, width: rect.w, height: rect.h, borderRadius: rect.r,
      overflow: 'hidden', zIndex: 2, boxShadow: rect.r ? '0 32px 80px #00000050' : undefined,
      outline: rect.r ? `1px solid ${c.line}` : undefined}}>
      <Video src={staticFile(s.source.video)} disallowFallbackToOffthreadVideo
        style={{position: 'absolute', width: videoWidth, height: videoHeight,
          left: (rect.w - videoWidth) / 2, top: -focus * 250, maxWidth: 'none'}}/>
      <svg width="100%" height="100%" viewBox={`0 0 ${rect.w} ${rect.h}`} style={{position: 'absolute', inset: 0, pointerEvents: 'none', opacity: rect.r / 24 * .65}} aria-hidden>
        <defs><linearGradient id="presenter-border" x1="0%" y1="0%" x2="100%" y2="100%"><stop stopColor={c.main}/><stop offset="1" stopColor={c.sub}/></linearGradient></defs>
        <rect x="1.5" y="1.5" width={rect.w - 3} height={rect.h - 3} rx={Math.max(0, rect.r - 1)} fill="none" stroke="url(#presenter-border)" strokeWidth="2.5" pathLength="1"
          strokeDasharray="1" strokeDashoffset={1 - borderDraw}/>
      </svg>
    </div>
    <div style={{position: 'absolute', left: 96, right: 96, top: 58, display: 'flex', justifyContent: 'space-between',
      fontSize: 20, letterSpacing: '.12em', color: c.muted, zIndex: 4, opacity: ready,
      textShadow: mode === 'focus' || mode === 'closing' ? '0 2px 10px #000' : undefined}}>
      <span style={{color: c.ink, background: `${c.bg}DB`, padding: '7px 14px', borderRadius: 7, border: `1px solid ${c.line}`}}>{String(index + 1).padStart(2, '0')} / {String(s.beats.length).padStart(2, '0')}</span>
      <span style={{color: c.main}}>{label}</span>
    </div>
    {mode === 'process' ? <div style={{...textStyle, left: 120, top: doodle ? 170 : 226, width: 1000}}>
      <div style={{height: 4, width: 130 * ready, background: c.result, marginBottom: 26}}/>
      {lines.map((text, i) => {
        const k = out((local - s.fps * (.3 + i * .14)) / (s.fps * .36));
        const selected = i === (direction?.highlight ?? lines.length - 1);
        return <div key={i} style={{display: 'flex', alignItems: 'center', gap: 28, border: `1px solid ${c.line}`, borderLeft: `3px solid ${selected ? c.result : c.sub}`,
          borderRadius: 12, marginBottom: 10, background: selected ? `${c.result}12` : `${c.panel}66`,
          padding: '12px 18px', opacity: k, transform: `translateX(${(1 - k) * -40}px)`}}>
          <span style={{fontSize: 20, color: selected ? c.result : c.sub, border: `1px solid ${selected ? c.result : c.sub}55`, borderRadius: 7, padding: '8px 10px'}}>0{i + 1}</span>
          <div style={{fontSize: fontSize(text, 780, doodle ? 70 : 96), fontWeight: 900, lineHeight: 1.22, whiteSpace: 'nowrap', color: selected ? c.result : c.ink}}>{text}</div>
        </div>;
      })}
    </div> : <div style={{...textStyle, left: x, top: mode === 'closing' ? (doodle ? 230 : 640) : mode === 'focus' ? 230 : doodle ? 190 : 285,
      ...(mode === 'focus' || mode === 'closing' ? {background: `${c.bg}ED`, padding: 30, borderLeft: `4px solid ${emphasisColor}`, borderRadius: '0 16px 16px 0'} : {})}}>
      {label && <div style={{fontSize: 24, color: c.sub, marginBottom: 28, letterSpacing: '.04em'}}>{label}</div>}
      <Emphasis lines={lines} highlight={direction?.highlight ?? lines.length - 1} width={width} size={mode === 'focus' || mode === 'closing' ? 74 : doodle ? 112 : 132}
        local={local} fps={s.fps} color={emphasisColor} ink={c.ink}/>
      <div style={{width: 160 * ready, height: 4, background: `linear-gradient(90deg,${emphasisColor},${c.sub})`, marginTop: 28}}/>
    </div>}
    {doodle ? <div data-source-doodle={doodle.type} style={{position: 'absolute', zIndex: 3,
      left: mode === 'hero' ? 984 : 120, top: 590, width: mode === 'focus' || mode === 'closing' ? 540 : mode === 'process' ? 960 : 820,
      height: 264, opacity: ready, color: c.muted,
      ...(mode === 'focus' || mode === 'closing' ? {background: `${c.bg}F0`, borderRadius: 16, padding: 12, boxSizing: 'border-box'} : {})}}>
      <div style={{height: mode === 'focus' || mode === 'closing' ? 210 : 235}}><SourceDoodle type={doodle.type} progress={out((local - s.fps * .48) / (s.fps * .55))}
        actionProgress={smooth((local - s.fps * .85) / (s.fps * .42))} accent={drawingColor} ink={c.ink}/></div>
      <div style={{fontSize: 18, textAlign: 'center', marginTop: 5}}><span style={{color: drawingColor, border: `1px solid ${drawingColor}44`, padding: '3px 10px', borderRadius: 6,
        background: `${c.bg}CE`}}>{doodle.label} · 简笔画示意</span></div>
    </div> : null}
    <div style={{position: 'absolute', left: 96, right: 96, top: 914, height: 2, background: c.line, zIndex: 4}}>
      <div style={{height: '100%', width: `${clamp(frame / (Math.ceil(s.duration * s.fps) - 1)) * 100}%`, background: c.main}}/>
    </div>
    {s.captionsMode !== 'none' && cue ? <div style={{position: 'absolute', left: '5%', right: '5%', bottom: 25, textAlign: 'center', zIndex: 5}}>
      <span style={{display: 'inline-block', maxWidth: '100%', background: c.panel, color: c.ink, borderRadius: 14,
        padding: '16px 28px', fontSize: fontSize(cue.text, 1670, 46), fontWeight: 700, lineHeight: 1.3}}>{cue.text}</span>
    </div> : null}
  </AbsoluteFill>;
};
