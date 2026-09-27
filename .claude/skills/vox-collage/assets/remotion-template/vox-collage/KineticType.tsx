import React from 'react';
import {interpolate, spring, useCurrentFrame, useVideoConfig} from 'remotion';

export const KineticType: React.FC<{
  text: string;
  enterFrame?: number;
  duration?: number;
  color?: string;
  fontSize?: number;
  weight?: number;
  align?: React.CSSProperties['textAlign'];
  style?: React.CSSProperties;
}> = ({
  text,
  enterFrame = 0,
  duration = 16,
  color = '#182b27',
  fontSize = 72,
  weight = 900,
  align = 'left',
  style,
}) => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();
  const progress = spring({
    frame: frame - enterFrame,
    fps,
    durationInFrames: duration,
    config: {damping: 18, stiffness: 170, mass: 0.7},
  });
  return (
    <div
      style={{
        color,
        fontSize,
        fontWeight: weight,
        lineHeight: 0.98,
        letterSpacing: '-0.04em',
        textAlign: align,
        opacity: interpolate(progress, [0, 0.15, 1], [0, 1, 1]),
        clipPath: `inset(${interpolate(progress, [0, 1], [100, 0])}% 0 0 0)`,
        transform: `translateY(${interpolate(progress, [0, 1], [42, 0])}px)`,
        ...style,
      }}
    >
      {text}
    </div>
  );
};
