import React from 'react';
import {AbsoluteFill, Img, interpolate, spring, staticFile, useCurrentFrame, useVideoConfig} from 'remotion';
import {Background, BaseProps} from '../style';

type Props = BaseProps & {channel: {name: string; handle?: string; avatar?: string | null}; title?: string};

// Where YouTube Studio's end-screen elements go (the owner drops "Best for viewer" on the video box and
// "Subscribe" on the circle). Sizes follow YouTube's 1920×1080 end-screen grid.
export const VIDEO_BOX = {x: 230, y: 330, w: 880, h: 495};
export const SUB_CIRCLE = {x: 1330, y: 400, d: 360};

/** The last 20 seconds: channel world background, a frame for the next video and a ring for Subscribe. */
export const EndScreen: React.FC<Props> = ({style, channel, title = 'كمّل وياي'}) => {
  const f = useCurrentFrame();
  const {fps} = useVideoConfig();
  const p = style.palette as Record<string, string>;
  const k = (d: number) => spring({frame: f - Math.round(d * fps), fps, config: {damping: 15, stiffness: 120}});
  const pulse = 1 + 0.03 * Math.sin((f / fps) * Math.PI);   // a slow breath so the frame never looks frozen
  return (
    <Background style={style}>
      <AbsoluteFill style={{backgroundImage: `linear-gradient(${p.grid ?? '#CFC7B6'} 2px, transparent 2px),
        linear-gradient(90deg, ${p.grid ?? '#CFC7B6'} 2px, transparent 2px)`, backgroundSize: '64px 64px', opacity: 0.5}} />
      <div style={{position: 'absolute', top: 120, width: '100%', textAlign: 'center', direction: 'rtl', fontFamily: 'Lalezar',
        fontSize: 110, color: style.palette.ink, transform: `scale(${k(0)})`}}>{title}</div>
      {/* next-video frame: tape at the corners, YouTube puts the thumbnail inside */}
      <div style={{position: 'absolute', left: VIDEO_BOX.x - 18, top: VIDEO_BOX.y - 18, width: VIDEO_BOX.w + 36, height: VIDEO_BOX.h + 36,
        background: '#FBF8F1', boxShadow: '0 24px 50px rgba(0,0,0,.25)', transform: `rotate(-1.5deg) scale(${k(0.3)})`}}>
        <div style={{position: 'absolute', inset: 18, background: style.palette.ink, opacity: 0.85}} />
        <div style={{position: 'absolute', top: -22, left: 60, width: 170, height: 44, background: 'rgba(222,205,150,.85)', transform: 'rotate(-5deg)'}} />
        <div style={{position: 'absolute', top: -22, right: 60, width: 170, height: 44, background: 'rgba(222,205,150,.85)', transform: 'rotate(6deg)'}} />
      </div>
      {/* subscribe ring: the channel picture sits under YouTube's own button */}
      <div style={{position: 'absolute', left: SUB_CIRCLE.x, top: SUB_CIRCLE.y, width: SUB_CIRCLE.d, height: SUB_CIRCLE.d,
        transform: `scale(${k(0.55) * pulse})`}}>
        <div style={{position: 'absolute', inset: -26, borderRadius: '50%', background: style.palette.accent}} />
        <div style={{position: 'absolute', inset: 0, borderRadius: '50%', overflow: 'hidden', background: p.red ?? '#C4382E',
          border: `8px solid ${style.palette.paper}`, display: 'flex', alignItems: 'center', justifyContent: 'center',
          color: '#fff', fontFamily: 'Cairo', fontWeight: 900, fontSize: 150}}>
          {channel.avatar ? <Img src={staticFile(channel.avatar)} style={{width: '100%', height: '100%', objectFit: 'cover'}} /> : channel.name.slice(0, 1)}
        </div>
      </div>
      <div style={{position: 'absolute', left: SUB_CIRCLE.x - 120, width: SUB_CIRCLE.d + 240, top: SUB_CIRCLE.y + SUB_CIRCLE.d + 50,
        textAlign: 'center', direction: 'rtl', opacity: interpolate(f, [0.9 * fps, 1.3 * fps], [0, 1], {extrapolateLeft: 'clamp', extrapolateRight: 'clamp'})}}>
        <div style={{fontFamily: 'Tajawal', fontWeight: 800, fontSize: 46, color: style.palette.ink}}>{channel.name}</div>
        {channel.handle && <div style={{fontFamily: 'Inter', fontSize: 30, color: style.palette.ink, opacity: 0.6, direction: 'ltr'}}>{channel.handle}</div>}
      </div>
    </Background>
  );
};
