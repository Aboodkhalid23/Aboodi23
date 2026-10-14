import {Children, cloneElement, isValidElement, type ReactNode} from 'react';
import type {IllustrationProps} from './types';

const normalizedPaths = (children: ReactNode): ReactNode => Children.map(children, (child) => {
  if (!isValidElement<{children?: ReactNode}>(child)) return child;
  const shape = typeof child.type === 'string' && ['path', 'rect', 'circle', 'ellipse', 'line', 'polyline', 'polygon'].includes(child.type);
  return cloneElement(child, {...(shape ? {pathLength: 1} : {}),
    ...(child.props.children ? {children: normalizedPaths(child.props.children)} : {})});
});

export const Frame = ({progress, accent, children, ink = '#252933', normalized = false, overlay}: IllustrationProps & {children: ReactNode; overlay?: ReactNode}) => {
  const p = Math.max(0, Math.min(1, progress));
  return (
    <svg viewBox="0 0 640 360" width="100%" height="100%" fill="none" xmlns="http://www.w3.org/2000/svg" aria-hidden="true">
      <g
        fill="none"
        stroke={ink}
        strokeWidth="7"
        strokeLinecap="round"
        strokeLinejoin="round"
        opacity={0.35 + p * 0.65}
        style={{strokeDasharray: normalized ? 1 : 900, strokeDashoffset: (normalized ? 1 : 900) * (1 - p)}}
      >
        {normalized ? normalizedPaths(children) : children}
      </g>
      <circle cx="585" cy="48" r={10 + p * 9} fill={accent} opacity={0.55 + p * 0.45} />
      {overlay}
    </svg>
  );
};
