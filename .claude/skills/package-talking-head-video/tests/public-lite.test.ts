import {describe, expect, it} from 'vitest';
import {planStoryboard} from '../packages/core/src/planner';
import {splitLiteCue} from '../packages/core/src/public-lite';
import {assertDirectorPlan, validateDirectorPlan} from '../packages/core/src/director-validation';
import {StoryboardSchema} from '../packages/core/src/schema';
import {liteCameraScale, liteFlowFontSize} from '../packages/remotion-renderer/src/PublicLiteVideo';
import {buildCompositionPlan} from '../packages/remotion-renderer/src/VideoPackaging';
import {generateHyperFramesProject} from '../packages/hyperframes-adapter/src/generate';
import {selectRepresentativeBeats} from '../scripts/lib/artifact-qa';
import {editorialPalette, presenterRectAt} from '../packages/remotion-renderer/src/EditorialPresenterVideo';

const input = {
  id: 'public-test', title: 'Public test', edition: 'public-lite' as const,
  sourceVideo: 'input.mp4', sourceSrt: 'input.srt', captionsMode: 'burned-in' as const,
  probe: {duration: 40, size: 100, video: {width: 1920, height: 1080, fps: 30, codec: 'h264'}, audio: null},
  cues: Array.from({length: 10}, (_, i) => ({index: i + 1, start: i * 4, end: (i + 1) * 4, text: `当前原稿的观点${i + 1}`})),
};

describe('public-lite product boundary', () => {
  it('keeps every typography color readable against both stable surfaces', () => {
    const luminance = (hex: string) => {
      const values = [1, 3, 5].map((i) => parseInt(hex.slice(i, i + 2), 16) / 255).map((v) => v <= .04045 ? v / 12.92 : ((v + .055) / 1.055) ** 2.4);
      return values[0] * .2126 + values[1] * .7152 + values[2] * .0722;
    };
    for (const paper of [false, true]) {
      const palette = editorialPalette(paper);
      for (const foreground of [palette.ink, palette.muted, palette.main, palette.sub, palette.result]) {
        for (const background of [palette.bg, palette.panel]) {
          const a = luminance(foreground); const b = luminance(background);
          expect((Math.max(a, b) + .05) / (Math.min(a, b) + .05)).toBeGreaterThanOrEqual(4.5);
        }
      }
    }
  });
  it('keeps semantic doodle labels traceable to the spoken source', () => {
    const cues = [{index: 1, start: 0, end: 4, text: '通过手机与电脑的屏幕镜像完成展示'}];
    const plan = planStoryboard({...input, cues, probe: {...input.probe, duration: 4}, litePresenter: true,
      liteDirectionByCue: {1: {mode: 'split', lines: ['屏幕镜像'], doodle: {type: 'phone-mirror', label: '屏幕镜像'}}}});
    expect(plan.beats[0].liteDirection?.doodle?.type).toBe('phone-mirror');
    expect(() => assertDirectorPlan(plan)).not.toThrow();
    expect(() => planStoryboard({...input, cues, probe: {...input.probe, duration: 4}, litePresenter: true,
      liteDirectionByCue: {1: {mode: 'split', lines: ['屏幕镜像'], doodle: {type: 'phone-mirror', label: '未经说明的自动操作'}}}})).toThrow(/literal excerpt/);
  });
  it('rejects directed claims absent from the supplied source', () => {
    expect(() => planStoryboard({...input, litePresenter: true, liteDirectionByCue: {1: {mode: 'hero', lines: ['不存在的业务结论']}}})).toThrow(/literal excerpt/);
  });
  it('moves one presenter continuously across scene boundaries and supports deterministic seeks', () => {
    const plan = planStoryboard({...input, litePresenter: true});
    const atStart = presenterRectAt(plan, 0);
    expect(atStart.w).toBe(1920);
    const settled = presenterRectAt(plan, 110);
    expect(settled.w).toBe(760);
    const boundary = presenterRectAt(plan, 120);
    expect(boundary).toEqual(settled);
    for (const f of [135, 125, 239, 120, 135]) {
      const rect = presenterRectAt(plan, f);
      expect(rect).toEqual(presenterRectAt(plan, f));
      expect(rect.x).toBeGreaterThanOrEqual(0);
      expect(rect.x + rect.w).toBeLessThanOrEqual(1920);
      expect(rect.y + rect.h).toBeLessThanOrEqual(886);
    }
    expect(buildCompositionPlan({storyboard: plan}).videoTracks).toHaveLength(1);
  });
  it('does not enable presenter windows in SRT-only transparent output', () => {
    const plan = planStoryboard({...input, litePresenter: true});
    expect(() => buildCompositionPlan({storyboard: plan, overlayOnly: true})).toThrow(/composite/);
  });
  it('preserves short mixed-language headlines and never slices an English word', () => {
    const headline = '这个开发助手现在可以连接你的iPhone';
    const plan = planStoryboard({...input, cues: [{index: 1, start: 0, end: 4, text: headline}], probe: {...input.probe, duration: 4}});
    expect(plan.beats[0].content).toMatchObject({thesis: headline});
    const long = planStoryboard({...input, cues: [{index: 1, start: 0, end: 4, text: '接口配置方法需要查看最新版BrowserAutomationModule'}], probe: {...input.probe, duration: 4}});
    expect(long.beats[0].content).toMatchObject({thesis: '接口配置方法需要查看最新版…'});
  });
  it('keeps long source items readable and above the caption reserve', () => {
    const text = '风险'.repeat(40);
    const font = liteFlowFontSize(text, 3);
    expect(font).toBeGreaterThanOrEqual(24);
    const availableWidth = (1920 * .84 - 48) / 3 - 60;
    const lines = Math.ceil(text.length * font / availableWidth);
    expect(1080 * .4 + 104 + lines * font * 1.5).toBeLessThan(1080 * .82);
    expect(liteFlowFontSize('核心理由', 3)).toBe(40);
  });
  it('locks the supported horizontal format instead of claiming portrait face safety', () => {
    expect(() => planStoryboard({...input, probe: {...input.probe, video: {...input.probe.video, width: 1080, height: 1920}}})).toThrow(/16:9/);
    expect(planStoryboard({...input, probe: {...input.probe, video: {...input.probe.video, width: 1280, height: 720}}}).width).toBe(1280);
  });
  it('does not force eight unrelated structures into a long talking-head clip', () => {
    const plan = planStoryboard(input);
    expect(() => assertDirectorPlan(plan)).not.toThrow();
    expect(plan.beats.every((b) => b.liteLayout === 'title' || b.liteLayout === 'card')).toBe(true);
    expect(plan.beats.every((b) => !b.illustration && !b.evidence && b.motions.length === 1)).toBe(true);
    expect(new Set(plan.beats.map((b) => b.palette)).size).toBe(1);
  });

  it('offers only two public styles with no random palette rotation', () => {
    for (const publicStyle of ['dark', 'paper'] as const) {
      const plan = planStoryboard({...input, publicStyle});
      expect(plan.publicStyle).toBe(publicStyle);
      expect(new Set(plan.beats.map((b) => b.palette)).size).toBe(1);
    }
    expect(() => StoryboardSchema.parse({...planStoryboard(input), publicStyle: 'rainbow'})).toThrow();
  });

  it('splits long lists without adding facts or losing the original text', () => {
    const text = '找出遗漏信息、盲目乐观假设、不可逆成本、机会成本、最坏风险、情绪带来的认知偏差';
    const parts = splitLiteCue({index: 1, start: 0, end: 6.3, text});
    expect(parts.map((p) => p.text).join('')).toBe(text);
    expect(parts.every((p) => p.end - p.start <= 6)).toBe(true);
    expect(parts[0].start).toBe(0);
    expect(parts.at(-1)!.end).toBe(6.3);
    const plan = planStoryboard({...input, probe: {...input.probe, duration: 6.3}, cues: [{index: 1, start: 0, end: 6.3, text}]});
    for (const beat of plan.beats) for (const item of beat.liteItems ?? []) expect(text).toContain(item);
  });

  it('does not create invented pipeline steps from a single source clause', () => {
    const plan = planStoryboard({...input, cues: [{index: 1, start: 0, end: 4, text: '现在可以做出选择'}], probe: {...input.probe, duration: 4}});
    expect(plan.beats[0].liteItems).toEqual([]);
    expect(plan.beats[0].text).toBe('现在可以做出选择');
  });

  it('keeps the meaning of numbered headings instead of displaying only the list number', () => {
    const cues = [{index: 1, start: 0, end: 2, text: '口令如下'}, {index: 2, start: 2, end: 4, text: '一、全力反驳我的观点'}];
    const plan = planStoryboard({...input, cues, probe: {...input.probe, duration: 4}});
    expect(plan.beats[1].content).toMatchObject({thesis: '全力反驳我的观点'});
    expect(plan.beats[1].text).toBe('一、全力反驳我的观点');
  });

  it('can hold a short literal utterance for more than six seconds without inventing copy', () => {
    const pieces = splitLiteCue({index: 1, start: 0, end: 15, text: '好'});
    expect(pieces).toHaveLength(3);
    expect(pieces.every((p) => p.text === '好' && p.end - p.start <= 6)).toBe(true);
  });

  it('blocks invalid full-screen placement and advanced asset injection', () => {
    const plan = planStoryboard(input);
    plan.beats[1].placement = 'full';
    expect(validateDirectorPlan(plan).some((i) => i.code === 'presentation-mode-mismatch')).toBe(true);
    plan.beats[1].placement = 'left';
    plan.beats[1].illustration = {type: 'climb-boulder', label: 'not public-lite'};
    expect(() => assertDirectorPlan(plan)).toThrow(/advanced assets/);
  });

  it('samples eight real timeline points without inventing eight different layouts', () => {
    const plan = planStoryboard(input); const samples = selectRepresentativeBeats(plan);
    expect(samples).toHaveLength(8);
    expect(samples.every((f) => f.timestamp >= 0 && f.timestamp < 40)).toBe(true);
    expect(new Set(samples.map((f) => f.timestamp)).size).toBe(8);
  });

  it('has bounded seek-safe basic zoom and one continuous audio track', () => {
    const plan = planStoryboard({...input, liteCamera: true});
    expect(liteCameraScale(plan, 0)).toBe(1);
    expect(liteCameraScale(plan, 120)).toBe(1);
    expect(liteCameraScale(plan, 239)).toBe(1);
    expect(liteCameraScale(plan, 180)).toBeCloseTo(1.06);
    for (const f of [0, 125, 180, 230, 239, 180]) {
      expect(liteCameraScale(plan, f)).toBeGreaterThanOrEqual(1);
      expect(liteCameraScale(plan, f)).toBeLessThanOrEqual(1.06);
    }
    expect(buildCompositionPlan({storyboard: plan}).videoTracks).toHaveLength(1);
    expect(buildCompositionPlan({storyboard: plan}).videoTracks[0].audio).toBe(true);
    expect(buildCompositionPlan({storyboard: plan}).captionTracks).toEqual([]);
  });

  it('rejects source motion for overlays and unsupported new adapter jobs', () => {
    const plan = planStoryboard({...input, liteCamera: true});
    expect(() => buildCompositionPlan({storyboard: plan, overlayOnly: true})).toThrow(/composite/);
    expect(() => generateHyperFramesProject(plan)).toThrow(/Remotion/);
  });
});
