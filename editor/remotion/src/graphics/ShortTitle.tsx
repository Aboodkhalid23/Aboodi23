import React from 'react';
import {AbsoluteFill} from 'remotion';
import {BaseProps} from '../style';

type Props = BaseProps & {title: string; handle?: string};

/** Transparent 1080×1920 overlay for a Short: the hook title on top, the channel handle at the bottom. */
export const ShortTitle: React.FC<Props> = ({style, title, handle}) => (
  <AbsoluteFill style={{backgroundColor: 'transparent'}}>
    <div style={{position: 'absolute', top: 170, left: 60, right: 60, display: 'flex', justifyContent: 'center'}}>
      <div style={{direction: 'rtl', textAlign: 'center', fontFamily: 'Lalezar', fontSize: title.length > 24 ? 74 : 92, lineHeight: 1.25,
        color: style.palette.ink, background: style.palette.paper, padding: '18px 40px', borderRadius: 14,
        boxShadow: '0 14px 34px rgba(0,0,0,.35)', transform: 'rotate(-1.5deg)'}}>
        <span style={{backgroundImage: `linear-gradient(${style.palette.accent}, ${style.palette.accent})`, backgroundRepeat: 'no-repeat',
          backgroundPosition: 'right 85%', backgroundSize: '100% 38%', boxDecorationBreak: 'clone', WebkitBoxDecorationBreak: 'clone'}}>{title}</span>
      </div>
    </div>
    {handle && (
      <div style={{position: 'absolute', bottom: 260, width: '100%', textAlign: 'center', fontFamily: 'Inter', fontWeight: 700,
        fontSize: 40, color: '#fff', textShadow: '0 3px 12px rgba(0,0,0,.7)', direction: 'ltr'}}>{handle}</div>
    )}
  </AbsoluteFill>
);
