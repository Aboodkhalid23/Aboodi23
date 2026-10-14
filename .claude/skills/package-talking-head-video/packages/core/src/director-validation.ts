import type {Storyboard} from './schema';
import {TemplateContentSchema, type SemanticStructure} from './template-contracts';
import {PRESENTATION_MODE_BY_STRUCTURE} from './presentation-contracts';

export type DirectorIssueCode =
  | 'structure-diversity'
  | 'structure-run-too-long'
  | 'side-repeat'
  | 'invalid-full-screen-role'
  | 'evidence-missing'
  | 'content-contract'
  | 'copy-too-long'
  | 'semantic-mismatch'
  | 'presentation-mode-mismatch';

export type DirectorIssue = {code: DirectorIssueCode; message: string; beatId?: string};

const roleAllowsFullScreen = new Set(['hook', 'bridge', 'payoff', 'cta', 'evidence']);
const structureAllowsFullScreen = new Set<SemanticStructure>([
  'four-stage-pipeline',
  'before-after-scrub',
  'evidence-panel',
  'metric-odometer',
  'signal-route',
  'semantic-doodle',
  'bidirectional-flow',
]);

export const validateDirectorPlan = (storyboard: Storyboard): DirectorIssue[] => {
  if (storyboard.edition === 'public-lite') {
    const expectedPalette = storyboard.publicStyle === 'paper' ? 'editorial-cream' : 'deep-ocean';
    return storyboard.beats.flatMap((beat): DirectorIssue[] => {
      const issues: DirectorIssue[] = [];
      if (beat.liteDirection?.doodle && !storyboard.litePresenter) {
        issues.push({code: 'content-contract', beatId: beat.id, message: 'Semantic doodles require single-presenter composition'});
      }
      if (beat.liteDirection && [...beat.liteDirection.lines, beat.liteDirection.eyebrow ?? '', beat.liteDirection.doodle?.label ?? ''].some((copy) => copy && !beat.text.includes(copy))) {
        issues.push({code: 'content-contract', beatId: beat.id, message: 'Directed emphasis must use literal excerpts of the current source beat'});
      }
      if (!beat.liteLayout || beat.illustration || beat.evidence || beat.palette !== expectedPalette || beat.structure !== 'thesis-and-proof') {
        issues.push({code: 'content-contract', beatId: beat.id, message: 'Public-lite requires a basic layout and a single selected palette; advanced assets are not supported'});
      }
      if (beat.liteLayout === 'flow' && ((beat.liteItems?.length ?? 0) < 2 || (beat.liteItems?.length ?? 0) > 3)) {
        issues.push({code: 'content-contract', beatId: beat.id, message: 'Public-lite flow requires two or three source items'});
      }
      if ((beat.liteLayout === 'card') === (beat.placement === 'full')) {
        issues.push({code: 'presentation-mode-mismatch', beatId: beat.id, message: 'Cards use side lanes; titles and flows require an opaque full-screen background'});
      }
      return issues;
    });
  }
  const issues: DirectorIssue[] = [];
  const uniqueStructures = new Set(storyboard.beats.map((beat) => beat.structure)).size;
  if (storyboard.duration > 30 && uniqueStructures < 8) {
    issues.push({
      code: 'structure-diversity',
      message: `Videos over 30 seconds require eight semantically valid structures; received ${uniqueStructures}`,
    });
  }

  let runLength = 0;
  let previousStructure: SemanticStructure | undefined;
  storyboard.beats.forEach((beat, index) => {
    runLength = beat.structure === previousStructure ? runLength + 1 : 1;
    previousStructure = beat.structure;
    if (runLength === 3) {
      issues.push({
        code: 'structure-run-too-long',
        beatId: beat.id,
        message: `${beat.structure} appears more than twice consecutively`,
      });
    }

    const parsedContent = TemplateContentSchema.safeParse(beat.content);
    if (!parsedContent.success || beat.content.structure !== beat.structure) {
      issues.push({
        code: 'content-contract',
        beatId: beat.id,
        message: `Content does not satisfy ${beat.structure}`,
      });
    }
    if (beat.structure === 'evidence-panel' && !beat.evidence) {
      issues.push({
        code: 'evidence-missing',
        beatId: beat.id,
        message: 'Evidence panels require a real source asset',
      });
    }
    if (
      beat.placement === 'full'
      && !roleAllowsFullScreen.has(beat.directorRole)
      && !structureAllowsFullScreen.has(beat.structure)
    ) {
      issues.push({
        code: 'invalid-full-screen-role',
        beatId: beat.id,
        message: `${beat.structure}/${beat.directorRole} cannot use a full-screen treatment`,
      });
    }
    if (PRESENTATION_MODE_BY_STRUCTURE[beat.structure] === 'opaque-full-screen' && beat.placement !== 'full') {
      issues.push({
        code: 'presentation-mode-mismatch',
        beatId: beat.id,
        message: `${beat.structure} crosses the presenter center and must use an opaque full-screen treatment`,
      });
    }

    const previous = storyboard.beats[index - 1];
    if (
      previous
      && beat.placement !== 'full'
      && previous.placement !== 'full'
      && beat.placement === previous.placement
    ) {
      issues.push({
        code: 'side-repeat',
        beatId: beat.id,
        message: 'Consecutive ordinary overlays use the same presenter-safe lane',
      });
    }
  });
  return issues;
};

export const assertDirectorPlan = (storyboard: Storyboard): void => {
  const issues = validateDirectorPlan(storyboard);
  if (issues.length === 0) return;
  const details = issues
    .map((issue) => `${issue.code}${issue.beatId ? `(${issue.beatId})` : ''}: ${issue.message}`)
    .join('; ');
  throw new Error(`Director plan rejected: ${details}`);
};
