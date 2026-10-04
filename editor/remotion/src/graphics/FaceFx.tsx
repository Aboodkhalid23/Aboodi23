import React from 'react';
import {AbsoluteFill, Img, interpolate, OffthreadVideo, staticFile, useCurrentFrame, useVideoConfig} from 'remotion';
import {ease, StyleProps, useFonts} from '../style';
import {SCENE_SPOTS, Sticker, Stickers} from './Stickers';

type Channel = {name: string; handle?: string; avatar?: string | null};
type Props = {style: StyleProps; durationSec: number; fps?: number; src: string; fx: 'subscribe' | 'tv' | 'none';
  stickers?: Sticker[]; channel: Channel};

const W = 1920, H = 1080;
type Rect = [number, number, number, number];
const lerp = (a: Rect, b: Rect, k: number): Rect => a.map((v, i) => v + (b[i] - v) * k) as Rect;
const FULL: Rect = [0, 0, W, H];
// Timings (seconds). Sounds in compose.py FX_CUES must match: whoosh 0, click 1.6, ding 1.75.
const SHRINK = 0.5, CLICK = 1.6, BELL = 1.75, GROW = 0.45;

const useShrink = (target: Rect) => {
  const f = useCurrentFrame();
  const {fps, durationInFrames} = useVideoConfig();
  const k = interpolate(f, [0, SHRINK * fps], [0, 1], {extrapolateRight: 'clamp', easing: ease});
  const canExit = durationInFrames / fps >= 3;
  const back = canExit ? interpolate(f, [durationInFrames - GROW * fps, durationInFrames - 1], [0, 1],
    {extrapolateLeft: 'clamp', extrapolateRight: 'clamp', easing: ease}) : 0;
  const m = k * (1 - back);
  return {rect: lerp(FULL, target, m), m};
};

const Footage: React.FC<{src: string; rect: Rect; radius: number; shadow?: boolean}> = ({src, rect, radius, shadow}) => (
  <div style={{position: 'absolute', left: rect[0], top: rect[1], width: rect[2], height: rect[3], borderRadius: radius,
    overflow: 'hidden', boxShadow: shadow ? '0 40px 90px rgba(0,0,0,.55)' : undefined}}>
    <OffthreadVideo src={staticFile(src)} muted style={{width: '100%', height: '100%', objectFit: 'cover'}} />
  </div>
);

const Bell: React.FC<{size: number; color: string; angle: number}> = ({size, color, angle}) => (
  <svg width={size} height={size} viewBox="0 0 24 24" style={{transform: `rotate(${angle}deg)`, transformOrigin: '50% 10%'}}>
    <path fill={color} d="M12 22a2.2 2.2 0 0 0 2.2-2.2H9.8A2.2 2.2 0 0 0 12 22Zm7-6V11a7 7 0 0 0-5.5-6.8V3.5a1.5 1.5 0 0 0-3 0v.7A7 7 0 0 0 5 11v5l-2 2v1h18v-1Z" />
  </svg>
);

const Cursor: React.FC<{x: number; y: number; press: number}> = ({x, y, press}) => (
  <svg width={64} height={64} viewBox="0 0 24 24" style={{position: 'absolute', left: x, top: y,
    transform: `scale(${1 - press * 0.15})`, transformOrigin: '10% 10%', filter: 'drop-shadow(0 4px 6px rgba(0,0,0,.5))'}}>
    <path d="M3 2l7.5 19 2.6-7.4L20.5 11Z" fill="#fff" stroke="#111" strokeWidth={1.4} strokeLinejoin="round" />
  </svg>
);

const Subscribe: React.FC<Props> = ({src, channel}) => {
  const f = useCurrentFrame();
  const {fps} = useVideoConfig();
  const target: Rect = [W * 0.19, 70, W * 0.62, H * 0.62];
  const {rect, m} = useShrink(target);
  const bar = interpolate(f, [0.3 * fps, 0.7 * fps], [0, 1], {extrapolateLeft: 'clamp', extrapolateRight: 'clamp', easing: ease}) * Math.min(1, m * 1.5);
  const btn = {x: target[0] + 110, y: target[1] + target[3] + 72};    // button centre (left side: RTL layout)
  const move = interpolate(f, [0.7 * fps, 1.5 * fps], [0, 1], {extrapolateLeft: 'clamp', extrapolateRight: 'clamp', easing: ease});
  const cx = interpolate(move, [0, 1], [W + 80, btn.x]);
  const cy = interpolate(move, [0, 1], [H + 80, btn.y]);
  const press = interpolate(f, [CLICK * fps - 3, CLICK * fps, CLICK * fps + 4], [0, 1, 0], {extrapolateLeft: 'clamp', extrapolateRight: 'clamp'});
  const subscribed = f >= CLICK * fps + 1;
  const ring = f >= BELL * fps ? Math.sin((f - BELL * fps) / fps * 40) * 22 * Math.max(0, 1 - (f - BELL * fps) / (0.7 * fps)) : 0;
  const cursorOut = interpolate(f, [2.2 * fps, 2.6 * fps], [1, 0], {extrapolateLeft: 'clamp', extrapolateRight: 'clamp'});
  return (
    <AbsoluteFill style={{background: '#0F0F0F'}}>
      <AbsoluteFill style={{opacity: m}}>
        {/* blur a quarter-size copy, then scale it up: same look, 16x cheaper to render */}
        <div style={{width: W / 4, height: H / 4, transform: 'scale(4.6) translate(-12px, -7px)', transformOrigin: '0 0', overflow: 'hidden'}}>
          <OffthreadVideo src={staticFile(src)} muted style={{width: '100%', height: '100%', objectFit: 'cover',
            filter: 'blur(12px) brightness(.38) saturate(1.2)'}} />
        </div>
      </AbsoluteFill>
      <Footage src={src} rect={rect} radius={28 * m} shadow />
      <div style={{position: 'absolute', left: target[0], top: target[1] + target[3] + 26, width: target[2], height: 100,
        display: 'flex', direction: 'rtl', alignItems: 'center', gap: 26, opacity: bar, transform: `translateY(${(1 - bar) * 30}px)`}}>
        <div style={{width: 100, height: 100, borderRadius: '50%', overflow: 'hidden', background: '#C4382E', flexShrink: 0,
          display: 'flex', alignItems: 'center', justifyContent: 'center', color: '#fff', fontFamily: 'Cairo', fontWeight: 900, fontSize: 50}}>
          {channel.avatar ? <Img src={staticFile(channel.avatar)} style={{width: '100%', height: '100%', objectFit: 'cover'}} /> : channel.name.slice(0, 1)}
        </div>
        <div style={{display: 'flex', flexDirection: 'column', color: '#F1F1F1'}}>
          <span style={{fontFamily: 'Tajawal', fontWeight: 700, fontSize: 48, lineHeight: 1.2}}>{channel.name}</span>
          {channel.handle && <span style={{fontFamily: 'Inter', fontSize: 32, color: '#AAAAAA', direction: 'ltr', textAlign: 'right'}}>{channel.handle}</span>}
        </div>
        <div style={{flex: 1}} />
        <div style={{display: 'flex', alignItems: 'center', gap: 14, padding: '0 44px', height: 88, borderRadius: 44,
          background: subscribed ? '#272727' : '#F1F1F1', color: subscribed ? '#F1F1F1' : '#0F0F0F',
          fontFamily: 'Tajawal', fontWeight: 700, fontSize: 44, transform: `scale(${1 - press * 0.08})`}}>
          {subscribed && <Bell size={44} color="#F1F1F1" angle={ring} />}
          {subscribed ? 'مشترك' : 'اشتراك'}
        </div>
      </div>
      {move > 0 && <div style={{opacity: cursorOut}}><Cursor x={cx} y={cy} press={press} /></div>}
    </AbsoluteFill>
  );
};

const TV: React.FC<Props> = ({src}) => {
  const f = useCurrentFrame();
  const {fps, durationInFrames} = useVideoConfig();
  const screen: Rect = [W * 0.2, 150, W * 0.6, H * 0.6];
  const {rect, m} = useShrink(screen);
  const badge = interpolate(f, [0.45 * fps, 0.85 * fps], [0, 1], {extrapolateLeft: 'clamp', extrapolateRight: 'clamp', easing: ease}) * Math.min(1, m * 1.5);
  const progress = interpolate(f, [0, durationInFrames], [0.18, 0.24]);
  const bezel = 18;
  return (
    <AbsoluteFill style={{background: 'radial-gradient(ellipse at 50% 30%, #5A4636 0%, #2C221B 55%, #17120E 100%)'}}>
      <div style={{position: 'absolute', left: 0, right: 0, bottom: 0, height: 230, opacity: m,
        background: 'linear-gradient(#3A2A1E, #22180F)', boxShadow: '0 -6px 24px rgba(0,0,0,.5)'}} />
      <div style={{position: 'absolute', left: screen[0] - bezel, top: screen[1] - bezel, width: screen[2] + 2 * bezel,
        height: screen[3] + 2 * bezel, borderRadius: 16, background: '#0B0B0B', opacity: m,
        boxShadow: '0 50px 120px rgba(0,0,0,.7), 0 0 120px rgba(120,160,255,.12)'}} />
      <div style={{position: 'absolute', left: W / 2 - 160, top: screen[1] + screen[3] + bezel, width: 320, height: 26,
        background: '#111', borderRadius: '0 0 10px 10px', opacity: m}} />
      <Footage src={src} rect={rect} radius={4 * m} />
      <div style={{position: 'absolute', left: screen[0], top: screen[1] + screen[3] - 8, height: 8,
        width: screen[2] * progress, background: '#FF0033', opacity: m}} />
      <div style={{position: 'absolute', top: H - 170, left: 0, right: 0, display: 'flex', justifyContent: 'center',
        opacity: badge, transform: `translateY(${(1 - badge) * 24}px)`}}>
        <div style={{display: 'flex', direction: 'rtl', alignItems: 'center', gap: 22, padding: '18px 44px', borderRadius: 999,
          background: 'rgba(15,15,15,.82)', color: '#fff', fontFamily: 'Tajawal', fontWeight: 700, fontSize: 46}}>
          <svg width={54} height={54} viewBox="0 0 24 24"><path fill="#FF0033" d="M3 5h18a1 1 0 0 1 1 1v11a1 1 0 0 1-1 1h-7v2h3v1H7v-1h3v-2H3a1 1 0 0 1-1-1V6a1 1 0 0 1 1-1Zm1 2v9h16V7Z" /></svg>
          لمشاهدة أفضل.. شغّلها على التلفزيون
        </div>
      </div>
    </AbsoluteFill>
  );
};

/** The presenter keeps talking while his shot is wrapped in a YouTube scene; stickers sit on top. */
export const FaceFx: React.FC<Props> = (props) => {
  useFonts();
  const {fx, src, stickers = [], style} = props;
  return (
    <AbsoluteFill style={{background: '#000'}}>
      {fx === 'subscribe' ? <Subscribe {...props} /> : fx === 'tv' ? <TV {...props} /> : <Footage src={src} rect={FULL} radius={0} />}
      <Stickers stickers={stickers} style={style} W={W} H={H} spots={fx === 'none' ? undefined : SCENE_SPOTS} />
    </AbsoluteFill>
  );
};
