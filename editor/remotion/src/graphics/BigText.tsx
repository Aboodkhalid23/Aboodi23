import React from 'react';
import {useCurrentFrame} from 'remotion';
import {appear, Background, BaseProps} from '../style';

export const BigText: React.FC<BaseProps & {text: string}> = ({style, text}) => {
  const f = useCurrentFrame();
  const a = appear(f);
  return (
    <Background style={style}>
      <div style={{fontFamily: style.fonts.title, fontWeight: 900, fontSize: 150, textAlign: 'center', maxWidth: 1600,
        lineHeight: 1.25, opacity: a, transform: `translateY(${(1 - a) * 40}px)`}}>{text}</div>
      <div style={{height: 22, marginTop: 30, background: style.palette.accent, width: `${appear(f, 8, 16) * 900}px`}} />
    </Background>
  );
};
