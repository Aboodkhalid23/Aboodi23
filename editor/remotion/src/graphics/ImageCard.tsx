import React from 'react';
import {AbsoluteFill, Img, interpolate, staticFile, useCurrentFrame} from 'remotion';
import {appear, Background, BaseProps, FPS} from '../style';

const TORN = 'polygon(0% 2%, 6% 0%, 13% 2%, 21% 0%, 30% 1.5%, 40% 0%, 52% 2%, 63% 0%, 74% 1.5%, 86% 0%, 100% 2%, 99% 20%, 100% 41%, 98.5% 63%, 100% 84%, 99% 100%, 88% 98%, 76% 100%, 64% 98.5%, 51% 100%, 39% 98%, 27% 100%, 15% 98%, 5% 100%, 0% 98%, 1% 76%, 0% 55%, 1.5% 33%, 0% 14%)';

export const ImageCard: React.FC<BaseProps & {src: string; treatment: string}> = ({style, durationSec, src, treatment}) => {
  const f = useCurrentFrame();
  const kb = interpolate(f, [0, durationSec * FPS], [1, 1.08]);
  if (treatment === 'paper_cutout') {
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
