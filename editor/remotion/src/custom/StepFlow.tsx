import React from 'react';
import {interpolate, spring, useCurrentFrame, useVideoConfig} from 'remotion';
import {appear, Background, CustomProps, ease} from '../style';

export const about = 'عملية خطوة بخطوة: مربعات تطلع وحدة ورا الثانية وأسهم تنرسم بيناتها (مثلاً: شلون تنتقل الفلوس، مراحل صناعة شي).';

type Props = CustomProps & {title?: string; steps: string[]; highlight?: number};

/** Boxes appear one after another across the frame (right to left), arrows draw between them. */
export const Scene: React.FC<Props> = ({style, durationSec, title, steps, highlight}) => {
  const f = useCurrentFrame();
  const {fps} = useVideoConfig();
  const p = style.palette as Record<string, string>;
  const span = Math.max(0.6, (durationSec * 0.75) / Math.max(1, steps.length));   // seconds per step
  const w = Math.min(380, 1600 / steps.length - 70);
  return (
    <Background style={style}>
      {title && (
        <div style={{position: 'absolute', top: 120, width: '100%', textAlign: 'center', direction: 'rtl', fontFamily: 'Cairo',
          fontWeight: 900, fontSize: 84, opacity: appear(f, 0, 10), transform: `translateY(${(1 - appear(f, 0, 10)) * -20}px)`}}>
          {title}
        </div>
      )}
      <div style={{display: 'flex', direction: 'rtl', alignItems: 'center', gap: 0, marginTop: title ? 120 : 0}}>
        {steps.map((s, i) => {
          const at = Math.round((0.3 + i * span) * fps);
          const k = spring({frame: f - at, fps, config: {damping: 14, stiffness: 150}});
          const arrow = interpolate(f, [at - 0.35 * fps, at], [0, 1], {extrapolateLeft: 'clamp', extrapolateRight: 'clamp', easing: ease});
          const hot = highlight === i;
          return (
            <React.Fragment key={i}>
              {i > 0 && (
                <svg width={70} height={40} viewBox="0 0 70 40" style={{transform: 'scaleX(-1)'}}>
                  {arrow > 0.02 && <line x1={4} y1={20} x2={4 + 52 * arrow} y2={20} stroke={style.palette.ink} strokeWidth={6} strokeLinecap="round" />}
                  {arrow > 0.95 && <path d="M50 8 L64 20 L50 32" fill="none" stroke={style.palette.ink} strokeWidth={6} strokeLinecap="round" />}
                </svg>
              )}
              <div style={{width: w, minHeight: 220, padding: '30px 26px', background: hot ? style.palette.accent : '#FBF8F1',
                border: `6px solid ${style.palette.ink}`, borderRadius: 18, boxShadow: '0 16px 30px rgba(0,0,0,.18)',
                display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', gap: 14,
                transform: `scale(${k}) rotate(${(i % 2 ? 1 : -1) * 1.5}deg)`, opacity: Math.min(1, k * 1.4)}}>
                <div style={{width: 64, height: 64, borderRadius: 32, background: hot ? style.palette.ink : (p.red ?? '#C4382E'),
                  color: '#fff', fontFamily: 'Oswald', fontWeight: 700, fontSize: 40, display: 'flex', alignItems: 'center',
                  justifyContent: 'center'}}>{i + 1}</div>
                <div style={{fontFamily: 'Tajawal', fontWeight: 800, fontSize: Math.min(54, w / 6), textAlign: 'center',
                  direction: 'rtl', lineHeight: 1.25}}>{s}</div>
              </div>
            </React.Fragment>
          );
        })}
      </div>
    </Background>
  );
};
