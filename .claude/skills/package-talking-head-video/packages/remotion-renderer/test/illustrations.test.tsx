import {renderToStaticMarkup} from 'react-dom/server';
import {describe, expect, it} from 'vitest';
import {ILLUSTRATION_SCENARIOS} from '../../core/src/schema';
import {illustrationRegistry} from '../src/illustrations';
import {SemanticDoodle} from '../src/illustrations/SemanticDoodle';
import {SourceDoodle} from '../src/illustrations/SourceDoodle';
import {PUBLIC_DOODLE_TYPES} from '../../core/src/schema';

describe('illustrationRegistry', () => {
  it('advances and settles conceptual route indicators without restarting the drawing', () => {
    const middle = renderToStaticMarkup(<SourceDoodle type="phone-mirror" progress={1} actionProgress={.5} accent="#73E4F0" ink="#F6F7FF"/>);
    const end = renderToStaticMarkup(<SourceDoodle type="phone-mirror" progress={1} actionProgress={1} accent="#73E4F0" ink="#F6F7FF"/>);
    expect(middle).toContain('data-doodle-action="source-to-result"');
    expect(middle).toContain('cx="262"');
    expect(end).toContain('cx="304"');
    expect(end).toContain('stroke-dashoffset:0');
    expect(end).toBe(renderToStaticMarkup(<SourceDoodle type="phone-mirror" progress={1} actionProgress={1} accent="#73E4F0" ink="#F6F7FF"/>));
  });
  it('supports new source diagrams and legacy drawings with normalized strokes and selected ink', () => {
    for (const type of PUBLIC_DOODLE_TYPES) {
      const markup = renderToStaticMarkup(<SourceDoodle type={type} progress={.5} accent="#58E1FF" ink="#F6F7FF"/>);
      expect(markup).toContain('stroke="#F6F7FF"');
      expect(markup).toContain('pathLength="1"');
      expect(markup).toContain('stroke-dashoffset:0.5');
      expect(markup).toBe(renderToStaticMarkup(<SourceDoodle type={type} progress={.5} accent="#58E1FF" ink="#F6F7FF"/>));
      expect(markup).not.toMatch(/<image|<text/);
    }
  });
  it('renders six deterministic transparent line illustrations', () => {
    expect(Object.keys(illustrationRegistry).sort()).toEqual([...ILLUSTRATION_SCENARIOS].sort());
    for (const name of ILLUSTRATION_SCENARIOS) {
      const Component = illustrationRegistry[name];
      const first = renderToStaticMarkup(<Component progress={0.72} accent="#5eead4" />);
      const second = renderToStaticMarkup(<Component progress={0.72} accent="#5eead4" />);
      expect(first).toBe(second);
      expect(first).toContain('viewBox="0 0 640 360"');
      expect(first).toContain('fill="none"');
      expect(first).toContain('stroke="#252933"');
      expect(first).not.toMatch(/<text|logo|watermark/i);
      expect(first.length).toBeGreaterThan(240);
    }
  });

  it('renders line, action, and outcome layers for an integrated semantic doodle', () => {
    const markup = renderToStaticMarkup(
      <SemanticDoodle
        progress={0.72}
        accent="#e97a5f"
        subject="创作者"
        action="推动流程"
        outcome="完成交付"
      />,
    );
    expect(markup).toContain('data-doodle-layer="line"');
    expect(markup).toContain('data-doodle-layer="action"');
    expect(markup).toContain('data-doodle-layer="outcome"');
    expect(markup).toContain('data-doodle-object="climber"');
    expect(markup).toContain('data-doodle-object="boulder"');
    expect(markup).toContain('fill="none"');
  });

  it('renders an explicit climber and boulder in the climb metaphor', () => {
    const ClimbBoulder = illustrationRegistry['climb-boulder'];
    const markup = renderToStaticMarkup(<ClimbBoulder progress={0.72} accent="#e97a5f"/>);
    expect(markup).toContain('data-doodle-object="climber"');
    expect(markup).toContain('data-doodle-object="boulder"');
  });
});
