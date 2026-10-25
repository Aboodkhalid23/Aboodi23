#!/usr/bin/env node

import { createHash } from 'node:crypto';
import { lstat, mkdir, readFile, readdir, rename, rm, writeFile } from 'node:fs/promises';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

import { loadLeanPlan } from './lean-plan.mjs';
import { applicationDataDir, HYPERFRAMES_VERSION, hyperframesCliPath } from './lib.mjs';
import { commandFailure, hashFile, probeAndDecode, requireRegularFile, runCommand } from './shot-media-lib.mjs';

const CACHE_SCHEMA = 'lean-render-cache-2';
const INDEX_SCHEMA = 'lean-render-index-1';
const OUTPUT_DIRECTORY = 'lean-renders';
const NON_RENDER_DIRECTORIES = new Set([
  '.cache', '.git', '.hyperframes', 'coverage', 'docs', 'logs', 'node_modules',
  'output', 'outputs', 'renders', 'temp', 'tmp', OUTPUT_DIRECTORY,
]);

function stableJson(value) {
  if (Array.isArray(value)) return `[${value.map(stableJson).join(',')}]`;
  if (value && typeof value === 'object') {
    return `{${Object.keys(value).sort().map((key) => `${JSON.stringify(key)}:${stableJson(value[key])}`).join(',')}}`;
  }
  return JSON.stringify(value);
}

function identity(value) {
  return createHash('sha256').update(stableJson(value)).digest('hex');
}

function portable(locator) {
  return locator.split(path.sep).join('/');
}

function isInside(root, candidate) {
  const relative = path.relative(root, candidate);
  return relative === '' || (!relative.startsWith('..') && !path.isAbsolute(relative));
}

function resolveInside(root, locator, label) {
  if (typeof locator !== 'string' || !locator || path.isAbsolute(locator)) {
    throw new Error(`${label} must be a non-empty project-relative path`);
  }
  const resolved = path.resolve(root, locator);
  if (!isInside(root, resolved) || resolved === root) throw new Error(`${label} escapes the project`);
  return resolved;
}

function defaultHyperframes() {
  return hyperframesCliPath(applicationDataDir());
}

async function pathKind(target) {
  try {
    const info = await lstat(target);
    if (info.isSymbolicLink()) return 'symlink';
    if (info.isFile()) return 'file';
    if (info.isDirectory()) return 'directory';
    return 'other';
  } catch (error) {
    if (error?.code === 'ENOENT') return 'missing';
    throw error;
  }
}

async function readJsonIfPresent(file) {
  try {
    return JSON.parse(await readFile(file, 'utf8'));
  } catch (error) {
    if (error?.code === 'ENOENT') return null;
    if (error instanceof SyntaxError) return null;
    throw error;
  }
}

async function replaceFile(temporary, destination) {
  await mkdir(path.dirname(destination), { recursive: true });
  if (await pathKind(destination) === 'missing') {
    await rename(temporary, destination);
    return;
  }
  const backup = `${destination}.previous-${process.pid}-${Date.now()}`;
  await rename(destination, backup);
  try {
    await rename(temporary, destination);
    await rm(backup, { force: true });
  } catch (error) {
    await rename(backup, destination).catch(() => {});
    throw error;
  }
}

async function atomicJson(file, value) {
  const temporary = path.join(path.dirname(file), `.${path.basename(file)}.${process.pid}-${Date.now()}.tmp`);
  await mkdir(path.dirname(file), { recursive: true });
  try {
    await writeFile(temporary, `${JSON.stringify(value, null, 2)}\n`, { flag: 'wx' });
    await replaceFile(temporary, file);
  } finally {
    await rm(temporary, { force: true });
  }
}

function draftDimension(value) {
  return Math.max(2, Math.floor(value / 4) * 2);
}

function renderProfile(plan, quality) {
  if (quality === 'final') {
    return { width: plan.profile.width, height: plan.profile.height, fps: plan.profile.fps, encoderQuality: 'high' };
  }
  return {
    width: draftDimension(plan.profile.width),
    height: draftDimension(plan.profile.height),
    fps: Math.min(plan.profile.fps, 15),
    encoderQuality: 'draft',
  };
}

function frameWindow(shot, fps) {
  // Pinned HyperFrames rounds every non-integral shot duration up. Adjacent
  // global boundaries prevent those independent extra frames accumulating.
  const startFrame = Math.round(shot.startMs * fps / 1_000);
  const endFrame = Math.round(shot.endMs * fps / 1_000);
  if (endFrame <= startFrame) throw new Error(`${shot.id} is shorter than one frame at ${fps}fps`);
  return { startFrame, endFrame, frameCount: endFrame - startFrame };
}

const RESOLUTIONS = new Map([
  ['1920x1080', 'landscape'], ['1080x1920', 'portrait'], ['1080x1080', 'square'],
  ['3840x2160', 'landscape-4k'], ['2160x3840', 'portrait-4k'], ['2160x2160', 'square-4k'],
]);

function resolutionFor(profile) {
  return RESOLUTIONS.get(`${profile.width}x${profile.height}`) ?? null;
}

async function visitFiles(directory, root, excluded, output) {
  for (const entry of (await readdir(directory, { withFileTypes: true })).sort((a, b) => a.name.localeCompare(b.name))) {
    const absolute = path.join(directory, entry.name);
    const locator = portable(path.relative(root, absolute));
    const parts = locator.split('/');
    if (excluded.has(locator) || parts.some((part) => NON_RENDER_DIRECTORIES.has(part))) continue;
    if (entry.isDirectory()) await visitFiles(absolute, root, excluded, output);
    else if (entry.isFile() && !/\.(?:log|md|tmp|txt)$/iu.test(entry.name)) output.add(locator);
    else if (entry.isSymbolicLink()) throw new Error(`dependency ${locator} must not be a symlink`);
  }
}

function localReferences(body) {
  const values = new Set();
  const patterns = [
    /(?:src|href|poster|data-composition-src)\s*=\s*["']([^"']+)["']/giu,
    /url\(\s*["']?([^"')]+)["']?\s*\)/giu,
    /(?:import|export)\s+(?:[^"']*?\s+from\s+)?["']([^"']+)["']/gu,
    /(?:import|require)\(\s*["']([^"']+)["']\s*\)/gu,
  ];
  for (const pattern of patterns) {
    for (const match of body.matchAll(pattern)) values.add(match[1]);
  }
  return values;
}

async function addReferenceClosure(project, initial, files) {
  const pending = [...initial];
  const visited = new Set();
  while (pending.length) {
    const locator = pending.pop();
    if (visited.has(locator)) continue;
    visited.add(locator);
    const absolute = path.join(project, locator);
    if (await pathKind(absolute) !== 'file') continue;
    files.add(locator);
    if (!/\.(?:html?|css|[cm]?js|mjs|json|svg)$/iu.test(locator)) continue;
    const body = await readFile(absolute, 'utf8');
    for (let reference of localReferences(body)) {
      if (/^(?:[a-z][a-z0-9+.-]*:|#|data:|\/\/)/iu.test(reference)) continue;
      reference = reference.split(/[?#]/u, 1)[0];
      if (!reference) continue;
      let decoded;
      try { decoded = decodeURIComponent(reference); } catch { decoded = reference; }
      const target = decoded.startsWith('/')
        ? path.resolve(project, `.${decoded}`)
        : path.resolve(path.dirname(absolute), decoded);
      if (!isInside(project, target)) continue;
      const kind = await pathKind(target);
      if (kind === 'file') pending.push(portable(path.relative(project, target)));
      if (kind === 'directory') {
        const discovered = new Set();
        await visitFiles(target, project, new Set(), discovered);
        for (const found of discovered) pending.push(found);
      }
    }
  }
}

async function hashBindings(project, files) {
  const bindings = [];
  for (const entry of [...files].sort()) {
    const absolute = path.join(project, entry);
    await requireRegularFile(absolute, `dependency ${entry}`);
    bindings.push({ path: entry, sha256: await hashFile(absolute) });
  }
  return bindings;
}

async function sharedDependencyBindings(loaded) {
  const { projectDir: project, planFile, srtFile, designFile, plan } = loaded;
  const excluded = new Set([portable(path.relative(project, planFile)), ...plan.shots.map(({ composition }) => composition)]);
  const files = new Set();
  await visitFiles(project, project, excluded, files);
  files.add(portable(path.relative(project, srtFile)));
  files.add(portable(path.relative(project, designFile)));
  return hashBindings(project, files);
}

async function dependencyIdentity({ loaded, shot, quality, profile, hyperframesVersion, sharedBindings }) {
  const project = loaded.projectDir;
  const files = new Set();
  await addReferenceClosure(project, [shot.composition], files);
  for (const locator of shot.material?.locators ?? []) {
    if (typeof locator === 'string') await addReferenceClosure(project, [locator], files);
  }
  for (const item of shot.material?.provenance ?? []) {
    if (typeof item?.locator === 'string') await addReferenceClosure(project, [item.locator], files);
  }
  const sharedPaths = new Set(sharedBindings.map(({ path: locator }) => locator));
  const shotBindings = await hashBindings(project, new Set([...files].filter((locator) => !sharedPaths.has(locator))));
  return identity({
    renderer: CACHE_SCHEMA, hyperframesVersion, quality, profile,
    shot: {
      id: shot.id, startMs: shot.startMs, endMs: shot.endMs, cueIds: shot.cueIds,
      intent: shot.intent, subject: shot.subject, material: shot.material, composition: shot.composition,
    },
    dependencies: [...sharedBindings, ...shotBindings],
  });
}

function relativeOutput(project, file) {
  return portable(path.relative(project, file));
}

async function validCachedShot(project, record, expectedIdentity) {
  if (!record || record.dependencyIdentity !== expectedIdentity || record.decode !== 'passed') return false;
  const media = resolveInside(project, record.output, 'cached output');
  const sheet = resolveInside(project, record.sheet, 'cached sheet');
  if (await pathKind(media) !== 'file' || await pathKind(sheet) !== 'file') return false;
  return await hashFile(media) === record.sha256 && await hashFile(sheet) === record.sheetSha256;
}

function assertMedia(facts, profile, window, label) {
  const frameMs = 1_000 / profile.fps;
  const duration = window.frameCount / profile.fps * 1_000;
  if (facts.codec !== 'h264') throw new Error(`${label} codec must be h264`);
  if (facts.width !== profile.width || facts.height !== profile.height) {
    throw new Error(`${label} raster ${facts.width}x${facts.height} differs from ${profile.width}x${profile.height}`);
  }
  if (!Number.isFinite(facts.fps) || Math.abs(facts.fps - profile.fps) > 1e-6) {
    throw new Error(`${label} fps ${facts.fps} differs from ${profile.fps}`);
  }
  if (facts.frameCount !== window.frameCount) {
    throw new Error(`${label} has ${facts.frameCount} frames; expected ${window.frameCount}`);
  }
  if (!Number.isFinite(facts.durationMs) || Math.abs(facts.durationMs - duration) > frameMs + 1) {
    throw new Error(`${label} duration ${facts.durationMs}ms differs from ${duration}ms`);
  }
  if (facts.audioStreams !== 0) throw new Error(`${label} must be silent`);
}

async function probeFacts(file, { ffprobe, runner, cwd, label }) {
  const result = await runner({
    executable: ffprobe,
    args: ['-v', 'error', '-count_frames', '-show_streams', '-show_format', '-of', 'json', file],
    cwd,
  });
  if (result.code !== 0) throw commandFailure(`${label} FFprobe`, result);
  let value;
  try { value = JSON.parse(result.stdout); } catch { throw new Error(`${label} FFprobe returned invalid JSON`); }
  const video = (value.streams ?? []).filter(({ codec_type: type }) => type === 'video');
  if (video.length !== 1) throw new Error(`${label} must contain exactly one video stream`);
  const stream = video[0];
  const fpsText = stream.avg_frame_rate ?? stream.r_frame_rate;
  const fpsMatch = /^([0-9]+)\/([1-9][0-9]*)$/u.exec(String(fpsText ?? ''));
  const fps = fpsMatch ? Number(fpsMatch[1]) / Number(fpsMatch[2]) : Number(fpsText);
  const frameCount = Number(stream.nb_read_frames ?? stream.nb_frames);
  return {
    codec: stream.codec_name,
    width: Number(stream.width), height: Number(stream.height), fps, frameCount,
    durationMs: Number.isFinite(frameCount) && Number.isFinite(fps) && fps > 0
      ? frameCount / fps * 1_000
      : Number(value.format?.duration ?? stream.duration) * 1_000,
    audioStreams: (value.streams ?? []).filter(({ codec_type: type }) => type === 'audio').length,
  };
}

function tempFile(directory, label, extension) {
  return path.join(directory, `.${label}.${process.pid}-${Date.now()}-${Math.random().toString(16).slice(2)}${extension}`);
}

async function renderShot({ loaded, shot, quality, profile, window, dependency, output, sheet, hyperframes, ffmpeg, ffprobe, runner }) {
  const project = loaded.projectDir;
  const raw = tempFile(path.dirname(output), `${shot.id}-raw`, '.mp4');
  const converted = tempFile(path.dirname(output), `${shot.id}-converted`, '.mp4');
  const nextSheet = tempFile(path.dirname(sheet), `${shot.id}-sheet`, '.png');
  await Promise.all([mkdir(path.dirname(output), { recursive: true }), mkdir(path.dirname(sheet), { recursive: true })]);
  try {
    const args = [
      'render', project, '--composition', shot.composition,
      '--fps', String(profile.fps), '--quality', profile.encoderQuality,
      '--strict', '--no-best-effort', '--output', raw,
    ];
    const resolution = quality === 'final' ? resolutionFor(profile) : null;
    if (resolution) args.push('--resolution', resolution);
    const rendered = await runner({ executable: hyperframes, args, cwd: project });
    if (rendered.code !== 0) throw commandFailure(`${shot.id} HyperFrames render`, rendered);
    await requireRegularFile(raw, `${shot.id} raw render`);

    let candidate = raw;
    const rawFacts = await probeFacts(raw, { ffprobe, runner, cwd: project, label: shot.id });
    const frameMs = 1_000 / profile.fps;
    if (rawFacts.codec !== 'h264' || rawFacts.audioStreams !== 0
      || !Number.isFinite(rawFacts.fps) || Math.abs(rawFacts.fps - profile.fps) > 1e-6
      || !Number.isInteger(rawFacts.frameCount) || rawFacts.frameCount < 1
      || !Number.isFinite(rawFacts.durationMs)
      || Math.abs(rawFacts.durationMs - (shot.endMs - shot.startMs)) > frameMs + 1) {
      throw new Error(`${shot.id} raw render does not match its planned time or codec`);
    }
    if (quality === 'final' && (rawFacts.width !== profile.width || rawFacts.height !== profile.height)) {
      throw new Error(`${shot.id} final raster ${rawFacts.width}x${rawFacts.height} differs from ${profile.width}x${profile.height}`);
    }
    if (rawFacts.frameCount < window.frameCount) {
      throw new Error(`${shot.id} raw render has ${rawFacts.frameCount} frames; expected at least ${window.frameCount}`);
    }
    const needsScale = rawFacts.width !== profile.width || rawFacts.height !== profile.height;
    const needsTrim = rawFacts.frameCount !== window.frameCount;
    if (needsScale || needsTrim) {
      const filters = [];
      if (needsTrim) filters.push(`trim=end_frame=${window.frameCount}`, 'setpts=PTS-STARTPTS');
      if (needsScale) filters.push(`scale=${profile.width}:${profile.height}`);
      const finalQuality = quality === 'final' ? ['slow', '15'] : ['ultrafast', '28'];
      const normalized = await runner({
        executable: ffmpeg,
        args: [
          '-v', 'error', '-nostdin', '-i', raw, '-an', '-vf', filters.join(','),
          '-c:v', 'libx264', '-preset', finalQuality[0], '-crf', finalQuality[1], '-pix_fmt', 'yuv420p',
          '-movflags', '+faststart', converted,
        ],
        cwd: project,
      });
      if (normalized.code !== 0) throw commandFailure(`${shot.id} frame normalization`, normalized);
      await requireRegularFile(converted, `${shot.id} normalized render`);
      candidate = converted;
    }

    const facts = await probeAndDecode(candidate, { ffmpeg, ffprobe, runner, cwd: project, shotId: shot.id });
    assertMedia(facts, profile, window, shot.id);
    const frameCount = facts.frameCount;
    const frames = frameCount >= 6
      ? Array.from({ length: 6 }, (_, index) => Math.round((frameCount - 1) * index / 5))
      : null;
    const filter = frames
      ? `select=${frames.map((frame) => `eq(n\\,${frame})`).join('+')},scale=320:-2,tile=3x2:padding=8:margin=8`
      : `fps=6/${frameCount / profile.fps},scale=320:-2,tile=3x2:padding=8:margin=8`;
    const checked = await runner({
      executable: ffmpeg,
      args: ['-v', 'error', '-nostdin', '-i', candidate, '-vf', filter, '-frames:v', '1', nextSheet],
      cwd: project,
    });
    if (checked.code !== 0) throw commandFailure(`${shot.id} six-frame sheet`, checked);
    await requireRegularFile(nextSheet, `${shot.id} six-frame sheet`);

    await replaceFile(candidate, output);
    await replaceFile(nextSheet, sheet);
    return {
      dependencyIdentity: dependency,
      ...window,
      output: relativeOutput(project, output), sha256: await hashFile(output), facts, decode: 'passed',
      sheet: relativeOutput(project, sheet), sheetSha256: await hashFile(sheet),
    };
  } finally {
    await Promise.all([rm(raw, { force: true }), rm(converted, { force: true }), rm(nextSheet, { force: true })]);
  }
}

function escapeConcat(file) {
  return file.replaceAll("'", "'\\''");
}

async function validCachedPreview(project, preview, expectedIdentity) {
  if (!preview || preview.identity !== expectedIdentity || preview.decode !== 'passed') return false;
  const file = resolveInside(project, preview.output, 'cached preview');
  return await pathKind(file) === 'file' && await hashFile(file) === preview.sha256;
}

async function assemblePreview({ project, records, profile, previewFile, previewIdentity, ffmpeg, ffprobe, runner }) {
  const temporary = tempFile(path.dirname(previewFile), 'preview', '.mp4');
  const concat = tempFile(path.dirname(previewFile), 'preview-concat', '.txt');
  await mkdir(path.dirname(previewFile), { recursive: true });
  try {
    const files = records.map((record) => resolveInside(project, record.output, 'preview shot output'));
    await writeFile(concat, `${files.map((file) => `file '${escapeConcat(file)}'`).join('\n')}\n`, { flag: 'wx' });
    const result = await runner({
      executable: ffmpeg,
      args: [
        '-v', 'error', '-nostdin', '-f', 'concat', '-safe', '0', '-i', concat, '-an',
        '-c:v', 'libx264', '-preset', 'veryfast', '-crf', '22', '-pix_fmt', 'yuv420p',
        '-movflags', '+faststart', temporary,
      ],
      cwd: project,
    });
    if (result.code !== 0) throw commandFailure('lean preview assembly', result);
    await requireRegularFile(temporary, 'lean preview');
    const facts = await probeAndDecode(temporary, { ffmpeg, ffprobe, runner, cwd: project, shotId: 'lean preview' });
    const previewWindow = { frameCount: records.reduce((sum, record) => sum + record.frameCount, 0) };
    assertMedia(
      facts,
      profile,
      previewWindow,
      'lean preview',
    );
    await replaceFile(temporary, previewFile);
    return {
      identity: previewIdentity, output: relativeOutput(project, previewFile), sha256: await hashFile(previewFile),
      facts, decode: 'passed', shotIds: records.map(({ id }) => id),
    };
  } finally {
    await Promise.all([rm(temporary, { force: true }), rm(concat, { force: true })]);
  }
}

async function identifyHyperframes(hyperframes, runner, cwd) {
  if (!path.isAbsolute(hyperframes)) throw new Error('--hyperframes must be an absolute CLI path');
  const result = await runner({ executable: hyperframes, args: ['--version'], cwd });
  if (result.code !== 0) throw commandFailure('HyperFrames version check', result);
  const version = result.stdout.trim().split(/\s+/u).at(-1);
  if (version !== HYPERFRAMES_VERSION) {
    throw new Error(`HyperFrames ${HYPERFRAMES_VERSION} is required; found ${version || 'unknown'}`);
  }
  return version;
}

export async function runLeanRender({
  project, quality, shots = null, hyperframes = defaultHyperframes(), ffmpeg = 'ffmpeg', ffprobe = 'ffprobe',
  runner = runCommand, planLoader = loadLeanPlan, onOperation = () => {}, now = () => Date.now(),
}) {
  if (!['draft', 'final'].includes(quality)) throw new Error('quality must be draft or final');
  if (typeof project !== 'string' || !project.trim()) throw new Error('project is required');
  const started = now();
  const projectDir = path.resolve(project);
  const loaded = await planLoader(projectDir);
  const plan = loaded.plan;
  const orderedShots = [...plan.shots].sort((left, right) => left.startMs - right.startMs || left.id.localeCompare(right.id));
  for (const shot of orderedShots) {
    if (!/^[A-Za-z0-9][A-Za-z0-9._-]{0,63}$/u.test(shot.id)) {
      throw new Error(`unsafe shot id ${shot.id}`);
    }
  }
  const requestedIds = shots == null
    ? orderedShots.map(({ id }) => id)
    : Array.isArray(shots) ? shots : String(shots).split(',').map((value) => value.trim()).filter(Boolean);
  if (!requestedIds.length || new Set(requestedIds).size !== requestedIds.length) throw new Error('--shots must name unique shot ids');
  const shotById = new Map(orderedShots.map((shot) => [shot.id, shot]));
  for (const id of requestedIds) if (!shotById.has(id)) throw new Error(`unknown shot ${id}`);
  const compositionAvailable = new Map();
  for (const shot of orderedShots) {
    const composition = resolveInside(projectDir, shot.composition, `${shot.id} composition`);
    const available = await pathKind(composition) === 'file';
    compositionAvailable.set(shot.id, available);
    if (requestedIds.includes(shot.id) && !available) {
      throw new Error(`${shot.id} composition is missing or is not a regular file`);
    }
  }

  const version = await identifyHyperframes(hyperframes, runner, projectDir);
  const profile = renderProfile(plan, quality);
  const qualityRoot = path.join(projectDir, OUTPUT_DIRECTORY, quality);
  const cacheFile = path.join(qualityRoot, '.cache.json');
  const indexFile = path.join(qualityRoot, 'index.json');
  const previewFile = path.join(qualityRoot, 'preview.mp4');
  const previous = await readJsonIfPresent(cacheFile);
  const cache = previous?.schemaVersion === CACHE_SCHEMA ? previous : { schemaVersion: CACHE_SCHEMA, shots: {} };
  cache.shots ??= {};

  const sharedBindings = await sharedDependencyBindings(loaded);
  const dependencies = new Map();
  for (const shot of orderedShots) {
    if (!compositionAvailable.get(shot.id)) continue;
    dependencies.set(shot.id, await dependencyIdentity({
      loaded, shot, quality, profile, hyperframesVersion: version, sharedBindings,
    }));
  }

  const states = new Map();
  const metrics = { requested: requestedIds.length, rendered: 0, reused: 0, sheetsGenerated: 0, previewGenerated: 0, previewReused: 0 };
  for (const shot of orderedShots) {
    if (!compositionAvailable.get(shot.id)) {
      states.set(shot.id, { status: 'source-missing' });
      continue;
    }
    const cached = cache.shots[shot.id];
    const valid = await validCachedShot(projectDir, cached, dependencies.get(shot.id));
    states.set(shot.id, valid ? { status: 'ready', record: cached } : { status: cached ? 'stale' : 'missing' });
  }

  for (const id of requestedIds) {
    const shot = shotById.get(id);
    const state = states.get(id);
    if (state.status === 'ready') {
      state.status = 'reused';
      metrics.reused += 1;
      await onOperation({ type: 'shot-reused', shotId: id, elapsedMs: now() - started });
      continue;
    }
    await onOperation({ type: 'shot-render-start', shotId: id, elapsedMs: now() - started });
    const output = path.join(qualityRoot, 'shots', `${id}.mp4`);
    const sheet = path.join(qualityRoot, 'checks', `${id}.png`);
    const shotStarted = now();
    const record = await renderShot({
      loaded, shot, quality, profile, window: frameWindow(shot, profile.fps),
      dependency: dependencies.get(id), output, sheet,
      hyperframes, ffmpeg, ffprobe, runner,
    });
    record.id = id;
    cache.shots[id] = record;
    states.set(id, { status: 'rendered', record });
    metrics.rendered += 1;
    metrics.sheetsGenerated += 1;
    cache.updatedAt = new Date().toISOString();
    await atomicJson(cacheFile, cache);
    await onOperation({ type: 'shot-rendered', shotId: id, elapsedMs: now() - shotStarted });
  }

  const ready = orderedShots
    .map((shot) => ({ id: shot.id, state: states.get(shot.id) }))
    .filter(({ state }) => ['ready', 'rendered', 'reused'].includes(state.status))
    .map(({ id, state }) => ({ id, ...state.record }));
  if (!ready.length) throw new Error('no current shot outputs are available for preview');
  const complete = ready.length === orderedShots.length;
  const previewIdentity = identity({
    quality, profile,
    shots: ready.map(({ id, sha256 }) => ({ id, sha256, startMs: shotById.get(id).startMs, endMs: shotById.get(id).endMs })),
  });
  if (await validCachedPreview(projectDir, cache.preview, previewIdentity)) {
    metrics.previewReused = 1;
    await onOperation({ type: 'preview-reused', elapsedMs: now() - started });
  } else {
    cache.preview = await assemblePreview({
      project: projectDir, records: ready, profile, previewFile, previewIdentity, ffmpeg, ffprobe, runner,
    });
    metrics.previewGenerated = 1;
    await onOperation({ type: 'preview-generated', elapsedMs: now() - started });
  }

  const generatedAt = new Date().toISOString();
  const index = {
    schemaVersion: INDEX_SCHEMA,
    planSchemaVersion: plan.schemaVersion,
    title: plan.title,
    quality,
    complete,
    deliveryStatus: complete
      ? (quality === 'final' ? 'final-render' : 'draft-preview')
      : 'partial-preview',
    profile: { width: profile.width, height: profile.height, fps: profile.fps },
    shots: orderedShots.map((shot, order) => {
      const state = states.get(shot.id);
      return {
        order: order + 1, id: shot.id, startMs: shot.startMs, endMs: shot.endMs,
        status: state.status,
        ...(state.record ? {
          startFrame: state.record.startFrame,
          endFrame: state.record.endFrame,
          frameCount: state.record.frameCount,
          output: state.record.output, sha256: state.record.sha256,
          sheet: state.record.sheet, sheetSha256: state.record.sheetSha256,
          decode: state.record.decode,
        } : {}),
      };
    }),
    preview: cache.preview,
    generatedAt,
  };
  cache.updatedAt = generatedAt;
  await atomicJson(cacheFile, cache);
  await atomicJson(indexFile, index);
  metrics.elapsedMs = now() - started;
  return {
    status: complete ? (quality === 'final' ? 'final-ready' : 'draft-ready') : 'partial-preview',
    complete,
    project: projectDir, quality,
    outputRoot: qualityRoot, index: indexFile, preview: previewFile,
    metrics,
  };
}

function parseArgs(argv) {
  const options = {};
  for (let index = 0; index < argv.length; index += 2) {
    const name = argv[index];
    const value = argv[index + 1];
    if (!name?.startsWith('--') || value === undefined || value.startsWith('--')) throw new Error(`invalid argument ${name ?? ''}`);
    const key = name.slice(2);
    if (!['project', 'quality', 'shots', 'hyperframes', 'ffmpeg', 'ffprobe'].includes(key)) throw new Error(`unknown option --${key}`);
    if (options[key] !== undefined) throw new Error(`duplicate option --${key}`);
    options[key] = value;
  }
  return options;
}

async function main() {
  const options = parseArgs(process.argv.slice(2));
  if (!options.project) throw new Error('--project is required');
  if (!options.quality) throw new Error('--quality is required');
  const result = await runLeanRender({
    project: options.project,
    quality: options.quality,
    shots: options.shots,
    hyperframes: options.hyperframes,
    ffmpeg: options.ffmpeg,
    ffprobe: options.ffprobe,
  });
  process.stdout.write(`${JSON.stringify(result)}\n`);
}

if (process.argv[1] && path.resolve(process.argv[1]) === fileURLToPath(import.meta.url)) {
  main().catch((error) => {
    process.stderr.write(`${error.message}\n`);
    process.exitCode = 1;
  });
}
