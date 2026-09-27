import {Easing, interpolate, spring} from 'remotion';

export type PaperEntrance = {
  frame: number;
  fps: number;
  start?: number;
  duration?: number;
  fromX?: number;
  fromY?: number;
  fromScale?: number;
  fromRotate?: number;
};

export const paperEntrance = ({
  frame,
  fps,
  start = 0,
  duration = 18,
  fromX = 0,
  fromY = 42,
  fromScale = 0.94,
  fromRotate = -4,
}: PaperEntrance) => {
  const progress = spring({
    fps,
    frame: frame - start,
    durationInFrames: duration,
    config: {damping: 14, mass: 0.75, stiffness: 150},
  });
  const opacity = interpolate(progress, [0, 0.18, 1], [0, 1, 1], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
  });
  return {
    progress,
    opacity,
    x: interpolate(progress, [0, 1], [fromX, 0]),
    y: interpolate(progress, [0, 1], [fromY, 0]),
    scale: interpolate(progress, [0, 1], [fromScale, 1]),
    rotate: interpolate(progress, [0, 1], [fromRotate, 0]),
  };
};

export const restrainedPush = (frame: number, duration: number, amount = 0.045) =>
  interpolate(frame, [0, duration], [1, 1 + amount], {
    easing: Easing.bezier(0.16, 1, 0.3, 1),
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
  });

export const stableNoise = (seed: number) => {
  const value = Math.sin(seed * 127.1) * 43758.5453;
  return value - Math.floor(value);
};
