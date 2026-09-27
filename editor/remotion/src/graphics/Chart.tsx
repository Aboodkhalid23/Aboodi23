import React from 'react';
import {useCurrentFrame} from 'remotion';
import {appear, Background, BaseProps, formatNumber, FPS} from '../style';

export const Chart: React.FC<BaseProps & {bars: {label: string; value: number}[]; unit: string}> = ({style, durationSec, bars, unit}) => {
  const f = useCurrentFrame();
  const max = Math.max(...bars.map((b) => b.value), 1);
  const grow = durationSec * FPS * 0.5;
  return (
    <Background style={style}>
      <div style={{display: 'flex', alignItems: 'flex-end', gap: 80, height: 760}}>
        {bars.map((b, i) => {
          const a = appear(f, i * 6, grow);
          return (
            <div key={i} style={{display: 'flex', flexDirection: 'column', alignItems: 'center', width: 220}}>
              <div style={{fontSize: 60, fontWeight: 900, direction: 'ltr'}}>{formatNumber(b.value * a)}</div>
              <div style={{width: 200, height: (b.value / max) * 520 * a, background: i === bars.length - 1 ? style.palette.accent : style.palette.ink,
                border: `6px solid ${style.palette.ink}`}} />
              <div style={{fontSize: 52, fontWeight: 700, marginTop: 16}}>{b.label}</div>
            </div>
          );
        })}
      </div>
      <div style={{position: 'absolute', top: 60, fontSize: 48}}>{unit}</div>
    </Background>
  );
};
