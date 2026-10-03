import React from 'react';
import {AbsoluteFill, interpolate, random, spring, useCurrentFrame, useVideoConfig} from 'remotion';
import {appear, Background, BaseProps, ease, StyleProps} from '../style';

type Props = BaseProps & {text: string; variant?: 'marker' | 'ransom' | 'typewriter' | 'highlight'};
const pal = (s: StyleProps) => s.palette as Record<string, string>;

/** Words cut out of different magazines, glued on one by one. Words (not letters) so Arabic stays joined. */
const Ransom: React.FC<{style: StyleProps; text: string}> = ({style, text}) => {
  const f = useCurrentFrame();
  const {fps} = useVideoConfig();
  const words = text.split(/\s+/);
  const papers = ['#FBF8F1', pal(style).accent ?? '#D8B23A', '#1C1B19', '#E9E1CF', pal(style).red ?? '#C4382E'];
  const fonts = [['Lalezar', 400], ['Amiri', 700], ['Cairo', 900], ['Rakkas', 400], ['Changa', 800], ['Reem Kufi', 700]] as const;
  return (
    <Background style={style}>
      <div style={{display: 'flex', flexWrap: 'wrap', justifyContent: 'center', gap: '26px 22px', maxWidth: 1600, direction: 'rtl'}}>
        {words.map((w, i) => {
          const k = spring({frame: f - i * Math.round(0.12 * fps), fps, config: {damping: 12, stiffness: 180}});
          const bg = papers[Math.floor(random(`p${w}${i}`) * papers.length)];
          const [font, weight] = fonts[Math.floor(random(`f${w}${i}`) * fonts.length)];
          const dark = bg === '#1C1B19' || bg === papers[4];
          return (
            <span key={i} style={{background: bg, color: dark ? '#FBF8F1' : '#1C1B19', fontFamily: font, fontWeight: weight,
              fontSize: 120 + random(`s${i}`) * 40, padding: '6px 26px', lineHeight: 1.25,
              transform: `rotate(${(random(`r${i}`) - 0.5) * 9}deg) scale(${k})`, opacity: Math.min(1, k * 1.5),
              boxShadow: '0 8px 14px rgba(0,0,0,.25)'}}>{w}</span>
          );
        })}
      </div>
    </Background>
  );
};

/** Typed on a sheet of paper, with a blinking cursor. Prefixes of Arabic text keep their shaping. */
const Typewriter: React.FC<{style: StyleProps; text: string}> = ({style, text}) => {
  const f = useCurrentFrame();
  const {fps} = useVideoConfig();
  const n = Math.floor(interpolate(f, [0.15 * fps, 0.15 * fps + text.length * 1.6], [0, text.length],
    {extrapolateLeft: 'clamp', extrapolateRight: 'clamp'}));
  const cursor = Math.floor(f / (fps * 0.35)) % 2 === 0;
  return (
    <Background style={style}>
      <div style={{width: 1500, minHeight: 620, background: '#FBF9F3', padding: '90px 110px', direction: 'rtl',
        boxShadow: '0 30px 60px rgba(0,0,0,.25)', transform: 'rotate(-1deg)',
        backgroundImage: 'repeating-linear-gradient(#FBF9F3 0 118px, #d8e1ec 118px 120px)'}}>
        <span style={{fontFamily: 'Noto Kufi Arabic', fontWeight: 700, fontSize: 96, lineHeight: 1.6, color: '#232323'}}>
          {text.slice(0, n)}
        </span>
        <span style={{display: 'inline-block', width: 10, height: 100, background: pal(style).red ?? '#C4382E',
          marginRight: 8, verticalAlign: 'middle', opacity: cursor ? 1 : 0}} />
      </div>
    </Background>
  );
};

/** Serif sentence on paper; a highlighter pen sweeps across it right-to-left. */
const Highlight: React.FC<{style: StyleProps; text: string}> = ({style, text}) => {
  const f = useCurrentFrame();
  const {fps} = useVideoConfig();
  const a = appear(f, 0, 10);
  const sweep = interpolate(f, [0.35 * fps, 1.1 * fps], [0, 1], {extrapolateLeft: 'clamp', extrapolateRight: 'clamp', easing: ease});
  return (
    <Background style={style}>
      <div style={{maxWidth: 1500, textAlign: 'center', direction: 'rtl', opacity: a, transform: `scale(${0.96 + 0.04 * a})`}}>
        <span style={{fontFamily: 'Amiri', fontWeight: 700, fontSize: 130, lineHeight: 1.5, color: '#1C1B19',
          backgroundImage: `linear-gradient(${style.palette.accent}cc, ${style.palette.accent}cc)`, backgroundRepeat: 'no-repeat',
          backgroundPosition: 'right 80%', backgroundSize: `${sweep * 100}% 48%`, boxDecorationBreak: 'clone',
          WebkitBoxDecorationBreak: 'clone', padding: '0 12px'}}>{text}</span>
      </div>
    </Background>
  );
};

const Marker: React.FC<{style: StyleProps; text: string}> = ({style, text}) => {
  const f = useCurrentFrame();
  const a = appear(f);
  return (
    <Background style={style}>
      <AbsoluteFill style={{alignItems: 'center', justifyContent: 'center'}}>
        <div style={{fontFamily: style.fonts.title, fontWeight: 900, fontSize: 150, textAlign: 'center', maxWidth: 1600,
          lineHeight: 1.25, opacity: a, transform: `translateY(${(1 - a) * 40}px)`}}>{text}</div>
        <div style={{height: 22, marginTop: 30, background: style.palette.accent, width: `${appear(f, 8, 16) * 900}px`}} />
      </AbsoluteFill>
    </Background>
  );
};

export const BigText: React.FC<Props> = ({style, text, variant = 'marker'}) => {
  const V = {ransom: Ransom, typewriter: Typewriter, highlight: Highlight, marker: Marker}[variant] ?? Marker;
  return <V style={style} text={text} />;
};
