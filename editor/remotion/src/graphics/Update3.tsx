/** The owner as a drawn character inside the story (editor/pipeline/avatar.py). The scene is one drawing; his figure
 *  (cut out of it: `fg`) is a separate layer, so the code can make the picture live without any extra AI cost:
 *  the place drifts slowly behind him with a touch of depth blur, he settles in with a small bounce, then breathes
 *  and sways a little (sin² so every move starts and ends at rest). The place behind him is a clean plate
 *  (masks.clean_plate: he is painted out of it), so no second copy of him shows when his layer moves.
 *  Without a cut-out the whole drawing gets a slow push and a gentle hand-held drift. */
import React from 'react';
import {AbsoluteFill, Img, interpolate, spring, staticFile} from 'remotion';
import {ease, StyleProps} from '../style';

export type AvatarProps = {style: StyleProps; src: string; f: number; fps: number; dur: number; fg?: string; caption?: string};

const sin2 = (x: number) => Math.sin(x) * Math.abs(Math.sin(x));   // eases through zero: no jerk at the turns

export const AvatarScene: React.FC<AvatarProps> = ({src, fg, f, fps, dur}) => {
  const t = interpolate(f, [0, dur * fps], [0, 1], {easing: ease});
  const s = f / fps;
  const pic: React.CSSProperties = {position: 'absolute', inset: 0, width: '100%', height: '100%', objectFit: 'cover'};
  if (!fg) {
    const driftX = Math.sin(s * 0.9) * 6, driftY = Math.sin(s * 0.7 + 1) * 4;
    return (
      <AbsoluteFill style={{background: '#000', overflow: 'hidden'}}>
        <Img src={staticFile(src)} style={{...pic, transform: `translate(${driftX}px, ${driftY}px) scale(${1.04 + 0.06 * t})`}} />
      </AbsoluteFill>
    );
  }
  const enter = spring({frame: f, fps, config: {damping: 13, stiffness: 140, mass: 0.8}});
  const breathe = 1 + 0.012 * (0.5 + 0.5 * Math.sin(s * 2.4));
  const sway = sin2(s * 1.3) * 0.8;
  const bob = sin2(s * 1.9) * 5;
  return (
    <AbsoluteFill style={{background: '#000', overflow: 'hidden'}}>
      {/* the place: slower than him (depth), softly out of focus */}
      <Img src={staticFile(src)} style={{...pic, transform: `translateX(${-14 * t}px) scale(${1.05 + 0.04 * t})`, filter: 'blur(1.6px) brightness(.95)'}} />
      {/* him: settles in from slightly below, then lives */}
      <Img src={staticFile(fg)} style={{...pic, transformOrigin: '50% 92%',
        transform: `translate(${18 * t}px, ${(1 - enter) * 40 + bob}px) scale(${(1.05 + 0.1 * t) * (0.96 + 0.04 * enter)}) ` +
          `rotate(${sway}deg) scaleY(${breathe})`,
        filter: 'drop-shadow(0 18px 22px rgba(0,0,0,.35))'}} />
      <AbsoluteFill style={{background: 'radial-gradient(ellipse at center, transparent 60%, rgba(0,0,0,.35) 100%)'}} />
    </AbsoluteFill>
  );
};
