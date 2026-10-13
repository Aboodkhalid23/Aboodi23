/** He keeps talking in his room, and the story's papers land beside him (owner's idea, round 6):
 *  a newspaper, a document with a highlighted line, a photo with tape, a quote, a number, a real scanned page.
 *  Vox look: paper texture, slight hand-made wobble, highlighter swipe, papers pile up as the next one lands.
 *  Props: src (his footage, canvas-sized), side (where the papers go: the emptier side of the frame), papers[]. */
import React from 'react';
import {AbsoluteFill, Img, interpolate, OffthreadVideo, random, spring, staticFile, useCurrentFrame, useVideoConfig} from 'remotion';
import {ease, StyleProps, useFonts} from '../style';
import {ScribbleCircle, useDraw} from './HandDrawn';

export type Paper = {
  type: 'newspaper' | 'document' | 'photo' | 'quote' | 'number' | 'page';
  at?: number;                 // seconds into the scene (default: spread evenly)
  title?: string;              // newspaper headline / document title / photo caption
  text?: string;               // quote text / document body
  lines?: string[];            // document lines
  highlight?: string;          // words (or a line) the highlighter swipes
  outlet?: string;             // newspaper name
  date?: string;               // newspaper / document date
  who?: string;                // quote author
  value?: number;              // number
  label?: string;              // number label
  stamp?: string;              // red rubber stamp on a document
  img?: string;                // published image (newspaper photo / photo / page scan)
  box?: [number, number, number, number];   // page: area to mark (0–1 of the page)
};
type Props = {style: StyleProps; durationSec: number; fps?: number; src: string; side?: 'left' | 'right'; papers: Paper[];
  layout?: 'overlay' | 'desk';   // overlay: he stays full frame, papers on the empty side; desk: he shrinks into a taped photo on the paper desk
  picW?: number;                 // share of the canvas width that is real picture (phone footage is narrow)
  faceX?: number;                // his face centre (0–1 of the canvas)
  layerOnly?: boolean};          // only the papers, on transparent (laid between his room and him by cutout.py)

const W = 1920, H = 1080;
const clamp = {extrapolateLeft: 'clamp', extrapolateRight: 'clamp'} as const;
const AR = '٠١٢٣٤٥٦٧٨٩';
const ar = (s: string | number) => String(s).replace(/\d/g, (d) => AR[+d]);
const YELLOW = '#F7D23C';
const PAPER = '#F3EDDF';

/** Words with a highlighter swiping behind the chosen phrase (right to left, as Arabic is read). */
const Marked: React.FC<{text: string; mark?: string; p: number}> = ({text, mark, p}) => {
  if (!mark || !text.includes(mark)) return <>{text}</>;
  const [a, ...rest] = text.split(mark);
  return (
    <>
      {a}
      <span style={{backgroundImage: `linear-gradient(transparent 52%, ${YELLOW} 52%, ${YELLOW} 92%, transparent 92%)`,
        backgroundRepeat: 'no-repeat', backgroundPosition: 'right', backgroundSize: `${p * 100}% 100%`,
        boxDecorationBreak: 'clone', WebkitBoxDecorationBreak: 'clone'}}>{mark}</span>
      {rest.join(mark)}
    </>
  );
};

const Grain: React.FC<{f: number; opacity?: number}> = ({f, opacity = 0.4}) => (
  <AbsoluteFill style={{backgroundImage: `url(${staticFile('paper-noise.png')})`, backgroundSize: '512px', mixBlendMode: 'multiply',
    opacity, backgroundPosition: `${(Math.floor(f / 8) * 137) % 512}px ${(Math.floor(f / 8) * 71) % 512}px`, pointerEvents: 'none'}} />
);

const Tape: React.FC<{x: number; rot: number}> = ({x, rot}) => (
  <div style={{position: 'absolute', top: -26, left: `${x}%`, width: 150, height: 46, marginLeft: -75, transform: `rotate(${rot}deg)`,
    background: 'rgba(238,228,196,.82)', boxShadow: '0 2px 4px rgba(0,0,0,.15)'}} />
);

/** Body-text stand-in: grey bars like printed columns. */
const Columns: React.FC<{rows: number; seed: string; width?: number}> = ({rows, seed, width = 100}) => (
  <div style={{display: 'flex', flexDirection: 'column', gap: 9, width: `${width}%`}}>
    {Array.from({length: rows}, (_, i) => (
      <div key={i} style={{height: 7, borderRadius: 2, background: 'rgba(40,34,26,.28)', width: `${70 + random(`${seed}${i}`) * 30}%`,
        alignSelf: 'flex-end'}} />
    ))}
  </div>
);

const Card: React.FC<{paper: Paper; p: number; f: number; idx: number}> = ({paper, p, f, idx}) => {
  const {fps} = useVideoConfig();
  const mark = interpolate(p, [0.55, 1], [0, 1], clamp);   // the highlighter runs once the paper has landed
  const [ink, seed] = useDraw(Math.round((paper.at ?? 0) * fps + 0.7 * fps), `pg${idx}`);
  switch (paper.type) {
    case 'newspaper':
      return (
        <div style={{width: 640, background: PAPER, padding: '26px 30px 30px', position: 'relative', direction: 'rtl', color: '#1E1A14'}}>
          <div style={{textAlign: 'center', fontFamily: 'Reem Kufi', fontWeight: 700, fontSize: 52, borderBottom: '4px double #1E1A14', paddingBottom: 6}}>
            {paper.outlet || 'الجريدة'}
          </div>
          <div style={{display: 'flex', justifyContent: 'space-between', fontFamily: 'Amiri', fontSize: 22, padding: '4px 0', borderBottom: '1.5px solid #1E1A14'}}>
            <span>{paper.date ? ar(paper.date) : ''}</span><span>العدد {ar(1000 + Math.round(random(`n${idx}`) * 8000))}</span>
          </div>
          <div style={{fontFamily: 'Amiri', fontWeight: 700, fontSize: 60, lineHeight: 1.2, margin: '16px 0 14px', textWrap: 'balance' as never}}>
            <Marked text={paper.title || ''} mark={paper.highlight} p={mark} />
          </div>
          <div style={{display: 'flex', gap: 18}}>
            {paper.img && (
              <div style={{flex: '0 0 52%', height: 250, overflow: 'hidden', background: '#ccc'}}>
                <Img src={staticFile(paper.img)} style={{width: '100%', height: '100%', objectFit: 'cover', filter: 'grayscale(1) contrast(1.25) brightness(1.05)'}} />
              </div>
            )}
            <Columns rows={paper.img ? 11 : 7} seed={`np${idx}`} />
          </div>
          <Grain f={f} opacity={0.5} />
        </div>
      );
    case 'document': {
      const lines = paper.lines || (paper.text ? [paper.text] : []);
      return (
        <div style={{width: 600, background: '#FBF8F1', padding: '40px 44px 46px', position: 'relative', direction: 'rtl', color: '#222',
          backgroundImage: 'repeating-linear-gradient(transparent 0 47px, rgba(60,90,160,.13) 47px 48px)'}}>
          {paper.date && <div style={{fontFamily: 'Noto Naskh Arabic, Amiri', fontSize: 24, color: '#555', marginBottom: 8}}>{ar(paper.date)}</div>}
          <div style={{fontFamily: 'Noto Kufi Arabic', fontWeight: 700, fontSize: 40, marginBottom: 18, borderBottom: '2px solid #222', paddingBottom: 10}}>{paper.title}</div>
          {lines.map((l, i) => (
            <div key={i} style={{fontFamily: 'Noto Naskh Arabic, Amiri', fontSize: 34, lineHeight: '48px'}}>
              <Marked text={l} mark={paper.highlight && (l.includes(paper.highlight) ? paper.highlight : undefined)} p={mark} />
            </div>
          ))}
          {paper.stamp && (
            <div style={{position: 'absolute', bottom: 40, left: 40, transform: `rotate(-14deg) scale(${interpolate(mark, [0, 0.4], [1.8, 1], clamp)})`,
              opacity: interpolate(mark, [0, 0.3], [0, 0.85], clamp), border: '6px solid #B3261E', color: '#B3261E', borderRadius: 10,
              padding: '0 18px', fontFamily: 'Lalezar', fontSize: 64, mixBlendMode: 'multiply'}}>{paper.stamp}</div>
          )}
          <Grain f={f} opacity={0.3} />
        </div>
      );
    }
    case 'photo':
      return (
        <div style={{width: 560, background: '#FFFDF8', padding: '20px 20px 18px', position: 'relative'}}>
          <Tape x={22} rot={-8} /><Tape x={78} rot={6} />
          <div style={{height: 400, overflow: 'hidden', background: '#ddd'}}>
            {paper.img && <Img src={staticFile(paper.img)} style={{width: '100%', height: '100%', objectFit: 'cover'}} />}
          </div>
          {paper.title && <div style={{fontFamily: 'Aref Ruqaa', fontWeight: 700, fontSize: 46, textAlign: 'center', marginTop: 10, color: '#1E2A5A', direction: 'rtl'}}>{paper.title}</div>}
          <Grain f={f} opacity={0.25} />
        </div>
      );
    case 'quote':
      return (
        <div style={{width: 600, background: PAPER, padding: '30px 44px 36px', position: 'relative', direction: 'rtl', color: '#1E1A14'}}>
          <div style={{fontFamily: 'Amiri', fontSize: 170, lineHeight: 0.6, color: '#C4382E', height: 70}}>”</div>
          <div style={{fontFamily: 'Amiri', fontWeight: 700, fontSize: 50, lineHeight: 1.35}}>
            <Marked text={paper.text || ''} mark={paper.highlight} p={mark} />
          </div>
          {paper.who && <div style={{fontFamily: 'Cairo', fontWeight: 700, fontSize: 32, marginTop: 16, color: '#5A5246'}}>— {paper.who}</div>}
          <Grain f={f} />
        </div>
      );
    case 'number': {
      const v = paper.value ?? 0;
      const n = Math.round(v * interpolate(p, [0.3, 1], [0, 1], {...clamp, easing: ease}));
      return (
        <div style={{width: 560, background: PAPER, padding: '30px 40px 40px', position: 'relative', direction: 'rtl', textAlign: 'center', color: '#1E1A14'}}>
          <div style={{fontFamily: 'Lalezar', fontSize: 190, lineHeight: 1.1, color: '#1E1A14'}}>{ar(n.toLocaleString('en-US'))}</div>
          <div style={{fontFamily: 'Cairo', fontWeight: 800, fontSize: 44, display: 'inline-block'}}>
            <Marked text={paper.label || ''} mark={paper.label} p={mark} />
          </div>
          <Grain f={f} />
        </div>
      );
    }
    case 'page': {
      const [bx, by, bw, bh] = paper.box || [0, 0, 0, 0];
      return (
        <div style={{width: 600, height: 780, background: PAPER, padding: 16, position: 'relative'}}>
          <div style={{position: 'relative', width: '100%', height: '100%', overflow: 'hidden', background: '#ddd'}}>
            {paper.img && <Img src={staticFile(paper.img)} style={{width: '100%', height: '100%', objectFit: 'cover', objectPosition: 'top', filter: 'sepia(.25) contrast(1.1)'}} />}
            {paper.box && (
              <>
                <div style={{position: 'absolute', left: `${bx * 100}%`, top: `${by * 100}%`, width: `${bw * 100}%`, height: `${bh * 100}%`,
                  background: YELLOW, opacity: 0.45 * mark, mixBlendMode: 'multiply'}} />
                <div style={{position: 'absolute', left: `${(bx - 0.04) * 100}%`, top: `${(by - 0.04) * 100}%`}}>
                  <ScribbleCircle w={(bw + 0.08) * 568} h={(bh + 0.08) * 748} color="#C4382E" draw={ink} seed={seed} />
                </div>
              </>
            )}
          </div>
          {paper.title && <div style={{position: 'absolute', bottom: -34, right: 30, background: '#141414', color: '#F4F1EA', fontFamily: 'Cairo',
            fontWeight: 700, fontSize: 34, padding: '4px 20px 10px', direction: 'rtl'}}>{paper.title}</div>}
          <Grain f={f} opacity={0.3} />
        </div>
      );
    }
    default:
      return null;
  }
};

export const FacePaper: React.FC<Props> = ({style, durationSec, src, side = 'right', papers, layout = 'overlay', picW = 1, layerOnly = false, faceX = 0.5}) => {
  useFonts();
  const f = useCurrentFrame();
  const {fps} = useVideoConfig();
  const n = papers.length;
  const times = papers.map((p, i) => p.at ?? (0.25 + i * Math.max(1.6, (durationSec - 1) / Math.max(1, n))));
  const dir = side === 'right' ? 1 : -1;
  const long = durationSec >= 2.5;
  const exit = long ? interpolate(f, [(durationSec - 0.4) * fps, durationSec * fps], [0, 1], {...clamp, easing: ease}) : 0;

  // his picture: full frame, or shrinking into a taped photo on the desk (and back at the end)
  const full: [number, number, number, number] = [W * (1 - picW) / 2, 0, W * picW, H];
  let rect = full;
  let m = 0;
  if (layout === 'desk') {
    const a = (picW * W) / H;
    const ch = Math.min(H * 0.8, (W * 0.56) / a), cw = ch * a;
    const card: [number, number, number, number] = [(side === 'right' ? W * 0.31 : W * 0.69) - cw / 2, (H - ch) / 2, cw, ch];
    const k = interpolate(f, [0, 0.45 * fps], [0, 1], {...clamp, easing: ease});
    m = k * (1 - exit);
    rect = full.map((v, i) => v + (card[i] - v) * m) as typeof full;
  }
  const s = rect[3] / H;
  // papers sit in the middle of the free side (beside his photo on the desk)
  let cx = side === 'right' ? W * 0.775 : W * 0.225;
  let paperScale = 1;
  if (layout === 'desk') {
    const a = (picW * W) / H, cw = Math.min(H * 0.8, (W * 0.56) / a) * a;
    const edge = (side === 'right' ? W * 0.31 : W * 0.69) + dir * cw / 2;
    cx = side === 'right' ? (edge + W) / 2 : edge / 2;
    paperScale = Math.min(1.2, Math.abs(side === 'right' ? W - edge : edge) / 700);
  }
  const push = layout === 'desk' ? 1 : interpolate(f, [0, durationSec * fps], [1, 1.035]);
  return (
    <AbsoluteFill style={{background: layerOnly ? 'transparent' : layout === 'desk' ? style.palette.paper : '#000', overflow: 'hidden'}}>
      {layout === 'desk' && <Grain f={f} opacity={0.35} />}
      {!layerOnly && <div style={{position: 'absolute', left: rect[0], top: rect[1], width: rect[2], height: rect[3], transform: `rotate(${-1.2 * dir * m}deg)`,
        boxShadow: m ? `0 0 0 ${14 * m}px #FFFDF8, 0 ${26 * m}px ${50 * m}px rgba(0,0,0,.4)` : undefined}}>
        <div style={{position: 'absolute', inset: 0, overflow: 'hidden'}}>
          <div style={{position: 'absolute', left: -full[0] * s, top: 0, width: W * s, height: H * s,
            transform: `scale(${push}) translateX(${layout === 'desk' ? 0 : -dir * 18 * interpolate(f, [0, 0.5 * fps], [0, 1], clamp)}px)`}}>
            <OffthreadVideo src={staticFile(src)} muted style={{width: '100%', height: '100%', objectFit: 'cover'}} />
          </div>
        </div>
        {m > 0.5 && <><Tape x={8} rot={-10} /><div style={{position: 'absolute', bottom: -26, right: '6%', width: 150, height: 46,
          transform: 'rotate(-6deg)', background: 'rgba(238,228,196,.82)', boxShadow: '0 2px 4px rgba(0,0,0,.15)'}} /></>}
      </div>}
      {/* overlay: a soft shade on the papers' side so they read against any room */}
      {layout === 'overlay' && <AbsoluteFill style={{background: `linear-gradient(${side === 'right' ? 270 : 90}deg, rgba(0,0,0,.28), transparent 45%)`,
        opacity: interpolate(f, [times[0] * fps - 6, times[0] * fps + 6], [0, 1], clamp) * (1 - exit)}} />}
      {papers.map((paper, i) => {
        const start = Math.round(times[i] * fps);
        if (f < start - 1) return null;
        const p = spring({frame: f - start, fps, config: {damping: 14, stiffness: 120, mass: 0.9}});
        const behind = i < n - 1   // pushed back by the next one
          ? spring({frame: f - Math.round(times[i + 1] * fps), fps, config: {damping: 16, stiffness: 110}}) : 0;
        const depth = n - 1 - i;
        const rest = (random(`rot${i}`) - 0.5) * 8;
        const wobble = (random(`w${i}-${Math.floor(f / 4)}`) - 0.5) * 0.6;                      // hand-made boil
        // behind him: the paper slides out from behind his shoulder; otherwise it flies in from the frame edge
        const from = layerOnly ? faceX * W : cx + dir * 760;
        const x = from + (cx - from) * p - dir * behind * 70 + dir * exit * 900;
        const y = H * 0.5 + (1 - p) * (layerOnly ? 60 : 120) - behind * 30;
        const rot = rest + dir * (1 - p) * 16 - dir * behind * 7 + wobble;
        const scale = (1 - behind * 0.1) * paperScale;
        return (
          <div key={i} style={{position: 'absolute', left: x, top: y, transform: `translate(-50%, -50%) rotate(${rot}deg) scale(${scale})`,
            filter: `drop-shadow(0 ${18 + depth * 2}px 26px rgba(0,0,0,.45)) brightness(${1 - behind * 0.12})`, zIndex: i}}>
            <Card paper={{...paper, at: times[i]}} p={p} f={f} idx={i} />
          </div>
        );
      })}
    </AbsoluteFill>
  );
};
