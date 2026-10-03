import React from 'react';
import {AbsoluteFill, Img, interpolate, spring, staticFile, useCurrentFrame, useVideoConfig} from 'remotion';
import {appear, Background, BaseProps, ease} from '../style';

type Props = BaseProps & {name: string; role?: string; entityKind?: 'person' | 'company'; src?: string};

const TORN = 'polygon(0% 8%, 7% 0%, 18% 6%, 31% 1%, 44% 7%, 58% 0%, 71% 6%, 84% 1%, 100% 7%, 98% 50%, 100% 93%, 86% 100%, 72% 94%, 57% 100%, 43% 95%, 29% 100%, 15% 94%, 0% 100%, 2% 50%)';

/** Real photo of a person (circle cut-out over a coloured disc) or a company logo (pinned paper card).
 *  Sounds in compose.py FX_CUES["entity"]: paper at 0 s, pop at 0.45 s (when the name lands). */
export const EntityCard: React.FC<Props> = ({style, durationSec, name, role = '', entityKind = 'person', src}) => {
  const f = useCurrentFrame();
  const {fps} = useVideoConfig();
  const p = style.palette as Record<string, string>;
  const red = p.red ?? '#C4382E';
  const disc = p.maroon ?? p.accent;
  const pop = spring({frame: f, fps, config: {damping: 14, stiffness: 140}});
  const nameIn = appear(f, Math.round(0.4 * fps), Math.round(0.35 * fps));
  const roleIn = appear(f, Math.round(0.75 * fps), Math.round(0.3 * fps));
  const underline = appear(f, Math.round(0.95 * fps), Math.round(0.4 * fps));
  const drift = interpolate(f, [0, durationSec * fps], [1, 1.04]);   // slow push-in, never still-dead

  const picture = entityKind === 'company' ? (
    <div style={{transform: `scale(${0.85 + 0.15 * pop}) rotate(-1.5deg)`, opacity: pop,
      background: '#FBF8F1', padding: '60px 80px', boxShadow: '0 30px 60px rgba(0,0,0,.28)', position: 'relative'}}>
      {[[-30, -18, -8], [null, -18, 9]].map(([l, t, r], i) => (
        <div key={i} style={{position: 'absolute', top: t as number, left: l === null ? undefined : (l as number),
          right: l === null ? -30 : undefined, width: 150, height: 44, background: 'rgba(216,178,58,.75)',
          transform: `rotate(${r}deg)`}} />
      ))}
      {src ? <Img src={staticFile(src)} style={{maxWidth: 820, maxHeight: 420, objectFit: 'contain', display: 'block'}} />
        : <div style={{fontFamily: 'Lalezar', fontSize: 180, color: style.palette.ink}}>{name}</div>}
    </div>
  ) : (
    <div style={{position: 'relative', width: 620, height: 620, transform: `scale(${0.8 + 0.2 * pop})`, opacity: pop}}>
      <div style={{position: 'absolute', inset: -34, borderRadius: '50%', background: disc}} />
      <div style={{position: 'absolute', inset: 0, borderRadius: '50%', overflow: 'hidden', border: `10px solid ${style.palette.paper}`,
        boxShadow: '0 25px 50px rgba(0,0,0,.35)'}}>
        {src ? <Img src={staticFile(src)} style={{width: '100%', height: '100%', objectFit: 'cover', objectPosition: '50% 22%',
          transform: `scale(${drift})`, filter: 'contrast(1.05) saturate(.9)'}} />
          : <div style={{width: '100%', height: '100%', background: style.palette.ink, color: style.palette.paper,
            fontSize: 260, fontFamily: 'Cairo', fontWeight: 900, display: 'flex', alignItems: 'center', justifyContent: 'center'}}>{name.slice(0, 1)}</div>}
      </div>
    </div>
  );

  return (
    <Background style={style}>
      <AbsoluteFill style={{flexDirection: 'row', alignItems: 'center', justifyContent: 'center', gap: 110, padding: '0 140px'}}>
        {picture}
        <div style={{display: 'flex', flexDirection: 'column', alignItems: 'flex-start', gap: 26, maxWidth: 820}}>
          {/* name: revealed right-to-left with a wipe (Arabic letters stay joined) */}
          <div style={{fontFamily: 'Changa', fontWeight: 800, fontSize: 132, lineHeight: 1.05, color: red,
            clipPath: `inset(0 0 0 ${(1 - nameIn) * 100}%)`, transform: `translateY(${(1 - nameIn) * 20}px)`}}>{name}</div>
          {role && (
            <div style={{position: 'relative', opacity: roleIn, transform: `translateX(${(1 - roleIn) * -30}px) rotate(-1deg)`}}>
              <div style={{background: '#FBF8F1', clipPath: TORN, padding: '18px 44px', fontFamily: 'Tajawal', fontWeight: 700,
                fontSize: 54, color: style.palette.ink, boxShadow: '0 8px 18px rgba(0,0,0,.2)'}}>{role}</div>
              <div style={{position: 'absolute', bottom: -14, right: 20, height: 8, background: red, borderRadius: 4,
                width: `${interpolate(underline, [0, 1], [0, 88], {easing: ease})}%`}} />
            </div>
          )}
        </div>
      </AbsoluteFill>
    </Background>
  );
};
