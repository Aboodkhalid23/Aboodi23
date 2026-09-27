import React from 'react';
import {interpolate, spring, useCurrentFrame, useVideoConfig} from 'remotion';

export const DrawnArrow: React.FC<{
  path: string;
  viewBox?: string;
  color?: string;
  strokeWidth?: number;
  enterFrame?: number;
  duration?: number;
  length?: number;
  style?: React.CSSProperties;
}> = ({
  path,
  viewBox = '0 0 500 300',
  color = '#c94b32',
  strokeWidth = 12,
  enterFrame = 0,
  duration = 22,
  length = 900,
  style,
}) => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();
  const progress = spring({
    frame: frame - enterFrame,
    fps,
    durationInFrames: duration,
    config: {damping: 200, stiffness: 120, overshootClamping: true},
  });
  const p = interpolate(progress, [0, 1], [0, 1], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
  });
  return (
    <svg viewBox={viewBox} style={{overflow: 'visible', ...style}}>
      <path
        d={path}
        fill="none"
        stroke={color}
        strokeWidth={strokeWidth}
        strokeLinecap="round"
        strokeLinejoin="round"
        strokeDasharray={length}
        strokeDashoffset={length * (1 - p)}
      />
    </svg>
  );
};
