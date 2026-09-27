import React from 'react';
import {useCurrentFrame} from 'remotion';
import {appear, Background, BaseProps, FPS} from '../style';

export const Headline: React.FC<BaseProps & {outlet: string; title: string; highlight: string}> = ({style, durationSec, outlet, title, highlight}) => {
  const f = useCurrentFrame();
  const i = highlight ? title.indexOf(highlight) : -1;
  const [before, hl, after] = i < 0 ? [title, '', ''] : [title.slice(0, i), highlight, title.slice(i + highlight.length)];
  const sweep = appear(f, 10, Math.max(8, durationSec * FPS * 0.35));
  return (
    <Background style={style}>
      <div style={{width: 1500, background: '#FBF8F1', padding: '60px 80px', boxShadow: '0 25px 60px rgba(0,0,0,.25)',
        transform: `rotate(-1.5deg) scale(${0.94 + appear(f) * 0.06})`, opacity: appear(f, 0, 8)}}>
        <div style={{fontFamily: 'Georgia, serif', fontSize: 40, letterSpacing: 6, textTransform: 'uppercase',
          borderBottom: `3px solid ${style.palette.ink}`, paddingBottom: 16, marginBottom: 30, direction: 'ltr'}}>{outlet}</div>
        <div style={{fontFamily: style.fonts.title, fontWeight: 900, fontSize: 92, lineHeight: 1.45}}>
          {before}
          <span style={{background: `linear-gradient(${style.palette.accent}, ${style.palette.accent})`, backgroundRepeat: 'no-repeat',
            backgroundPosition: 'right', backgroundSize: `${sweep * 100}% 70%`, backgroundPositionY: '80%'}}>{hl}</span>
          {after}
        </div>
      </div>
    </Background>
  );
};
