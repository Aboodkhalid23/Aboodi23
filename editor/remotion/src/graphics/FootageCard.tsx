import React from 'react';
import {RoundedFootage} from './Update4';
import {AbsoluteFill, interpolate, OffthreadVideo, random, spring, staticFile, useCurrentFrame, useVideoConfig} from 'remotion';
import {Background, BaseProps} from '../style';

type Props = BaseProps & {src: string; treatment?: 'crt' | 'paper' | 'rounded'; caption?: string};

const TORN = 'polygon(0% 2%, 6% 0%, 13% 2%, 21% 0%, 30% 1.5%, 40% 0%, 52% 2%, 63% 0%, 74% 1.5%, 86% 0%, 100% 2%, 99% 20%, 100% 41%, 98.5% 63%, 100% 84%, 99% 100%, 88% 98%, 76% 100%, 64% 98.5%, 51% 100%, 39% 98%, 27% 100%, 15% 98%, 5% 100%, 0% 98%, 1% 76%, 0% 55%, 1.5% 33%, 0% 14%)';

/** Real moving footage framed in the episode's world: an old TV set (archive films) or a torn paper print. */
export const FootageCard: React.FC<Props> = ({style, src, treatment = 'crt', caption}) => {
  const f = useCurrentFrame();
  const {fps} = useVideoConfig();
  const video = (filter: string) => (
    <OffthreadVideo src={staticFile(src)} muted style={{width: '100%', height: '100%', objectFit: 'cover', filter}} />
  );
  if (treatment === 'rounded') return <RoundedFootage style={style} durationSec={0} src={src} caption={caption} />;
  if (treatment === 'paper') {
    const k = spring({frame: f, fps, config: {damping: 15, stiffness: 120}});
    return (
      <Background style={style}>
        <div style={{transform: `scale(${0.88 + 0.12 * k}) rotate(${-2 + k}deg)`, opacity: k, filter: 'drop-shadow(0 24px 34px rgba(0,0,0,.35))'}}>
          <div style={{background: '#FBF8F1', padding: 26, clipPath: TORN}}>
            <div style={{width: 1340, height: 754, overflow: 'hidden'}}>{video('contrast(1.05) saturate(.9)')}</div>
          </div>
          {caption && <div style={{position: 'absolute', bottom: -70, right: 40, direction: 'rtl', fontFamily: 'Aref Ruqaa',
            fontWeight: 700, fontSize: 60, color: style.palette.ink}}>{caption}</div>}
        </div>
      </Background>
    );
  }
  const on = interpolate(f, [0, 0.25 * fps], [0, 1], {extrapolateRight: 'clamp'});
  const flick = 0.93 + random(`fl${Math.floor(f / 2)}`) * 0.07;
  return (
    <AbsoluteFill style={{background: 'radial-gradient(ellipse at center, #2a2620 0%, #0d0c0a 75%)', alignItems: 'center', justifyContent: 'center'}}>
      <div style={{width: 1340, height: 960, borderRadius: 60, background: 'linear-gradient(160deg, #5b4c3c, #2d251d)',
        boxShadow: '0 40px 80px rgba(0,0,0,.7)', display: 'flex', alignItems: 'center', padding: 60, gap: 50}}>
        <div style={{width: 1000, height: 760, borderRadius: '48px / 38px', overflow: 'hidden', position: 'relative', background: '#000'}}>
          <div style={{width: '100%', height: '100%', transform: `scale(${2 - on}, ${on})`}}>{video(`contrast(1.15) brightness(${flick})`)}</div>
          <AbsoluteFill style={{backgroundImage: 'repeating-linear-gradient(0deg, rgba(0,0,0,.25) 0 2px, transparent 2px 5px)'}} />
          <AbsoluteFill style={{background: 'radial-gradient(ellipse at center, transparent 55%, rgba(0,0,0,.6) 100%)'}} />
        </div>
        <div style={{display: 'flex', flexDirection: 'column', gap: 50}}>
          {[0, 1].map((i) => <div key={i} style={{width: 90, height: 90, borderRadius: '50%', background: 'radial-gradient(circle at 35% 35%, #8a7a66, #2b241c)'}} />)}
          {Array.from({length: 6}, (_, i) => <div key={i} style={{width: 90, height: 8, background: '#1d1812', borderRadius: 4}} />)}
        </div>
      </div>
    </AbsoluteFill>
  );
};
