import React from 'react';
import {useCurrentFrame} from 'remotion';
import {appear, Background, BaseProps} from '../style';

export const Quote: React.FC<BaseProps & {text: string; who: string}> = ({style, text, who}) => {
  const f = useCurrentFrame();
  const words = text.split(' ');
  return (
    <Background style={style}>
      <div style={{fontSize: 260, lineHeight: 0.6, color: style.palette.accent, fontFamily: 'Georgia, serif'}}>”</div>
      <div style={{fontFamily: style.fonts.title, fontWeight: 700, fontSize: 88, maxWidth: 1500, textAlign: 'center', lineHeight: 1.5}}>
        {words.map((w, i) => <span key={i} style={{opacity: appear(f, i * 3, 8)}}>{w} </span>)}
      </div>
      <div style={{fontSize: 52, marginTop: 40, opacity: appear(f, words.length * 3 + 4)}}>— {who}</div>
    </Background>
  );
};
