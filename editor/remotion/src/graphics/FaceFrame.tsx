import React from 'react';
import {Background, BaseProps} from '../style';

/** Still background for face_framed: ffmpeg overlays the face at 1152x648, top-left (384,216). */
export const FaceFrame: React.FC<BaseProps> = ({style}) => (
  <Background style={style}>
    <div style={{position: 'absolute', left: 384 - 18, top: 216 - 18, width: 1152 + 36, height: 648 + 36, background: '#FBF8F1',
      boxShadow: '0 25px 50px rgba(0,0,0,.3)', transform: 'rotate(-1deg)'}} />
    {[[330, 180, -12], [1500, 830, -8]].map(([x, y, r], i) => (
      <div key={i} style={{position: 'absolute', left: x, top: y, width: 140, height: 44, background: style.palette.accent,
        opacity: 0.85, transform: `rotate(${r}deg)`}} />
    ))}
  </Background>
);
