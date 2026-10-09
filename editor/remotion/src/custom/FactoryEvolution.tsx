/** Before → after of one place in a single shot, the Vox way: an archive photo (or film) on paper, marked by
 *  hand, then the years roll on a timeline while the paper tears and today's photo shows through in colour.
 *  Props: old / now — images (or oldVideo — a film clip) in assets; years; labels; facts; the point of interest of
 *  each picture (0–1) for the push-in and the marker circle. */
import React from 'react';
import {AbsoluteFill, Audio, Img, interpolate, OffthreadVideo, random, Sequence, spring, staticFile, useCurrentFrame,
  useVideoConfig} from 'remotion';
import {Background, CustomProps, ease} from '../style';
import {ScribbleCircle, ScribbleLine, useDraw} from '../graphics/HandDrawn';

export const about = 'قبل وبعد لنفس المكان: صورة أرشيف على ورق ويه علامات يد، السنين تعد على خط زمني، والورقة تنشگ وتطلع صورة اليوم بالألوان.';

type Shot = {src: string; video?: string; year: number; label: string; fact: string; focus: [number, number]; ring: [number, number, number, number]};
type Props = CustomProps & {old: Shot; now: Shot; sfx?: boolean};

const AR = '٠١٢٣٤٥٦٧٨٩';
const ar = (n: number | string) => String(n).replace(/\d/g, (d) => AR[+d]);
const clamp = {extrapolateLeft: 'clamp', extrapolateRight: 'clamp'} as const;
const CARD_W = 1500, CARD_H = 960;

/** Words appear one by one (Arabic letters stay joined). */
const Words: React.FC<{text: string; start: number; per?: number; style?: React.CSSProperties}> = ({text, start, per = 4, style}) => {
  const f = useCurrentFrame();
  return (
    <span style={{direction: 'rtl', ...style}}>
      {text.split(' ').map((w, i) => {
        const p = interpolate(f, [start + i * per, start + i * per + 6], [0, 1], {...clamp, easing: ease});
        return <span key={i} style={{opacity: p, display: 'inline-block', transform: `translateY(${(1 - p) * 14}px)`}}>{w}&nbsp;</span>;
      })}
    </span>
  );
};

/** A rubber-stamped year: drops in big and rotated, lands with a little squash. */
const Stamp: React.FC<{text: string; start: number; color: string}> = ({text, start, color}) => {
  const f = useCurrentFrame();
  const {fps} = useVideoConfig();
  const k = spring({frame: f - start, fps, config: {damping: 11, stiffness: 180}});
  if (f < start) return null;
  return (
    <div style={{position: 'absolute', top: 70, right: 120, transform: `rotate(${-8 + 2 * k}deg) scale(${2.2 - 1.2 * k})`,
      opacity: Math.min(1, k * 2), border: `8px solid ${color}`, color, borderRadius: 14, padding: '0 26px',
      fontFamily: 'Lalezar', fontSize: 130, lineHeight: 1.15, mixBlendMode: 'multiply', zIndex: 5}}>{text}</div>
  );
};

/** The picture inside the card: slow push toward the point of interest, film grain for the archive. */
const Picture: React.FC<{shot: Shot; t: number; archive: boolean}> = ({shot, t, archive}) => {
  const [fx, fy] = shot.focus;
  const scale = 1.02 + 0.13 * t;
  const look: React.CSSProperties = archive ? {filter: 'grayscale(1) sepia(.25) contrast(1.12) brightness(1.02)'} : {filter: 'saturate(1.08) contrast(1.04)'};
  const common: React.CSSProperties = {width: '100%', height: '100%', objectFit: 'cover', transformOrigin: `${fx * 100}% ${fy * 100}%`,
    transform: `scale(${scale})`, ...look};
  return shot.video
    ? <OffthreadVideo src={staticFile(shot.video)} muted style={common} />
    : <Img src={staticFile(shot.src)} style={common} />;
};

/** Jagged vertical tear at x (0–1 of the card), deterministic. */
const tear = (x: number, seed: string, off = 0) => {
  const n = 22, pts: string[] = [];
  for (let i = 0; i <= n; i++) {
    const y = (i / n) * 100;
    const j = (random(`${seed}-${i}`) - 0.5) * 3.2 + Math.sin(i * 1.7) * 0.8;
    pts.push(`${(x * 100 + j - off).toFixed(2)}% ${y.toFixed(2)}%`);
  }
  return pts;
};

export const Scene: React.FC<Props> = ({style, old, now, sfx = true}) => {
  const f = useCurrentFrame();
  const {fps, durationInFrames} = useVideoConfig();
  const s = (sec: number) => Math.round(sec * fps);
  const T_TEAR = s(4.4), T_DONE = s(5.7);                  // the tear: 4.4 → 5.7 s
  const tearP = interpolate(f, [T_TEAR, T_DONE], [0, 1], {...clamp, easing: ease});

  // card drops in on the paper
  const drop = spring({frame: f, fps, config: {damping: 15, stiffness: 120}});
  const cardRot = interpolate(f, [0, T_TEAR, T_DONE], [-1.6, -1.6, 0.8], {...clamp, easing: ease});
  const oldT = interpolate(f, [0, T_DONE], [0, 1], clamp);
  const nowT = interpolate(f, [T_TEAR, durationInFrames], [0, 1], clamp);

  // the tear runs right → left (Arabic reading direction): the new picture comes in from the right
  const edge = 1 - tearP * 1.12 + 0.06;
  const clipNow = tearP <= 0 ? 'inset(0 0 0 100%)' : tearP >= 1 ? 'none'
    : `polygon(100% 0, ${tear(edge, 'tear').join(', ')}, 100% 100%)`;
  const clipRim = tearP <= 0 || tearP >= 1 ? 'inset(0 0 0 100%)'
    : `polygon(100% 0, ${tear(edge, 'tear', 1.1).join(', ')}, 100% 100%)`;

  // the years roll on the timeline during the tear
  const yr = Math.round(interpolate(tearP, [0, 1], [old.year, now.year], {easing: (x) => x}));
  const ticksOn = f >= T_TEAR - s(0.3);
  const lineP = interpolate(f, [T_TEAR - s(0.4), T_TEAR], [0, 1], {...clamp, easing: ease});
  const head = interpolate(f, [T_TEAR, T_DONE], [0, 1], {...clamp, easing: ease});
  const lineOut = interpolate(f, [T_DONE + s(0.4), T_DONE + s(0.8)], [1, 0], clamp);

  // hand marks
  const [oldInk, oldSeed] = useDraw(s(1.3), 'old');
  const [oldArrow, oldArrowSeed] = useDraw(s(1.6), 'olda');
  const [nowInk, nowSeed] = useDraw(T_DONE + s(0.6), 'now');
  const [nowArrow, nowArrowSeed] = useDraw(T_DONE + s(0.9), 'nowa');
  const markOld = f < T_TEAR ? 1 : interpolate(f, [T_TEAR, T_TEAR + s(0.25)], [1, 0], clamp);

  // the "before" polaroid comes back at the end for the comparison
  const back = spring({frame: f - s(8.4), fps, config: {damping: 14, stiffness: 110}});

  const Ring: React.FC<{shot: Shot; ink: number; seed: string; arrow: number; arrowSeed: string; label: string; opacity: number}> =
    ({shot, ink, seed, arrow, arrowSeed, label, opacity}) => {
      const [x, y, w, h] = shot.ring;
      const left = x * CARD_W - w / 2, top = y * CARD_H - h / 2;
      const below = top < 190;                               // no room above the ring: the label goes under it
      const ly = below ? top + h - 10 : top - 150;
      return (
        <div style={{position: 'absolute', inset: 0, opacity}}>
          <div style={{position: 'absolute', left, top}}>
            <ScribbleCircle w={w} h={h} color={style.palette.accent} draw={ink} seed={seed} />
          </div>
          <div style={{position: 'absolute', left: left - 120, top: below ? ly - 10 : ly + 70}}>
            <ScribbleLine w={130} dx={110} dy={below ? -70 : 70} color={style.palette.accent} draw={arrow} seed={arrowSeed} arrow />
          </div>
          <div style={{position: 'absolute', right: CARD_W - left + 60, top: ly,
            background: style.palette.accent, color: '#141414', fontFamily: 'Cairo', fontWeight: 900, fontSize: 64,
            padding: '2px 26px 10px', transform: 'rotate(-2deg)', boxShadow: '0 8px 18px rgba(0,0,0,.25)', whiteSpace: 'nowrap',
            opacity: interpolate(arrow, [0.6, 1], [0, 1], clamp)}}>
            <Words text={label} start={0} per={0} />
          </div>
        </div>
      );
    };

  const factStrip = (text: string, start: number, end: number) => {
    const p = interpolate(f, [start, start + s(0.35)], [0, 1], {...clamp, easing: ease});
    const out = interpolate(f, [end - s(0.2), end], [1, 0], clamp);
    if (f < start || f > end) return null;
    return (
      <div style={{position: 'absolute', bottom: 46, right: 70, background: '#141414', color: '#F4F1EA', fontFamily: 'Cairo',
        fontWeight: 700, fontSize: 58, padding: '8px 34px 16px', borderRadius: 6, transform: `translateY(${(1 - p) * 40}px) rotate(1deg)`,
        opacity: Math.min(p, out), boxShadow: '0 10px 24px rgba(0,0,0,.3)', zIndex: 6}}>
        <Words text={text} start={start + s(0.15)} per={3} />
      </div>
    );
  };

  const T = (sec: number) => s(sec);
  return (
    <Background style={style}>
      {sfx && <>
        <Sequence from={0}><Audio src={staticFile('sfx/paper.ogg')} volume={0.7} /></Sequence>
        <Sequence from={T(0.25)}><Audio src={staticFile('sfx/hit.ogg')} volume={0.55} /></Sequence>
        <Sequence from={T(1.3)}><Audio src={staticFile('sfx/pop.ogg')} volume={0.5} /></Sequence>
        <Sequence from={T(2.6)}><Audio src={staticFile('sfx/paper.ogg')} volume={0.4} /></Sequence>
        <Sequence from={T_TEAR - s(0.9)}><Audio src={staticFile('sfx/riser.wav')} volume={0.45} /></Sequence>
        <Sequence from={T_TEAR}><Audio src={staticFile('sfx/whoosh.wav')} volume={0.6} /></Sequence>
        {Array.from({length: 9}, (_, i) => (
          <Sequence key={i} from={T_TEAR + Math.round(i * (T_DONE - T_TEAR) / 9)}><Audio src={staticFile('sfx/tick.ogg')} volume={0.35} /></Sequence>
        ))}
        <Sequence from={T_DONE}><Audio src={staticFile('sfx/boom.wav')} volume={0.6} /></Sequence>
        <Sequence from={T_DONE + s(0.6)}><Audio src={staticFile('sfx/pop.ogg')} volume={0.5} /></Sequence>
        <Sequence from={T(8.4)}><Audio src={staticFile('sfx/paper.ogg')} volume={0.5} /></Sequence>
        <Sequence from={T(8.9)}><Audio src={staticFile('sfx/ding.ogg')} volume={0.4} /></Sequence>
      </>}

      {/* the card */}
      <div style={{position: 'absolute', left: (1920 - CARD_W) / 2, top: 50, width: CARD_W, height: CARD_H,
        transform: `translateY(${(1 - drop) * -700}px) rotate(${cardRot}deg)`, filter: 'drop-shadow(0 22px 30px rgba(0,0,0,.32))'}}>
        <div style={{position: 'absolute', inset: -16, background: '#F7F3EA'}} />
        <div style={{position: 'absolute', inset: 0, overflow: 'hidden'}}>
          <Picture shot={old} t={oldT} archive />
          <AbsoluteFill style={{background: 'radial-gradient(ellipse at center, transparent 55%, rgba(30,20,10,.45) 100%)'}} />
          <AbsoluteFill style={{backgroundImage: `url(${staticFile('paper-noise.png')})`, backgroundSize: '512px', mixBlendMode: 'multiply',
            opacity: 0.45, backgroundPosition: `${(f * 37) % 512}px ${(f * 91) % 512}px`}} />
          {/* torn paper rim, then today's picture */}
          <AbsoluteFill style={{background: '#F7F3EA', clipPath: clipRim}} />
          <AbsoluteFill style={{clipPath: clipNow}}>
            <Picture shot={now} t={nowT} archive={false} />
          </AbsoluteFill>
        </div>
        <Ring shot={old} ink={oldInk} seed={oldSeed} arrow={oldArrow} arrowSeed={oldArrowSeed} label={old.label} opacity={markOld} />
        {f >= T_DONE && <Ring shot={now} ink={nowInk} seed={nowSeed} arrow={nowArrow} arrowSeed={nowArrowSeed} label={now.label} opacity={1} />}
        {f < T_TEAR + s(0.2) && <Stamp text={ar(old.year)} start={s(0.25)} color="#B3261E" />}
        {f >= T_DONE && <Stamp text={ar(now.year)} start={T_DONE} color="#B3261E" />}
      </div>

      {factStrip(old.fact, s(2.6), T_TEAR)}
      {factStrip(now.fact, T_DONE + s(1.5), durationInFrames + 1)}

      {/* the timeline with the years rolling */}
      {ticksOn && (
        <div style={{position: 'absolute', left: 120, right: 120, bottom: 40, height: 150, opacity: lineOut, zIndex: 7,
          background: 'rgba(247,243,234,.94)', borderRadius: 10, boxShadow: '0 10px 24px rgba(0,0,0,.25)', transform: `translateY(${(1 - lineP) * 60}px)`}}>
        <div style={{position: 'absolute', left: 90, right: 90, top: 10, bottom: 0}}>
          <div style={{position: 'absolute', left: 0, right: 0, top: 60, height: 8, background: '#141414', transformOrigin: 'right',
            transform: `scaleX(${lineP})`, borderRadius: 4}} />
          <div style={{position: 'absolute', right: `${head * 100}%`, top: 40, width: 48, height: 48, marginRight: -24, borderRadius: '50%',
            background: style.palette.accent, border: '7px solid #141414'}} />
          <div style={{position: 'absolute', right: `${head * 100}%`, top: -150, transform: 'translateX(50%)', fontFamily: 'Lalezar',
            fontSize: 150, color: '#141414', textShadow: '0 0 0 #fff, 5px 5px 0 #F7F3EA'}}>{ar(yr)}</div>
          <div style={{position: 'absolute', right: -40, top: 78, fontFamily: 'Cairo', fontWeight: 700, fontSize: 40, color: '#141414'}}>{ar(old.year)}</div>
          <div style={{position: 'absolute', left: -40, top: 78, fontFamily: 'Cairo', fontWeight: 700, fontSize: 40, color: '#141414',
            opacity: lineP}}>{ar(now.year)}</div>
        </div>
        </div>
      )}

      {/* "before" comes back small, like a photo pinned to the corner */}
      {f >= s(8.4) && (
        <div style={{position: 'absolute', left: 70, bottom: 60, width: 520, height: 340, transform: `translateX(${(1 - back) * -700}px) rotate(${-6 + back * 2}deg)`,
          background: '#F7F3EA', padding: 14, boxShadow: '0 14px 26px rgba(0,0,0,.35)', zIndex: 8}}>
          <div style={{width: '100%', height: '100%', overflow: 'hidden', position: 'relative'}}>
            <Img src={staticFile(old.src)} style={{width: '100%', height: '100%', objectFit: 'cover', filter: 'grayscale(1) sepia(.25) contrast(1.1)'}} />
            <div style={{position: 'absolute', bottom: 8, right: 10, background: '#B3261E', color: '#fff', fontFamily: 'Lalezar', fontSize: 44,
              padding: '0 14px'}}>{ar(old.year)}</div>
          </div>
        </div>
      )}
    </Background>
  );
};
