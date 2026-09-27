import React, {useMemo} from 'react';
import {geoMercator, geoPath} from 'd3-geo';
import {feature} from 'topojson-client';
import world from 'world-atlas/countries-110m.json';
import {interpolate, useCurrentFrame} from 'remotion';
import {appear, Background, BaseProps, ease, FPS} from '../style';

type Feat = {type: 'Feature'; id: string; properties: {name: string}; geometry: any};
// eslint-disable-next-line @typescript-eslint/no-explicit-any
const countries = (feature(world as any, (world as any).objects.countries) as any).features as Feat[];

export const MapZoom: React.FC<BaseProps & {country: string; label: string}> = ({style, durationSec, country, label}) => {
  const f = useCurrentFrame();
  const target = countries.find((c) => c.properties.name.toLowerCase() === country.toLowerCase() || c.id === country);
  const t = interpolate(f, [0, durationSec * FPS * 0.7], [0, 1], {extrapolateRight: 'clamp', easing: ease});
  const [wide, close] = useMemo(() => {
    const w = geoMercator().fitExtent([[60, 60], [1860, 1020]], {type: 'Sphere'} as any);
    const c = geoMercator().fitExtent([[460, 200], [1460, 900]], (target ?? {type: 'Sphere'}) as any);
    return [w, c];
  }, [target]);
  const proj = geoMercator()
    .scale(interpolate(t, [0, 1], [wide.scale(), close.scale()]))
    .translate([interpolate(t, [0, 1], [wide.translate()[0], close.translate()[0]]),
      interpolate(t, [0, 1], [wide.translate()[1], close.translate()[1]])]);
  const path = geoPath(proj);
  return (
    <Background style={style}>
      <svg width={1920} height={1080} style={{position: 'absolute', inset: 0}}>
        {countries.map((c) => (
          <path key={c.id + c.properties.name} d={path(c as any) ?? ''} stroke={style.palette.paper} strokeWidth={1.5}
            fill={c === target ? style.palette.accent : style.palette.ink} fillOpacity={c === target ? 1 : 0.18} />
        ))}
      </svg>
      <div style={{position: 'absolute', bottom: 90, fontFamily: style.fonts.title, fontWeight: 900, fontSize: 96,
        background: style.palette.paper, padding: '4px 40px', opacity: appear(f, durationSec * FPS * 0.4)}}>{label}</div>
    </Background>
  );
};
