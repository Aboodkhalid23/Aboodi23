import React from 'react';
import {interpolate, useCurrentFrame} from 'remotion';
import {appear, Background, BaseProps, ease, formatNumber, FPS} from '../style';

export const NumberCount: React.FC<BaseProps & {value: number; label: string; prefix?: string}> = ({style, durationSec, value, label, prefix}) => {
  const f = useCurrentFrame();
  const end = Math.max(10, durationSec * FPS * 0.6);
  const shown = interpolate(f, [0, end], [0, value], {extrapolateRight: 'clamp', easing: ease});
  return (
    <Background style={style}>
      <div style={{direction: 'ltr', fontFamily: style.fonts.title, fontWeight: 900, fontSize: 190, letterSpacing: -2}}>
        {prefix ?? ''}{formatNumber(shown)}
      </div>
      <div style={{fontSize: 80, fontWeight: 700, padding: '6px 34px', marginTop: 20, opacity: appear(f, 10),
        background: `linear-gradient(${style.palette.accent}, ${style.palette.accent})`, backgroundRepeat: 'no-repeat',
        backgroundPosition: 'right', backgroundSize: `${appear(f, 14, 18) * 100}% 100%`}}>{label}</div>
    </Background>
  );
};
