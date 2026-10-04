import React, {useMemo} from 'react';
import {geoBounds, geoMercator, geoPath} from 'd3-geo';
import {feature} from 'topojson-client';
import world from 'world-atlas/countries-50m.json';
import {interpolate, spring, useCurrentFrame, useVideoConfig} from 'remotion';
import {appear, Background, BaseProps, ease} from '../style';

type Feat = {type: 'Feature'; id: string; properties: {name: string}; geometry: any};
// eslint-disable-next-line @typescript-eslint/no-explicit-any
const countries = (feature(world as any, (world as any).objects.countries) as any).features as Feat[];
type Pin = {lon: number; lat: number; label?: string};
type Props = BaseProps & {
  country?: string;            // one country to highlight (older plans)
  countries?: string[];        // several countries (English names, as on Wikipedia)
  pins?: Pin[];                // places, each with an Arabic label; appear one by one
  route?: [number, number][];  // [lon, lat] points; a line draws through them
  label?: string;              // big title at the bottom
};

// A lon/lat rectangle as a polygon. d3-geo wants the outer ring clockwise; the other way round
// it means "the whole globe except this box" and the camera would never zoom in.
const box = (x0: number, y0: number, x1: number, y1: number) => ({type: 'Feature', geometry: {type: 'Polygon',
  coordinates: [[[x0, y0], [x0, y1], [x1, y1], [x1, y0], [x0, y0]]]}}) as any;
const WORLD = box(-170, -57, 190, 78);   // inhabited world, no Antarctica: fills a 16:9 frame

const byName = (n: string) => countries.find((c) => c.properties.name.toLowerCase() === n.toLowerCase() || c.id === n);

/** Flat map in the episode's world: world view → camera flies in to the subject (then holds),
 *  highlighted countries fill red, a route draws itself, pins drop with their names. */
export const MapZoom: React.FC<Props> = ({style, durationSec, country, countries: names = [], pins = [], route = [], label}) => {
  const f = useCurrentFrame();
  const {fps} = useVideoConfig();
  const p = style.palette as Record<string, string>;
  const red = p.red ?? '#C4382E';
  const targets = useMemo(() => [...names, ...(country ? [country] : [])].map(byName).filter(Boolean) as Feat[], [names, country]);
  // what the camera frames: the highlighted countries + pins + route
  const focus = useMemo(() => {
    const geoms: any[] = targets.map((t) => t.geometry);
    if (pins.length) geoms.push({type: 'MultiPoint', coordinates: pins.map((q) => [q.lon, q.lat])});
    if (route.length) geoms.push({type: 'LineString', coordinates: route});
    if (!geoms.length) return WORLD;
    const [[x0, y0], [x1, y1]] = geoBounds({type: 'GeometryCollection', geometries: geoms} as any);
    const padX = Math.max(4, (x1 - x0) * 0.25), padY = Math.max(3, (y1 - y0) * 0.25);
    return box(x0 - padX, y0 - padY, x1 + padX, y1 + padY);
  }, [targets, pins, route]);
  const [wide, close] = useMemo(() => [
    geoMercator().fitExtent([[40, 40], [1880, 1040]], WORLD),
    geoMercator().fitExtent([[260, 140], [1660, 900]], focus),
  ], [focus]);
  const fly = interpolate(f, [0.15 * fps, 1.4 * fps], [0, 1], {extrapolateLeft: 'clamp', extrapolateRight: 'clamp', easing: ease});
  const drift = interpolate(f, [1.4 * fps, durationSec * fps], [1, 1.04], {extrapolateLeft: 'clamp', extrapolateRight: 'clamp'});
  // zoom in log space so the move feels even, not a rush at the end
  const scale = Math.exp(interpolate(fly, [0, 1], [Math.log(wide.scale()), Math.log(close.scale())])) * drift;
  const proj = geoMercator().scale(scale).translate([
    interpolate(fly, [0, 1], [wide.translate()[0], close.translate()[0] * drift - 960 * (drift - 1)]),
    interpolate(fly, [0, 1], [wide.translate()[1], close.translate()[1] * drift - 540 * (drift - 1)])]);
  const path = geoPath(proj);
  const fill = interpolate(f, [1.0 * fps, 1.5 * fps], [0, 1], {extrapolateLeft: 'clamp', extrapolateRight: 'clamp'});
  const draw = interpolate(f, [1.3 * fps, 2.6 * fps], [0, 1], {extrapolateLeft: 'clamp', extrapolateRight: 'clamp', easing: ease});
  return (
    <Background style={style}>
      <svg width={1920} height={1080} style={{position: 'absolute', inset: 0}}>
        <rect width={1920} height={1080} fill={style.palette.accent} opacity={0.22} />
        {countries.map((c) => {
          const hot = targets.includes(c);
          return <path key={c.id + c.properties.name} d={path(c as any) ?? ''} stroke={style.palette.paper} strokeWidth={1.2}
            fill={hot ? red : '#CFC6B4'} fillOpacity={hot ? 0.25 + 0.75 * fill : 1} />;
        })}
        {route.length > 1 && (
          <path d={path({type: 'LineString', coordinates: route} as any) ?? ''} fill="none" stroke={style.palette.ink}
            strokeWidth={7} strokeLinecap="round" strokeDasharray="1" strokeDashoffset={1 - draw} pathLength={1} />
        )}
      </svg>
      {pins.map((q, i) => {
        const [x, y] = proj([q.lon, q.lat]) ?? [0, 0];
        const k = spring({frame: f - Math.round((1.4 + i * 0.35) * fps), fps, config: {damping: 12, stiffness: 160}});
        return (
          <div key={i} style={{position: 'absolute', left: x, top: y, transform: `translate(-50%, -100%) scale(${k})`,
            transformOrigin: '50% 100%', display: 'flex', flexDirection: 'column', alignItems: 'center'}}>
            {q.label && <div style={{background: style.palette.ink, color: style.palette.paper, fontFamily: 'Tajawal', fontWeight: 800,
              fontSize: 40, padding: '4px 18px', marginBottom: 8, direction: 'rtl', whiteSpace: 'nowrap'}}>{q.label}</div>}
            <svg width={44} height={58} viewBox="0 0 24 32"><path d="M12 0C5.4 0 0 5.2 0 11.6 0 20.3 12 32 12 32s12-11.7 12-20.4C24 5.2 18.6 0 12 0Z" fill={style.palette.ink} stroke={style.palette.paper} strokeWidth={1.5} />
              <circle cx={12} cy={11.5} r={4.6} fill={style.palette.accent} /></svg>
          </div>
        );
      })}
      {label && (
        <div style={{position: 'absolute', bottom: 80, fontFamily: style.fonts.title, fontWeight: 900, fontSize: 96, direction: 'rtl',
          background: style.palette.paper, padding: '4px 44px', boxShadow: '0 10px 24px rgba(0,0,0,.18)',
          opacity: appear(f, Math.round(0.9 * fps)), transform: `translateY(${(1 - appear(f, Math.round(0.9 * fps))) * 30}px)`}}>{label}</div>
      )}
    </Background>
  );
};
