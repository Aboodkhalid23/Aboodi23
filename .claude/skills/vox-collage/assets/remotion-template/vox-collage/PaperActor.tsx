import React from 'react';
import {useCurrentFrame, useVideoConfig} from 'remotion';
import {paperEntrance} from './motion';

export const PaperActor: React.FC<{
  x: number;
  y: number;
  width?: number | string;
  height?: number | string;
  z?: number;
  rotate?: number;
  scale?: number;
  enterFrame?: number;
  duration?: number;
  fromX?: number;
  fromY?: number;
  fromScale?: number;
  fromRotate?: number;
  style?: React.CSSProperties;
  children: React.ReactNode;
}> = ({
  x,
  y,
  width,
  height,
  z = 1,
  rotate = 0,
  scale = 1,
  enterFrame = 0,
  duration = 18,
  fromX = 0,
  fromY = 42,
  fromScale = 0.94,
  fromRotate = -4,
  style,
  children,
}) => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();
  const motion = paperEntrance({
    frame,
    fps,
    start: enterFrame,
    duration,
    fromX,
    fromY,
    fromScale,
    fromRotate,
  });
  return (
    <div
      style={{
        position: 'absolute',
        left: x,
        top: y,
        width,
        height,
        zIndex: z,
        opacity: motion.opacity,
        transform: `translate(-50%, -50%) translate(${motion.x}px, ${motion.y}px) rotate(${rotate + motion.rotate}deg) scale(${scale * motion.scale})`,
        transformOrigin: '50% 50%',
        ...style,
      }}
    >
      {children}
    </div>
  );
};
