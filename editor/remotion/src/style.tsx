import '@fontsource/cairo/400.css';
import '@fontsource/cairo/700.css';
import '@fontsource/cairo/900.css';
import React, {useEffect, useState} from 'react';
import {AbsoluteFill, continueRender, delayRender, Easing, interpolate, staticFile} from 'remotion';

export type Palette = {paper: string; ink: string; accent: string};
export type StyleProps = {palette: Palette; fonts: {title: string; body: string}; texture: string};
export type BaseProps = {style: StyleProps; durationSec: number};

export const FPS = 30;
export const ease = Easing.bezier(0.22, 1, 0.36, 1);

/** Hold rendering until the Arabic font is ready, so frame 0 is never in a fallback font. */
export const useFonts = () => {
  const [handle] = useState(() => delayRender('fonts'));
  useEffect(() => {
    document.fonts.ready.then(() => continueRender(handle));
  }, [handle]);
};

export const appear = (frame: number, start = 0, len = 12) =>
  interpolate(frame, [start, start + len], [0, 1], {extrapolateLeft: 'clamp', extrapolateRight: 'clamp', easing: ease});

export const Background: React.FC<{style: StyleProps; children: React.ReactNode}> = ({style, children}) => {
  useFonts();
  return (
    <AbsoluteFill style={{background: style.palette.paper, direction: 'rtl', fontFamily: style.fonts.body, color: style.palette.ink}}>
      {style.texture !== 'clean' && (
        <AbsoluteFill style={{backgroundImage: `url(${staticFile('paper-noise.png')})`, backgroundSize: '512px 512px',
          mixBlendMode: 'multiply', opacity: style.texture === 'grain' ? 0.25 : 0.35}} />
      )}
      <AbsoluteFill style={{alignItems: 'center', justifyContent: 'center'}}>{children}</AbsoluteFill>
    </AbsoluteFill>
  );
};

export const formatNumber = (n: number) => Math.round(n).toLocaleString('en-US');
