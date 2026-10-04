import './fonts';
import React, {useEffect, useState} from 'react';
import {AbsoluteFill, continueRender, delayRender, Easing, interpolate, staticFile, useCurrentFrame} from 'remotion';

export type Palette = {paper: string; ink: string; accent: string};
export type StyleProps = {palette: Palette; fonts: {title: string; body: string}; texture: string};
export type BaseProps = {style: StyleProps; durationSec: number};
/** Props every custom scene (src/custom) receives, plus its own. */
export type CustomProps = BaseProps;

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

/** Paper "boil" (research update): the paper grain jumps to a new spot ~4 times a second, so even a still
 * paper scene breathes like hand-made animation. */
export const boil = (f: number) => `${(Math.floor(f / 8) * 137) % 512}px ${(Math.floor(f / 8) * 71) % 512}px`;

export const Background: React.FC<{style: StyleProps; children: React.ReactNode}> = ({style, children}) => {
  useFonts();
  const f = useCurrentFrame();
  return (
    <AbsoluteFill style={{background: style.palette.paper, direction: 'rtl', fontFamily: style.fonts.body, color: style.palette.ink}}>
      {style.texture !== 'clean' && (
        <AbsoluteFill style={{backgroundImage: `url(${staticFile('paper-noise.png')})`, backgroundSize: '512px 512px',
          mixBlendMode: 'multiply', opacity: style.texture === 'grain' ? 0.25 : 0.35, backgroundPosition: boil(f)}} />
      )}
      <AbsoluteFill style={{alignItems: 'center', justifyContent: 'center'}}>{children}</AbsoluteFill>
    </AbsoluteFill>
  );
};

export const formatNumber = (n: number) => Math.round(n).toLocaleString('en-US');
