import type {PlannerInput} from './planner';
import {StoryboardSchema, type StoryboardBeat} from './schema';
import type {SrtCue} from './types';

const compact = (text: string) => text.replace(/\s+/g, ' ').trim();
const heading = (text: string): string => {
  const value = compact(text);
  const chars = Array.from(value);
  if (chars.length <= 24) return value;
  let prefix = chars.slice(0, 23).join('');
  if (/[A-Za-z0-9]/.test(chars[23]) && /[A-Za-z0-9]$/.test(prefix)) {
    prefix = prefix.replace(/[A-Za-z0-9]+$/, '');
  }
  return `${prefix.trimEnd()}…`;
};

/** Split long cues on punctuation, without introducing numbers or process steps. */
export const splitLiteCue = (cue: SrtCue): SrtCue[] => {
  const text = compact(cue.text);
  const duration = cue.end - cue.start;
  if (text.length < 2 && duration > 6) {
    const count = Math.ceil(duration / 6);
    return Array.from({length: count}, (_, index) => ({...cue, text,
      start: Number((cue.start + duration * index / count).toFixed(3)),
      end: Number((cue.start + duration * (index + 1) / count).toFixed(3))}));
  }
  if (duration <= 6 && text.length <= 80) return [{...cue, text}];
  const clauses = text.split(/(?<=[，、；。！？,.!?;])/u).filter(Boolean);
  const midpoint = text.length / 2;
  let prefix = '';
  for (const clause of clauses) {
    if (prefix && prefix.length + clause.length > midpoint) break;
    prefix += clause;
  }
  const cut = prefix.length > 0 && prefix.length < text.length ? prefix.length : Math.floor(text.length / 2);
  if (!cut) throw new Error('Cannot split a positive-duration cue with insufficient text');
  const at = Number((cue.start + duration * cut / text.length).toFixed(3));
  return [...splitLiteCue({...cue, end: at, text: text.slice(0, cut)}),
    ...splitLiteCue({...cue, start: at, text: text.slice(cut)})];
};

export const planPublicLite = (input: PlannerInput) => {
  if (Math.abs(input.probe.video.width / input.probe.video.height - 16 / 9) > .02) throw new Error('Public-lite currently supports 16:9 horizontal footage only');
  const palette = input.publicStyle === 'paper' ? 'editorial-cream' : 'deep-ocean';
  const cues = input.cues.flatMap(splitLiteCue);
  let side: 'left' | 'right' = 'right';
  const beats: StoryboardBeat[] = cues.map((cue, index) => {
    const displayText = cue.text.replace(/^\s*(?:[一二三四五六七八九十]+|\d+)[、．.）)]\s*/u, '');
    const parts = displayText.split(/[，、；。！？,.!?;]/u).map(compact).filter(Boolean);
    const layout = index === 0 ? 'title' : parts.length >= 2 && parts.length <= 3 && cue.end - cue.start >= 2 ? 'flow' : 'card';
    if (layout === 'card') side = side === 'left' ? 'right' : 'left';
    const title = heading(parts[0] ?? cue.text);
    const direction = input.liteDirectionByCue?.[cue.index];
    if (direction && [...direction.lines, direction.eyebrow ?? '', direction.doodle?.label ?? ''].some((copy) => copy && !cue.text.includes(copy))) {
      throw new Error(`Director copy must be a literal excerpt of source cue ${cue.index}`);
    }
    return {
      id: `beat-${String(index + 1).padStart(2, '0')}`,
      start: index === 0 ? 0 : cue.start,
      end: cues[index + 1]?.start ?? input.probe.duration,
      text: cue.text, structure: 'thesis-and-proof',
      content: {structure: 'thesis-and-proof', thesis: title, reason: heading(cue.text)},
      motions: ['reveal'], placement: layout === 'card' ? side : 'full', palette,
      directorRole: index === 0 ? 'hook' : 'definition',
      reason: 'Public-lite: literal source copy, basic layout; no invented facts or stages.',
      liteLayout: layout, liteItems: layout === 'flow' ? parts : [],
      ...(direction ? {liteDirection: direction} : {}),
    };
  });
  return StoryboardSchema.parse({
    version: '2.0', edition: 'public-lite', publicStyle: input.publicStyle ?? 'dark', liteCamera: input.liteCamera ?? false,
    litePresenter: input.litePresenter ?? false,
    id: input.id, title: input.title, duration: Number(input.probe.duration.toFixed(3)),
    fps: Math.round(input.probe.video.fps || 30), width: input.probe.video.width, height: input.probe.video.height,
    captionsMode: input.captionsMode,
    source: {video: input.sourceVideo, ...(input.sourceSrt ? {srt: input.sourceSrt} : {})},
    theme: input.publicStyle === 'paper'
      ? {background: '#F3F1FA', foreground: '#201D32', accent: '#6342C7'}
      : {background: '#111827', foreground: '#F6F7FF', accent: '#91BCFF'},
    beats,
  });
};
