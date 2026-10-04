import React from 'react';
import {AbsoluteFill, Img, staticFile} from 'remotion';
import {BaseProps, useFonts} from '../style';

type Props = BaseProps & {person: string; text: string; highlight?: string; src?: string; variant?: number};

/** YouTube thumbnail (1920×1080, rendered at 1280×720): him cut out large with a thick paper edge, 2–4 huge words,
 *  one word on the accent colour, and optionally the story's picture as a taped print. Three layouts by `variant`. */
export const Thumbnail: React.FC<Props> = ({style, person, text, highlight, src, variant = 0}) => {
  useFonts();
  const accent = style.palette.accent;
  const red = (style.palette as Record<string, string>).red ?? '#C4382E';
  const bgs = ['#F1EADB', '#151515', accent];
  const ink = variant === 1 ? '#F7F1E3' : '#151515';
  const words = text.split(/\s+/);
  const hl = highlight || words[words.length - 1];
  const size = text.length > 14 ? 150 : 190;
  const left = variant !== 2;                       // text on the left (person right), or the other way round
  return (
    <AbsoluteFill style={{background: bgs[variant % 3], overflow: 'hidden'}}>
      <AbsoluteFill style={{backgroundImage: `url(${staticFile('paper-noise.png')})`, backgroundSize: '512px 512px',
        mixBlendMode: variant === 1 ? 'screen' : 'multiply', opacity: variant === 1 ? 0.08 : 0.4}} />
      <div style={{position: 'absolute', width: 900, height: 900, borderRadius: '50%', top: 160, [left ? 'right' : 'left']: -60,
        background: variant === 2 ? '#151515' : accent}} />
      {src && (
        <div style={{position: 'absolute', top: 70, [left ? 'right' : 'left']: 700, transform: 'rotate(5deg)', background: '#FBF8F1',
          padding: 14, boxShadow: '0 20px 40px rgba(0,0,0,.35)'}}>
          <Img src={staticFile(src)} style={{width: 420, height: 300, objectFit: 'cover', display: 'block'}} />
        </div>
      )}
      <Img src={staticFile(person)} style={{position: 'absolute', bottom: 0, [left ? 'right' : 'left']: -40, height: 1040,
        filter: 'drop-shadow(0 0 0 #fff) drop-shadow(10px 0 0 #fff) drop-shadow(-10px 0 0 #fff) drop-shadow(0 -10px 0 #fff) drop-shadow(0 24px 40px rgba(0,0,0,.45))'}} />
      <div style={{position: 'absolute', top: 120, bottom: 120, [left ? 'left' : 'right']: 70, width: 840, display: 'flex',
        flexDirection: 'column', justifyContent: 'center', direction: 'rtl', textAlign: 'right'}}>
        <div style={{fontFamily: 'Lalezar, Blaka', fontSize: size, lineHeight: 1.12, color: ink,
          textShadow: variant === 1 ? '0 8px 30px rgba(0,0,0,.6)' : '0 6px 0 rgba(0,0,0,.08)'}}>
          {words.map((w, k) => (
            <span key={k}>{w === hl
              ? <span style={{background: variant === 2 ? '#151515' : red, color: '#fff', padding: '0 18px', borderRadius: 10,
                  boxDecorationBreak: 'clone', WebkitBoxDecorationBreak: 'clone'}}>{w}</span>
              : w}{k < words.length - 1 ? ' ' : ''}</span>
          ))}
        </div>
      </div>
    </AbsoluteFill>
  );
};
