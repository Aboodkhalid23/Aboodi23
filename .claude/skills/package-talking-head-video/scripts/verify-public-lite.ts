import {spawnSync} from 'node:child_process';
import {createHash} from 'node:crypto';
import {existsSync, mkdirSync, readFileSync, writeFileSync} from 'node:fs';
import {join, resolve} from 'node:path';
import {bundle} from '@remotion/bundler';
import {openBrowser, renderMedia, renderStill, selectComposition} from '@remotion/renderer';
import {planStoryboard} from '../packages/core/src/planner';
import {assertDirectorPlan} from '../packages/core/src/director-validation';
import {probeMedia} from '../packages/core/src/probe';
import {parseSrt} from '../packages/core/src/srt';
import {buildContactSheet, decodeEntireFile, detectBlackFrames, extractRepresentativeFrames, selectRepresentativeBeats} from './lib/artifact-qa';

// Engineering verification only: sample copy/frames are not production gate approvals.
const source = resolve(process.argv[2] || 'examples/synthetic-horizontal/input.mp4');
const srt = resolve(process.argv[3] || 'examples/synthetic-horizontal/input.srt');
const out = resolve(process.argv[4] || '.tmp/public-lite-verification');
if (!existsSync(source) || !existsSync(srt)) throw new Error('Supply matching video and SRT, or generate the synthetic fixture first');
const output = join(out, 'public-lite-dark.mp4');
if (existsSync(output)) throw new Error('Choose a new directory; an existing verification render is preserved');
const publicDir = join(out, 'public'); mkdirSync(publicDir, {recursive: true});
const prepare = spawnSync('ffmpeg', ['-v', 'error', '-y', '-i', source, '-map', '0:v:0', '-map', '0:a?',
  '-c:v', 'libx264', '-crf', '18', '-preset', 'fast', '-c:a', 'copy', join(publicDir, 'input.mp4')], {encoding: 'utf8', windowsHide: true});
if (prepare.status !== 0) throw new Error(prepare.stderr);
const cues = parseSrt(readFileSync(srt, 'utf8'));
const liteDirectionByCue = process.argv[5] ? JSON.parse(readFileSync(resolve(process.argv[5]), 'utf8')) : undefined;
const probe = probeMedia(source);
const plan = planStoryboard({id: 'public-lite-check', title: 'Public-lite verification', cues, probe,
  sourceVideo: 'input.mp4', sourceSrt: 'input.srt', captionsMode: 'burned-in', edition: 'public-lite', publicStyle: 'dark', liteCamera: true, litePresenter: true, liteDirectionByCue});
assertDirectorPlan(plan);
writeFileSync(join(out, 'storyboard.json'), JSON.stringify(plan, null, 2));
const inputProps = {storyboard: plan, cues, overlayOnly: false};
const serveUrl = await bundle({entryPoint: resolve('packages/remotion-renderer/src/index.ts'), publicDir});
const chromiumOptions = {gl: 'swangle' as const};
const browser = await openBrowser('chrome', {chromiumOptions});
try {
  const composition = await selectComposition({serveUrl, id: 'VideoPackaging', inputProps, puppeteerInstance: browser});
  for (const [i, sample] of selectRepresentativeBeats(plan).entries()) {
    await renderStill({serveUrl, composition, inputProps, frame: Math.round(sample.timestamp * plan.fps),
      output: join(out, `review-${i}.png`), imageFormat: 'png', chromiumOptions, puppeteerInstance: browser});
  }
  for (const layout of ['title', 'card', 'flow'] as const) {
    const beat = plan.beats.find((b) => b.liteLayout === layout);
    if (beat) await renderStill({serveUrl, composition, inputProps,
      frame: Math.min(composition.durationInFrames - 1, Math.round((beat.start + (beat.end - beat.start) * .6) * plan.fps)),
      output: join(out, `layout-${layout}.png`), imageFormat: 'png', chromiumOptions, puppeteerInstance: browser});
  }
  for (const beat of plan.beats) {
    for (const phase of [.12, .6, .9]) await renderStill({serveUrl, composition, inputProps,
      frame: Math.min(composition.durationInFrames - 1, Math.round((beat.start + (beat.end - beat.start) * phase) * plan.fps)),
      output: join(out, `${beat.id}-${phase}.png`), imageFormat: 'png', chromiumOptions, puppeteerInstance: browser});
  }
  for (const frame of [0, composition.durationInFrames - 1]) await renderStill({serveUrl, composition, inputProps, frame,
    output: join(out, `edge-${frame}.png`), imageFormat: 'png', chromiumOptions, puppeteerInstance: browser});
  const paper = planStoryboard({id: 'public-paper-check', title: 'Public paper verification', cues, probe,
    sourceVideo: 'input.mp4', captionsMode: 'burned-in', edition: 'public-lite', publicStyle: 'paper', liteCamera: true, litePresenter: true, liteDirectionByCue});
  const paperProps = {storyboard: paper, cues, overlayOnly: false};
  const paperComposition = await selectComposition({serveUrl, id: 'VideoPackaging', inputProps: paperProps, puppeteerInstance: browser});
  const paperBeat = paper.beats.find((beat) => beat.liteLayout === 'card') ?? paper.beats[0];
  const paperFrame = Math.round((paperBeat.start + (paperBeat.end - paperBeat.start) * .6) * paper.fps);
  await renderStill({serveUrl, composition: paperComposition, inputProps: paperProps, frame: Math.min(paperFrame, paperComposition.durationInFrames - 1),
    output: join(out, 'paper.png'), imageFormat: 'png', chromiumOptions, puppeteerInstance: browser});
  await renderMedia({serveUrl, composition, inputProps, outputLocation: output, codec: 'h264', crf: 18,
    concurrency: 2, chromiumOptions, puppeteerInstance: browser,
    onProgress: (() => {let last = -1; return ({progress}: {progress: number}) => {
      const pct = Math.floor(progress * 5) * 20;
      if (pct > last) {last = pct; process.stdout.write(`Render ${pct}%\n`);}
    };})()});
} finally {await browser.close({silent: true});}
decodeEntireFile(output);
const blackFrames = detectBlackFrames(output);
if (blackFrames.length) throw new Error(`Black-frame verification failed: ${JSON.stringify(blackFrames)}`);
const frames = extractRepresentativeFrames(output, plan, join(out, 'final-frames'));
buildContactSheet(frames, join(out, 'contact.jpg'));
const digest = (path: string) => createHash('sha256').update(readFileSync(path)).digest('hex');
writeFileSync(join(out, 'verification.json'), JSON.stringify({edition: plan.edition, sourceHash: digest(source), srtHash: digest(srt),
  outputHash: digest(output), fullDecode: 'PASS', blackFrames, layouts: [...new Set(plan.beats.map((b) => b.liteLayout))],
  paletteCount: new Set(plan.beats.map((b) => b.palette)).size, continuousPlaybackReviewed: false}, null, 2));
console.log(`Verification render complete: ${output}`);
