import React from 'react';
import {CalculateMetadataFunction, Composition, Still} from 'remotion';
import {BigText} from './graphics/BigText';
import {Chart} from './graphics/Chart';
import {FaceFrame} from './graphics/FaceFrame';
import {Headline} from './graphics/Headline';
import {ImageCard} from './graphics/ImageCard';
import {MapZoom} from './graphics/MapZoom';
import {NumberCount} from './graphics/Number';
import {Quote} from './graphics/Quote';
import {Timeline} from './graphics/Timeline';
import {BaseProps, FPS} from './style';

const style = {palette: {paper: '#F2EBDD', ink: '#1A1A1A', accent: '#FFD400'}, fonts: {title: 'Cairo', body: 'Cairo'}, texture: 'paper'};
const meta: CalculateMetadataFunction<any> = async ({props}) => ({durationInFrames: Math.max(1, Math.round((props as BaseProps).durationSec * FPS))});

const GRAPHICS: [string, React.FC<any>, Record<string, unknown>][] = [
  ['text', BigText, {text: 'شركة إيفرغراند'}],
  ['number', NumberCount, {value: 3000000000, label: 'دولار'}],
  ['headline', Headline, {outlet: 'Reuters', title: 'إيفرغراند تعلن إفلاسها', highlight: 'إفلاسها'}],
  ['quote', Quote, {text: 'ما كنا نتوقع', who: 'مدير'}],
  ['map', MapZoom, {country: 'China', label: 'الصين'}],
  ['timeline', Timeline, {items: [{year: '1996', label: 'التأسيس'}]}],
  ['chart', Chart, {bars: [{label: '2021', value: 300}], unit: 'مليار'}],
  ['image', ImageCard, {src: 'img.png', treatment: 'paper_cutout'}],
];

export const Root: React.FC = () => (
  <>
    {GRAPHICS.map(([id, C, defaults]) => (
      <Composition key={id} id={id} component={C} width={1920} height={1080} fps={FPS} durationInFrames={60}
        defaultProps={{style, durationSec: 2, ...defaults}} calculateMetadata={meta} />
    ))}
    <Still id="face-frame-bg" component={FaceFrame as React.FC<any>} width={1920} height={1080} defaultProps={{style, durationSec: 1}} />
  </>
);
