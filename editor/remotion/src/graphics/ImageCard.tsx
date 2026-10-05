import React from 'react';
import {AbsoluteFill, Img, interpolate, random, spring, staticFile, useCurrentFrame, useVideoConfig} from 'remotion';
import {appear, Background, BaseProps, ease, FPS, StyleProps} from '../style';
import {Desk, HalftoneCutout, Silhouette} from './Update1';
import {AvatarScene} from './Update3';

const TORN = 'polygon(0% 2%, 6% 0%, 13% 2%, 21% 0%, 30% 1.5%, 40% 0%, 52% 2%, 63% 0%, 74% 1.5%, 86% 0%, 100% 2%, 99% 20%, 100% 41%, 98.5% 63%, 100% 84%, 99% 100%, 88% 98%, 76% 100%, 64% 98.5%, 51% 100%, 39% 98%, 27% 100%, 15% 98%, 5% 100%, 0% 98%, 1% 76%, 0% 55%, 1.5% 33%, 0% 14%)';
// People's heads sit in the upper part of photos: crop from there, never through the face.
const FOCUS = '50% 22%';
const HALFTONE = 'radial-gradient(rgba(0,0,0,.55) 28%, transparent 30%)';

type Props = BaseProps & {src: string; treatment: string; caption?: string; fg?: string; title?: string; titleY?: number; titleFront?: boolean;
  parts?: string[]; face?: number[] | null};
type Inner = {style: StyleProps; src: string; caption: string; f: number; fps: number; dur: number; fg?: string; title?: string;
  titleY?: number; titleFront?: boolean; parts?: string[];
  face?: number[] | null};
const pal = (s: StyleProps) => s.palette as Record<string, string>;

/** Grid paper (grid-collage world) behind every paper treatment. */
const Grid: React.FC<{style: StyleProps}> = ({style}) => (
  <AbsoluteFill style={{backgroundImage: `linear-gradient(${pal(style).grid ?? '#CFC7B6'} 2px, transparent 2px),
    linear-gradient(90deg, ${pal(style).grid ?? '#CFC7B6'} 2px, transparent 2px)`, backgroundSize: '64px 64px', opacity: 0.55}} />
);

const Tape: React.FC<{x: number | string; y: number; r: number; w?: number}> = ({x, y, r, w = 170}) => (
  <div style={{position: 'absolute', left: x, top: y, width: w, height: 46, background: 'rgba(222,205,150,.82)',
    transform: `rotate(${r}deg)`, boxShadow: '0 2px 4px rgba(0,0,0,.12)'}} />
);

const Circle: React.FC<Inner> = ({style, src, f, fps, dur}) => {
  const pop = spring({frame: f, fps, config: {damping: 15, stiffness: 120}});
  const kb = interpolate(f, [0, dur * fps], [1, 1.08]);
  return (
    <Background style={style}>
      <Grid style={style} />
      <div style={{position: 'relative', width: 820, height: 820, transform: `scale(${0.85 + 0.15 * pop})`, opacity: pop}}>
        <div style={{position: 'absolute', inset: -40, borderRadius: '50%', background: style.palette.accent}} />
        <div style={{position: 'absolute', inset: 0, borderRadius: '50%', overflow: 'hidden', background: '#F4EFE3',
          boxShadow: '0 30px 60px rgba(0,0,0,.3)'}}>
          <Img src={staticFile(src)} style={{width: '100%', height: '100%', objectFit: 'cover', objectPosition: FOCUS, transform: `scale(${kb})`,
            filter: 'grayscale(1) contrast(1.35) brightness(1.05) sepia(.25)', mixBlendMode: 'multiply'}} />
        </div>
      </div>
    </Background>
  );
};

/** A clipping cut out of a newspaper: halftone photo, caption as the headline, fake column text. */
const Newspaper: React.FC<Inner> = ({style, src, caption, f, fps, dur}) => {
  const drop = spring({frame: f, fps, config: {damping: 13, stiffness: 110}});
  const push = interpolate(f, [0, dur * fps], [1, 1.06], {easing: ease});
  const hl = appear(f, Math.round(0.5 * fps), Math.round(0.6 * fps));
  return (
    <Background style={style}>
      <Grid style={style} />
      <div style={{transform: `translateY(${(1 - drop) * -120}px) rotate(${-3 + drop}deg) scale(${push})`, opacity: drop,
        filter: 'drop-shadow(0 26px 34px rgba(0,0,0,.33))'}}>
        <div style={{width: 1180, background: '#EFEADF', clipPath: TORN, padding: '54px 64px 70px', direction: 'rtl'}}>
          <div style={{fontFamily: 'Playfair Display', fontWeight: 900, fontSize: 30, letterSpacing: 8, direction: 'ltr',
            textAlign: 'center', borderBottom: '3px double #222', paddingBottom: 10, marginBottom: 22, color: '#222'}}>THE DAILY CHRONICLE</div>
          <div style={{fontFamily: 'Amiri', fontWeight: 700, fontSize: 70, lineHeight: 1.25, color: '#1a1a1a', marginBottom: 22}}>
            <span style={{backgroundImage: `linear-gradient(${style.palette.accent}, ${style.palette.accent})`, backgroundRepeat: 'no-repeat',
              backgroundPosition: 'right 85%', backgroundSize: `${hl * 100}% 45%`}}>{caption}</span>
          </div>
          <div style={{display: 'flex', gap: 30}}>
            <div style={{flex: 1.6, height: 480, overflow: 'hidden', position: 'relative'}}>
              <Img src={staticFile(src)} style={{width: '100%', height: '100%', objectFit: 'cover', objectPosition: FOCUS, filter: 'grayscale(1) contrast(1.25)'}} />
              <AbsoluteFill style={{backgroundImage: HALFTONE, backgroundSize: '6px 6px', mixBlendMode: 'multiply', opacity: 0.35}} />
            </div>
            <div style={{flex: 1, display: 'flex', flexDirection: 'column', gap: 15, paddingTop: 6}}>
              {Array.from({length: 15}, (_, i) => (
                <div key={i} style={{height: 11, background: '#8d887d', opacity: 0.55, width: `${70 + random(`l${i}`) * 30}%`}} />
              ))}
            </div>
          </div>
        </div>
      </div>
    </Background>
  );
};

/** Instant photo taped to the page, the caption hand-written under it. */
const Polaroid: React.FC<Inner> = ({style, src, caption, f, fps, dur}) => {
  const k = spring({frame: f, fps, config: {damping: 14, stiffness: 100}});
  const develop = interpolate(f, [0, 0.9 * fps], [0.35, 1], {extrapolateRight: 'clamp', easing: ease});
  const kb = interpolate(f, [0, dur * fps], [1.04, 1.1]);
  return (
    <Background style={style}>
      <Grid style={style} />
      <div style={{position: 'relative', transform: `translateY(${(1 - k) * 500}px) rotate(${4 - 1.5 * k}deg)`,
        filter: 'drop-shadow(0 30px 40px rgba(0,0,0,.35))'}}>
        <div style={{background: '#FBFAF6', padding: '34px 34px 150px', width: 900}}>
          <div style={{width: 832, height: 640, overflow: 'hidden', background: '#222'}}>
            <Img src={staticFile(src)} style={{width: '100%', height: '100%', objectFit: 'cover', objectPosition: FOCUS, transform: `scale(${kb})`,
              filter: `brightness(${develop}) saturate(${0.6 + 0.3 * develop}) sepia(.18)`}} />
          </div>
          <div style={{position: 'absolute', bottom: 38, left: 0, right: 0, textAlign: 'center', direction: 'rtl',
            fontFamily: 'Aref Ruqaa', fontWeight: 700, fontSize: 64, color: '#2a2a2a',
            opacity: appear(f, Math.round(0.6 * fps), Math.round(0.4 * fps))}}>{caption}</div>
        </div>
        <Tape x={360} y={-24} r={-4} />
      </div>
    </Background>
  );
};

/** Old television: the picture on a curved screen with scanlines and flicker. */
const Crt: React.FC<Inner> = ({src, f, fps, dur}) => {
  const on = interpolate(f, [0, 0.25 * fps], [0, 1], {extrapolateRight: 'clamp'});
  const flick = 0.94 + random(`fl${Math.floor(f / 2)}`) * 0.06;
  const kb = interpolate(f, [0, dur * fps], [1.02, 1.1]);
  return (
    <AbsoluteFill style={{background: 'radial-gradient(ellipse at center, #2a2620 0%, #0d0c0a 75%)', alignItems: 'center', justifyContent: 'center'}}>
      <div style={{width: 1340, height: 960, borderRadius: 60, background: 'linear-gradient(160deg, #5b4c3c, #2d251d)',
        boxShadow: '0 40px 80px rgba(0,0,0,.7), inset 0 0 0 6px rgba(255,255,255,.05)', display: 'flex', alignItems: 'center', padding: 60, gap: 50}}>
        <div style={{width: 1000, height: 760, borderRadius: '48px / 38px', overflow: 'hidden', position: 'relative', background: '#000',
          boxShadow: 'inset 0 0 80px rgba(0,0,0,.9)'}}>
          <Img src={staticFile(src)} style={{width: '100%', height: '100%', objectFit: 'cover', objectPosition: FOCUS, transform: `scale(${kb * (2 - on)}, ${kb * on})`,
            filter: `grayscale(.65) contrast(1.2) brightness(${flick})`}} />
          <AbsoluteFill style={{backgroundImage: 'repeating-linear-gradient(0deg, rgba(0,0,0,.28) 0 2px, transparent 2px 5px)'}} />
          <AbsoluteFill style={{background: 'radial-gradient(ellipse at center, transparent 55%, rgba(0,0,0,.65) 100%)'}} />
        </div>
        <div style={{display: 'flex', flexDirection: 'column', gap: 50}}>
          {[0, 1].map((i) => <div key={i} style={{width: 90, height: 90, borderRadius: '50%', background: 'radial-gradient(circle at 35% 35%, #8a7a66, #2b241c)'}} />)}
          {Array.from({length: 6}, (_, i) => <div key={i} style={{width: 90, height: 8, background: '#1d1812', borderRadius: 4}} />)}
        </div>
      </div>
    </AbsoluteFill>
  );
};

/** Evidence board: photo pinned on cork, a red string running to a note card with the caption. */
const Pinboard: React.FC<Inner> = ({style, src, caption, f, fps, dur}) => {
  const k = spring({frame: f, fps, config: {damping: 15, stiffness: 120}});
  const line = appear(f, Math.round(0.45 * fps), Math.round(0.5 * fps));
  const note = spring({frame: f - Math.round(0.8 * fps), fps, config: {damping: 13}});
  const cam = interpolate(f, [0, dur * fps], [1, 1.05], {easing: ease});
  const red = pal(style).red ?? '#C4382E';
  return (
    <AbsoluteFill style={{background: 'radial-gradient(circle at 40% 40%, #c49a6c, #8d6440)', transform: `scale(${cam})`}}>
      <AbsoluteFill style={{backgroundImage: 'radial-gradient(rgba(60,35,15,.35) 1.2px, transparent 1.6px)', backgroundSize: '9px 11px'}} />
      <div style={{position: 'absolute', left: 980, top: 150, transform: `rotate(-3deg) scale(${k})`, opacity: k,
        filter: 'drop-shadow(0 18px 24px rgba(0,0,0,.4))'}}>
        <div style={{background: '#f6f2ea', padding: 18}}>
          <Img src={staticFile(src)} style={{width: 760, height: 560, objectFit: 'cover', objectPosition: FOCUS, filter: 'contrast(1.1) saturate(.85)'}} />
        </div>
        <div style={{position: 'absolute', top: -14, left: 70, width: 34, height: 34, borderRadius: '50%', background: red,
          boxShadow: 'inset -4px -4px 0 rgba(0,0,0,.25)'}} />
      </div>
      <svg style={{position: 'absolute', inset: 0}} width={1920} height={1080}>
        <line x1={1067} y1={150} x2={1067 - 590 * line} y2={150 + 560 * line} stroke={red} strokeWidth={6} />
      </svg>
      <div style={{position: 'absolute', left: 230, top: 610, width: 560, transform: `rotate(4deg) scale(${note})`, opacity: note,
        background: '#FFF6B8', padding: '38px 42px', direction: 'rtl', fontFamily: 'Aref Ruqaa', fontWeight: 700, fontSize: 64,
        color: '#2a2a2a', lineHeight: 1.25, boxShadow: '0 14px 22px rgba(0,0,0,.3)'}}>{caption}</div>
    </AbsoluteFill>
  );
};

const PaperCutout: React.FC<Inner> = ({style, src, f, fps, dur}) => {
  const a = appear(f, 0, 10);
  const kb = interpolate(f, [0, dur * fps], [1, 1.08]);
  return (
    <Background style={style}>
      <div style={{filter: 'drop-shadow(0 22px 30px rgba(0,0,0,.35))', transform: `rotate(-2deg) scale(${0.9 + a * 0.1})`, opacity: a}}>
        <div style={{background: '#FBF8F1', padding: 26, clipPath: TORN}}>
          <div style={{width: 1300, height: 760, overflow: 'hidden'}}>
            <Img src={staticFile(src)} style={{width: '100%', height: '100%', objectFit: 'cover', objectPosition: FOCUS, transform: `scale(${kb})`}} />
          </div>
        </div>
      </div>
    </Background>
  );
};

/** In-scene title: a huge glowing word stands BEHIND the person (the person is cut out and laid on top).
 * `titleY` is the band where the person hides only a little of it (found in Python, masks.image_layout);
 * `titleFront` when he fills the frame: the word then sits in front, on the least covered band. */
const CinematicTitle: React.FC<Inner> = ({src, fg, title, caption, f, fps, dur, titleY = 0.5, titleFront = false}) => {
  const kb = interpolate(f, [0, dur * fps], [1.02, 1.1]);
  const word = title || caption;
  const rise = spring({frame: f - Math.round(0.25 * fps), fps, config: {damping: 18, stiffness: 90}});
  const pic: React.CSSProperties = {position: 'absolute', inset: 0, width: '100%', height: '100%', objectFit: 'cover',
    objectPosition: FOCUS, transform: `scale(${kb})`};
  const text = (
    <div style={{position: 'absolute', left: 0, right: 0, top: `${titleY * 100}%`, display: 'flex', justifyContent: 'center',
      transform: `translateY(-50%) translateY(${(1 - rise) * 60}px) scale(${0.94 + 0.06 * rise})`, opacity: rise}}>
      <div style={{fontFamily: 'Blaka, Badeen Display, Lalezar', fontSize: word.length > 8 ? 210 : 300, lineHeight: 1.05, color: '#F7D046',
        direction: 'rtl', whiteSpace: 'nowrap',
        textShadow: '0 0 30px rgba(247,208,70,.65), 0 0 90px rgba(247,160,40,.45), 0 10px 30px rgba(0,0,0,.6)'}}>{word}</div>
    </div>
  );
  return (
    <AbsoluteFill style={{background: '#000', overflow: 'hidden'}}>
      <Img src={staticFile(src)} style={{...pic, filter: 'brightness(.82) contrast(1.08)'}} />
      {!titleFront && text}
      {fg && !titleFront && <Img src={staticFile(fg)} style={pic} />}
      <AbsoluteFill style={{background: 'radial-gradient(ellipse at center, transparent 55%, rgba(0,0,0,.5) 100%)'}} />
      {titleFront && text}
    </AbsoluteFill>
  );
};

/** Vox 2.5D: the person (cut out) drifts and grows faster than the background, so the photo gains depth. */
const Parallax: React.FC<Inner> = ({src, fg, f, fps, dur}) => {
  const t = interpolate(f, [0, dur * fps], [0, 1], {easing: ease});
  const bg = 1.04 + 0.04 * t, front = 1.04 + 0.14 * t;
  const pic = (scale: number, x: number, extra: React.CSSProperties = {}): React.CSSProperties => ({position: 'absolute', inset: 0,
    width: '100%', height: '100%', objectFit: 'cover', objectPosition: FOCUS, transform: `translateX(${x}px) scale(${scale})`, ...extra});
  return (
    <AbsoluteFill style={{background: '#000', overflow: 'hidden'}}>
      <Img src={staticFile(src)} style={pic(bg, 20 * t, fg ? {filter: 'blur(2px) brightness(.9)'} : {})} />
      {fg && <Img src={staticFile(fg)} style={pic(front, -30 * t, {filter: 'drop-shadow(0 20px 30px rgba(0,0,0,.45))'})} />}
    </AbsoluteFill>
  );
};

const TREATMENTS: Record<string, React.FC<Inner>> = {
  cinematic_title: CinematicTitle, parallax: Parallax, halftone_cutout: HalftoneCutout, desk: Desk, silhouette: Silhouette,
  avatar: AvatarScene as React.FC<Inner>,
  engraving_in_circle: Circle, newspaper: Newspaper, polaroid: Polaroid, crt: Crt, pinboard: Pinboard, paper_cutout: PaperCutout,
};

export const ImageCard: React.FC<Props> = ({style, durationSec, src, treatment, caption = '', fg, title, titleY, titleFront, parts, face}) => {
  const f = useCurrentFrame();
  const {fps} = useVideoConfig();
  const T = TREATMENTS[treatment];
  if (T) return <T style={style} src={src} caption={caption} f={f} fps={fps} dur={durationSec} fg={fg} title={title}
    titleY={titleY} titleFront={titleFront} parts={parts} face={face} />;
  // ken_burns / film_grain: the picture fills the screen and drifts slowly
  const kb = interpolate(f, [0, durationSec * FPS], [1, 1.08]);
  return (
    <AbsoluteFill style={{background: '#000', overflow: 'hidden'}}>
      <Img src={staticFile(src)} style={{width: '100%', height: '100%', objectFit: 'cover', objectPosition: FOCUS, transform: `scale(${kb})`,
        filter: treatment === 'film_grain' ? 'sepia(.35) contrast(1.1)' : undefined}} />
      <AbsoluteFill style={{background: 'radial-gradient(ellipse at center, transparent 60%, rgba(0,0,0,.45) 100%)'}} />
    </AbsoluteFill>
  );
};
