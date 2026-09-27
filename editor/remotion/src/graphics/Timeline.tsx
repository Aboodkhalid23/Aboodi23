import React from 'react';
import {useCurrentFrame} from 'remotion';
import {appear, Background, BaseProps, FPS} from '../style';

export const Timeline: React.FC<BaseProps & {items: {year: string; label: string}[]}> = ({style, durationSec, items}) => {
  const f = useCurrentFrame();
  const step = (durationSec * FPS * 0.7) / Math.max(1, items.length);
  return (
    <Background style={style}>
      <div style={{position: 'relative', width: 1600, height: 500}}>
        <div style={{position: 'absolute', top: 240, right: 0, height: 10, background: style.palette.ink,
          width: `${appear(f, 0, step * items.length) * 100}%`}} />
        {items.map((it, i) => {
          const a = appear(f, i * step, 10);
          const x = items.length === 1 ? 50 : (i / (items.length - 1)) * 90 + 5;
          return (
            <div key={i} style={{position: 'absolute', right: `${x}%`, top: 0, width: 360, marginRight: -180, textAlign: 'center',
              opacity: a, transform: `translateY(${(1 - a) * 30}px)`}}>
              <div style={{fontSize: 76, fontWeight: 900, direction: 'ltr'}}>{it.year}</div>
              <div style={{width: 60, height: 60, borderRadius: 30, background: style.palette.accent, margin: '48px auto',
                border: `8px solid ${style.palette.ink}`}} />
              <div style={{fontSize: 54, fontWeight: 700}}>{it.label}</div>
            </div>
          );
        })}
      </div>
    </Background>
  );
};
