import React from 'react';
import {AbsoluteFill, Img, staticFile} from 'remotion';
import {Background, BaseProps} from '../style';

type Props = BaseProps & {caption?: string; src?: string; personX?: number};

/** The scene behind the cut-out presenter (a still): grid paper, a coloured disc where he stands,
 *  and on the free left side either a picture (taped) or the caption in big type. */
export const CutoutBg: React.FC<Props> = ({style, caption, src, personX = 0.66}) => {
  const p = style.palette as Record<string, string>;
  return (
    <Background style={style}>
      <AbsoluteFill style={{backgroundImage: `linear-gradient(${p.grid ?? '#CFC7B6'} 2px, transparent 2px),
        linear-gradient(90deg, ${p.grid ?? '#CFC7B6'} 2px, transparent 2px)`, backgroundSize: '64px 64px', opacity: 0.55}} />
      <div style={{position: 'absolute', left: personX * 1920 - 380, top: 230, width: 760, height: 760, borderRadius: '50%',
        background: style.palette.accent}} />
      {src ? (
        <div style={{position: 'absolute', left: 120, top: 210, transform: 'rotate(-3deg)', background: '#FBF8F1', padding: 20,
          boxShadow: '0 24px 44px rgba(0,0,0,.3)'}}>
          <Img src={staticFile(src)} style={{width: 720, height: 520, objectFit: 'cover', objectPosition: '50% 22%', display: 'block'}} />
          {caption && <div style={{direction: 'rtl', textAlign: 'center', fontFamily: 'Aref Ruqaa', fontWeight: 700, fontSize: 56,
            paddingTop: 14}}>{caption}</div>}
          <div style={{position: 'absolute', top: -22, left: 280, width: 170, height: 44, background: 'rgba(222,205,150,.85)', transform: 'rotate(-4deg)'}} />
        </div>
      ) : caption ? (
        <div style={{position: 'absolute', left: 110, top: 300, width: 760, direction: 'rtl', fontFamily: 'Lalezar', fontSize: 120,
          lineHeight: 1.2, color: style.palette.ink}}>
          <span style={{backgroundImage: `linear-gradient(${style.palette.accent}, ${style.palette.accent})`, backgroundRepeat: 'no-repeat',
            backgroundPosition: 'right 85%', backgroundSize: '100% 40%', boxDecorationBreak: 'clone', WebkitBoxDecorationBreak: 'clone'}}>
            {caption}
          </span>
        </div>
      ) : null}
    </Background>
  );
};
