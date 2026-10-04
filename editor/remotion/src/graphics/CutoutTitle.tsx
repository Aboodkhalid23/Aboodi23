import React from 'react';
import {AbsoluteFill, interpolate, spring, useCurrentFrame, useVideoConfig} from 'remotion';
import {BaseProps, ease, useFonts} from '../style';

// Letters that never join the next one: no kashida may follow them.
const NON_JOINING = new Set(['ا', 'أ', 'إ', 'آ', 'د', 'ذ', 'ر', 'ز', 'و', 'ؤ', 'ة', 'ى', 'ء']);

/** Stretch an Arabic word the calligrapher's way: kashida (ـ) at the last joining point before its end. */
export const stretch = (word: string, n: number): string => {
  if (n <= 0 || !/[؀-ۿ]/.test(word)) return word;
  for (let i = word.length - 2; i >= 1; i--) {
    const a = word[i], b = word[i + 1];
    if (/[ء-ي]/.test(a) && /[ء-ي]/.test(b) && !NON_JOINING.has(a)) {
      return word.slice(0, i + 1) + 'ـ'.repeat(n) + word.slice(i + 1);
    }
  }
  return word;
};

/** White words on black (the alpha of the words that stand behind him, cutout.py "title"): they rise, then
 *  stretch out with kashida while the camera of the line breathes a little wider. */
export const CutoutTitle: React.FC<BaseProps & {text: string; y?: number; maxStretch?: number}> = ({durationSec, text, y = 0.34, maxStretch = 6}) => {
  useFonts();
  const f = useCurrentFrame();
  const {fps} = useVideoConfig();
  const rise = spring({frame: f, fps, config: {damping: 16, stiffness: 120}});
  const grow = interpolate(f, [0.25 * fps, Math.max(0.3, durationSec * 0.6) * fps], [0, 1], {extrapolateLeft: 'clamp', extrapolateRight: 'clamp', easing: ease});
  const n = Math.round(grow * maxStretch);
  const words = text.split(/\s+/).filter(Boolean);
  const longest = words.reduce((a, w) => (w.length > a.length ? w : a), '');
  const shown = words.map((w) => (w === longest ? stretch(w, n) : w)).join(' ');
  const size = Math.min(300, 2600 / Math.max(4, text.length + maxStretch * 0.6));
  return (
    <AbsoluteFill style={{background: '#000'}}>
      <div style={{position: 'absolute', left: 0, right: 0, top: `${y * 100}%`, textAlign: 'center', direction: 'rtl',
        transform: `translateY(-50%) translateY(${(1 - rise) * 80}px) scale(${0.92 + 0.08 * rise + 0.04 * grow})`, opacity: rise,
        fontFamily: 'Lalezar, Blaka', fontSize: size, lineHeight: 1.1, color: '#fff', whiteSpace: 'nowrap'}}>{shown}</div>
    </AbsoluteFill>
  );
};
