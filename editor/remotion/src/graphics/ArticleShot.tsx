import React from 'react';
import {AbsoluteFill, Img, interpolate, spring, staticFile, useCurrentFrame, useVideoConfig} from 'remotion';
import {Background, BaseProps, ease} from '../style';

type Props = BaseProps & {
  src: string;                    // screenshot of the real page
  rects?: number[][];             // the quote's line boxes, as fractions of the screenshot [x, y, w, h]
  rtl?: boolean;
  site?: string;
  date?: string;
};

const PAGE_W = 1640;              // how wide the page sits in the frame before the push-in

/** A real article: the page lands, the camera pushes in to the quote, a highlighter runs along it. */
export const ArticleShot: React.FC<Props> = ({style, durationSec, src, rects = [], rtl = false, site, date}) => {
  const f = useCurrentFrame();
  const {fps} = useVideoConfig();
  const land = spring({frame: f, fps, config: {damping: 16, stiffness: 120}});
  const push = interpolate(f, [0.55 * fps, 1.5 * fps], [0, 1], {extrapolateLeft: 'clamp', extrapolateRight: 'clamp', easing: ease});
  const drift = interpolate(f, [1.5 * fps, durationSec * fps], [1, 1.035], {extrapolateLeft: 'clamp', extrapolateRight: 'clamp'});
  const pageH = PAGE_W * 0.625;   // screenshots are 16:10
  // the quote's bounding box in page pixels
  const bx = rects.length ? Math.min(...rects.map((r) => r[0])) : 0;
  const by = rects.length ? Math.min(...rects.map((r) => r[1])) : 0.3;
  const bx2 = rects.length ? Math.max(...rects.map((r) => r[0] + r[2])) : 1;
  const by2 = rects.length ? Math.max(...rects.map((r) => r[1] + r[3])) : 0.45;
  const cx = ((bx + bx2) / 2) * PAGE_W, cy = ((by + by2) / 2) * pageH;
  const zoom = Math.min(2.6, Math.max(1.2, 1400 / Math.max(80, (bx2 - bx) * PAGE_W)));
  const z = interpolate(push, [0, 1], [1, zoom]) * drift;
  // move so the quote's centre ends at the frame centre
  const tx = interpolate(push, [0, 1], [0, PAGE_W / 2 - cx]);
  const ty = interpolate(push, [0, 1], [0, pageH / 2 - cy]);
  // highlighter: line by line, in reading direction
  const sweep = interpolate(f, [1.2 * fps, 2.2 * fps], [0, rects.length || 1], {extrapolateLeft: 'clamp', extrapolateRight: 'clamp'});
  return (
    <Background style={style}>
      <AbsoluteFill style={{alignItems: 'center', justifyContent: 'center', overflow: 'hidden'}}>
        <div style={{width: PAGE_W, height: pageH, position: 'relative', transform: `scale(${(0.9 + 0.1 * land) * z}) translate(${tx}px, ${ty}px) rotate(${-1.2 * (1 - push)}deg)`,
          opacity: land, boxShadow: '0 30px 70px rgba(0,0,0,.35)', background: '#fff'}}>
          <Img src={staticFile(src)} style={{width: '100%', height: '100%', display: 'block'}} />
          {rects.map((r, i) => {
            const k = Math.min(1, Math.max(0, sweep - i));
            return (
              <div key={i} style={{position: 'absolute', top: `${r[1] * 100}%`, height: `${r[3] * 100}%`,
                [rtl ? 'right' : 'left']: `${(rtl ? 1 - r[0] - r[2] : r[0]) * 100}%`, width: `${r[2] * 100 * k}%`,
                background: style.palette.accent, mixBlendMode: 'multiply', opacity: 0.85, borderRadius: 3}} />
            );
          })}
        </div>
      </AbsoluteFill>
      {site && (
        <div style={{position: 'absolute', bottom: 54, right: 70, direction: 'ltr', background: style.palette.ink, color: style.palette.paper,
          fontFamily: 'Inter', fontWeight: 700, fontSize: 34, padding: '8px 22px', opacity: interpolate(f, [0.3 * fps, 0.7 * fps], [0, 1],
          {extrapolateLeft: 'clamp', extrapolateRight: 'clamp'})}}>{site}{date ? `  ·  ${date.slice(0, 10)}` : ''}</div>
      )}
    </Background>
  );
};
