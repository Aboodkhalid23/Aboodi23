import React from 'react';
import {AbsoluteFill, Img, interpolate, spring, staticFile, useCurrentFrame, useVideoConfig} from 'remotion';
import {appear, Background, BaseProps, FPS} from '../style';

const TORN = 'polygon(0% 2%, 6% 0%, 13% 2%, 21% 0%, 30% 1.5%, 40% 0%, 52% 2%, 63% 0%, 74% 1.5%, 86% 0%, 100% 2%, 99% 20%, 100% 41%, 98.5% 63%, 100% 84%, 99% 100%, 88% 98%, 76% 100%, 64% 98.5%, 51% 100%, 39% 98%, 27% 100%, 15% 98%, 5% 100%, 0% 98%, 1% 76%, 0% 55%, 1.5% 33%, 0% 14%)';

export const ImageCard: React.FC<BaseProps & {src: string; treatment: string}> = ({style, durationSec, src, treatment}) => {
  const f = useCurrentFrame();
  const {fps} = useVideoConfig();
  const kb = interpolate(f, [0, durationSec * FPS], [1, 1.08]);
  if (treatment === 'engraving_in_circle') {
    // grid-collage world: the picture, toned like an old print, cut into a circle over a coloured disc
    const pop = spring({frame: f, fps, config: {damping: 15, stiffness: 120}});
    const p = style.palette as Record<string, string>;
    return (
      <Background style={style}>
        <AbsoluteFill style={{backgroundImage: `linear-gradient(${p.grid ?? '#CFC7B6'} 2px, transparent 2px),
          linear-gradient(90deg, ${p.grid ?? '#CFC7B6'} 2px, transparent 2px)`, backgroundSize: '64px 64px', opacity: 0.55}} />
        <div style={{position: 'relative', width: 820, height: 820, transform: `scale(${0.85 + 0.15 * pop})`, opacity: pop}}>
          <div style={{position: 'absolute', inset: -40, borderRadius: '50%', background: style.palette.accent}} />
          <div style={{position: 'absolute', inset: 0, borderRadius: '50%', overflow: 'hidden', background: '#F4EFE3',
            boxShadow: '0 30px 60px rgba(0,0,0,.3)'}}>
            <Img src={staticFile(src)} style={{width: '100%', height: '100%', objectFit: 'cover', transform: `scale(${kb})`,
              filter: 'grayscale(1) contrast(1.35) brightness(1.05) sepia(.25)', mixBlendMode: 'multiply'}} />
          </div>
        </div>
      </Background>
    );
  }
  if (treatment !== 'ken_burns' && treatment !== 'film_grain') {  // paper_cutout, and any unknown treatment
    const a = appear(f, 0, 10);
    return (
      <Background style={style}>
        <div style={{filter: 'drop-shadow(0 22px 30px rgba(0,0,0,.35))', transform: `rotate(-2deg) scale(${0.9 + a * 0.1})`, opacity: a}}>
          <div style={{background: '#FBF8F1', padding: 26, clipPath: TORN}}>
            <div style={{width: 1300, height: 760, overflow: 'hidden'}}>
              <Img src={staticFile(src)} style={{width: '100%', height: '100%', objectFit: 'cover', transform: `scale(${kb})`}} />
            </div>
          </div>
        </div>
      </Background>
    );
  }
  return (
    <AbsoluteFill style={{background: '#000', overflow: 'hidden'}}>
      <Img src={staticFile(src)} style={{width: '100%', height: '100%', objectFit: 'cover', transform: `scale(${kb})`,
        filter: treatment === 'film_grain' ? 'sepia(.35) contrast(1.1)' : undefined}} />
    </AbsoluteFill>
  );
};
