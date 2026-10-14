import type {ReactElement} from 'react';
import {Video} from '@remotion/media';
import {AbsoluteFill, Sequence, staticFile, useCurrentFrame} from 'remotion';
import type {Storyboard, StoryboardBeat} from '../../core/src/schema';
import type {SrtCue} from '../../core/src/types';
import {EditorialPresenterVideo} from './EditorialPresenterVideo';

const clamp = (n: number) => Math.max(0, Math.min(1, n));
const ease = (n: number) => {const t = clamp(n); return t * t * (3 - 2 * t);};
const textWeight = (text: string) => Array.from(text).reduce((n, char) => n + ((char.codePointAt(0) ?? 0) > 0xffff ? 2 : char.charCodeAt(0) > 255 ? 1 : .6), 0);
export const liteFlowFontSize = (text: string, count: number) => {
  const width = (1920 * .84 - 24 * (count - 1)) / count - 60;
  return Math.max(24, Math.min(40, Math.floor(Math.sqrt(width * 220 / Math.max(1, textWeight(text) * 1.5)))));
};
const activeAt = (s: Storyboard, f: number) => s.beats.find((b) => f >= Math.round(b.start * s.fps) && f < Math.round(b.end * s.fps));

export const liteCameraScale = (s: Storyboard, frame: number): number => {
  const b = activeAt(s, frame);
  if (!s.liteCamera || !b || b.liteLayout !== 'card') return 1;
  const duration = Math.round(b.end * s.fps) - Math.round(b.start * s.fps);
  if (duration < s.fps * 1.2) return 1;
  const local = frame - Math.round(b.start * s.fps);
  const ramp = Math.min(s.fps * .4, (duration - 1) / 3);
  return 1 + .06 * Math.min(ease(local / ramp), ease((duration - 1 - local) / ramp));
};

const palette = (paper: boolean) => paper
  ? {bg: '#F3F1FA', panel: '#FFFFFF', ink: '#201D32', muted: '#615974', accent: '#6342C7', line: '#D5CEE5'}
  : {bg: '#111827', panel: '#12182B', ink: '#F6F7FF', muted: '#B6BED5', accent: '#91BCFF', line: '#2D3652'};

export const LiteBeat = ({beat, fps, paper}: {beat: StoryboardBeat; fps: number; paper: boolean}): ReactElement => {
  const frame = useCurrentFrame(); const c = palette(paper);
  const duration = Math.round(beat.end * fps) - Math.round(beat.start * fps);
  const opacity = Math.min(ease(frame / (fps * .2)), ease((duration - 1 - frame) / (fps * .15)));
  const title = beat.content.structure === 'thesis-and-proof' ? beat.content.thesis : beat.text;
  const font = 'Arial,"Microsoft YaHei","Noto Sans SC",system-ui,sans-serif';
  if (beat.liteLayout === 'card') return <div data-lite-layout="card" style={{position: 'absolute',
    left: beat.placement === 'left' ? '5%' : '68%', top: '24%', width: '27%', padding: '30px 28px',
    boxSizing: 'border-box', background: c.panel, border: `1px solid ${c.line}`, borderRadius: 14,
    color: c.ink, fontFamily: font, opacity, transform: `translateY(${(1 - opacity) * 12}px)`}}>
    <div style={{fontSize: 18, color: c.accent, marginBottom: 20}}>{String(Number(beat.id.match(/\d+$/)?.[0] ?? 1)).padStart(2, '0')}</div>
    <div style={{fontSize: 48, fontWeight: 800, lineHeight: 1.4, overflowWrap: 'anywhere', textWrap: 'balance'}}>{title}</div>
  </div>;
  return <AbsoluteFill data-lite-layout={beat.liteLayout} style={{background: c.bg, color: c.ink, fontFamily: font}}>
    <div style={{position: 'absolute', left: '8%', right: '8%', top: beat.liteLayout === 'title' ? '30%' : '16%', opacity}}>
      <div style={{fontSize: beat.liteLayout === 'title' ? 88 : 58, fontWeight: 900, lineHeight: 1.4, overflowWrap: 'anywhere'}}>{title}</div>
      <div style={{width: 120, height: 4, background: c.accent, marginTop: 28}}/>
    </div>
    {beat.liteLayout === 'flow' ? <div style={{position: 'absolute', left: '8%', right: '8%', top: '40%', display: 'flex', gap: 24}}>
      {(beat.liteItems ?? []).map((text, index) => <div key={index} style={{flex: 1, minWidth: 0, padding: 30,
        border: `1px solid ${c.line}`, borderRadius: 14, background: c.panel,
        opacity: Math.min(opacity, ease((frame - index * fps * .08) / (fps * .25)))}}>
        <div style={{fontSize: 20, color: c.accent, marginBottom: 22}}>0{index + 1}</div>
        <div style={{fontSize: liteFlowFontSize(text, (beat.liteItems ?? []).length), lineHeight: 1.5, overflowWrap: 'anywhere'}}>{text}</div>
      </div>)}
    </div> : null}
  </AbsoluteFill>;
};

export const PublicLiteVideo = ({storyboard: s, cues, overlayOnly}: {storyboard: Storyboard; cues: SrtCue[]; overlayOnly: boolean}): ReactElement => {
  const frame = useCurrentFrame(); const c = palette(s.publicStyle === 'paper'); const active = activeAt(s, frame);
  if (s.litePresenter && !overlayOnly) return <EditorialPresenterVideo storyboard={s} cues={cues}/>;
  if (s.litePresenter && overlayOnly) throw new Error('Presenter layout requires composite output');
  if (s.beats.some((beat) => beat.liteDirection?.doodle)) throw new Error('Semantic doodles require single-presenter composition');
  if (overlayOnly && s.liteCamera) throw new Error('Source camera motion requires composite output');
  const redrawBurned = !overlayOnly && s.captionsMode === 'burned-in' && (s.liteCamera || active?.liteLayout === 'title' || active?.liteLayout === 'flow');
  if (redrawBurned && !cues.length) throw new Error('Public-lite composite requires SRT cues to preserve covered burned-in subtitles');
  const cue = cues.find((q) => q.start <= frame / s.fps && q.end > frame / s.fps);
  return <AbsoluteFill style={{width: 1920, height: 1080, right: 'auto', bottom: 'auto',
    transform: `scale(${s.width / 1920})`, transformOrigin: '0 0',
    background: overlayOnly ? 'transparent' : c.bg, overflow: 'hidden'}}>
    {!overlayOnly ? <AbsoluteFill style={{clipPath: s.liteCamera && s.captionsMode === 'burned-in' ? 'inset(0 0 18% 0)' : undefined}}>
      <Video src={staticFile(s.source.video)} objectFit="cover" disallowFallbackToOffthreadVideo
        style={{width: '100%', height: '100%', transform: `scale(${liteCameraScale(s, frame)})`, transformOrigin: '50% 38%'}}/>
    </AbsoluteFill> : null}
    {s.beats.map((b) => <Sequence key={b.id} from={Math.round(b.start * s.fps)} durationInFrames={Math.max(1, Math.round(b.end * s.fps) - Math.round(b.start * s.fps))}>
      <LiteBeat beat={b} fps={s.fps} paper={s.publicStyle === 'paper'}/>
    </Sequence>)}
    {redrawBurned ? <div style={{position: 'absolute', left: 0, right: 0, bottom: 0, height: '18%', background: c.bg}}/> : null}
    {(s.captionsMode === 'generated' || redrawBurned) && cue ? <div style={{position: 'absolute', left: '8%', right: '8%', bottom: 32,
      textAlign: 'center', color: c.ink, font: '700 38px/1.35 "Microsoft YaHei","Noto Sans SC",system-ui,sans-serif'}}>
      <span style={{display: 'inline-block', maxWidth: '100%', padding: '12px 22px', background: c.panel, borderRadius: 10, overflowWrap: 'anywhere'}}>{cue.text}</span>
    </div> : null}
  </AbsoluteFill>;
};
