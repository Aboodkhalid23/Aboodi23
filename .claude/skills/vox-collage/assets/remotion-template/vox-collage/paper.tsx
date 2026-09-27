import React from 'react';
import {AbsoluteFill} from 'remotion';
import {stableNoise} from './motion';
import {VOX_PALETTE, VOX_SHADOW} from './tokens';

const tornPolygon = (seed: number, jitter = 1.4) => {
  const points: string[] = [];
  const steps = 14;
  for (let i = 0; i <= steps; i++) {
    points.push(`${(i / steps) * 100}% ${stableNoise(seed + i) * jitter}%`);
  }
  for (let i = 1; i <= steps; i++) {
    points.push(`${100 - stableNoise(seed + 100 + i) * jitter}% ${(i / steps) * 100}%`);
  }
  for (let i = 1; i <= steps; i++) {
    points.push(`${100 - (i / steps) * 100}% ${100 - stableNoise(seed + 200 + i) * jitter}%`);
  }
  for (let i = 1; i < steps; i++) {
    points.push(`${stableNoise(seed + 300 + i) * jitter}% ${100 - (i / steps) * 100}%`);
  }
  return `polygon(${points.join(',')})`;
};

export const PaperSubstrate: React.FC<{
  color?: string;
  children?: React.ReactNode;
}> = ({color = VOX_PALETTE.cream, children}) => (
  <AbsoluteFill
    style={{
      backgroundColor: color,
      overflow: 'hidden',
      color: VOX_PALETTE.ink,
      fontFamily: 'Arial, "Microsoft YaHei", sans-serif',
    }}
  >
    <AbsoluteFill
      style={{
        opacity: 0.28,
        backgroundImage:
          'radial-gradient(circle at 20% 30%, rgba(24,43,39,.16) 0 0.7px, transparent 0.9px), radial-gradient(circle at 70% 60%, rgba(255,255,255,.6) 0 0.8px, transparent 1px)',
        backgroundSize: '7px 7px, 11px 11px',
        mixBlendMode: 'multiply',
      }}
    />
    {children}
  </AbsoluteFill>
);

export const TornPaper: React.FC<{
  seed?: number;
  color?: string;
  shadow?: boolean;
  style?: React.CSSProperties;
  children?: React.ReactNode;
}> = ({seed = 1, color = VOX_PALETTE.paper, shadow = true, style, children}) => (
  <div
    style={{
      position: 'relative',
      backgroundColor: color,
      clipPath: tornPolygon(seed),
      filter: shadow ? VOX_SHADOW : undefined,
      overflow: 'hidden',
      ...style,
    }}
  >
    <div
      style={{
        position: 'absolute',
        inset: 0,
        opacity: 0.2,
        backgroundImage:
          'radial-gradient(circle, rgba(24,43,39,.38) 0 0.75px, transparent 0.9px)',
        backgroundSize: '6px 6px',
        mixBlendMode: 'multiply',
      }}
    />
    <div style={{position: 'relative', width: '100%', height: '100%'}}>{children}</div>
  </div>
);
