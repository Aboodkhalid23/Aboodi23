import React from 'react';
import {Img, staticFile} from 'remotion';
import {VOX_SHADOW} from './tokens';

export const CutoutImage: React.FC<{
  src: string;
  alt?: string;
  fit?: 'contain' | 'cover';
  style?: React.CSSProperties;
}> = ({src, alt = '', fit = 'contain', style}) => {
  const resolved = /^(https?:|data:)/.test(src) ? src : staticFile(src);
  return (
    <Img
      src={resolved}
      alt={alt}
      style={{
        width: '100%',
        height: '100%',
        objectFit: fit,
        filter: VOX_SHADOW,
        ...style,
      }}
    />
  );
};
