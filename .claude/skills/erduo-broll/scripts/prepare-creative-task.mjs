#!/usr/bin/env node

import { lstat, mkdir, readFile, writeFile } from 'node:fs/promises';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

import { loadLeanPlan } from './lean-plan.mjs';

const ROLES = new Set(['director', 'creator', 'reviewer']);
const SKILL_ROOT = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');

function shellQuote(value) {
  return `'${String(value).replaceAll("'", "'\\''")}'`;
}

async function kind(file) {
  try {
    const info = await lstat(file);
    if (info.isFile()) return 'file';
    if (info.isDirectory()) return 'directory';
    return 'other';
  } catch (error) {
    if (error?.code === 'ENOENT') return 'missing';
    throw error;
  }
}

async function requireFile(file, label) {
  if (await kind(file) !== 'file') throw new Error(`${label} is missing or is not a regular file: ${file}`);
  return path.resolve(file);
}

async function requireMaterial(file, label) {
  if (!['file', 'directory'].includes(await kind(file))) throw new Error(`${label} is missing: ${file}`);
  return path.resolve(file);
}

async function requireProject(project) {
  if (typeof project !== 'string' || !project.trim()) throw new Error('--project is required');
  const projectDir = path.resolve(project);
  if (await kind(projectDir) !== 'directory') throw new Error(`project directory is missing: ${projectDir}`);
  return projectDir;
}

function resolveInput(projectDir, locator) {
  return path.isAbsolute(locator) ? path.resolve(locator) : path.resolve(projectDir, locator);
}

function parseShots(value) {
  if (value == null) return null;
  const ids = String(value).split(',').map((item) => item.trim()).filter(Boolean);
  if (!ids.length || new Set(ids).size !== ids.length) throw new Error('--shots must name unique shot ids');
  return ids;
}

function selectShots(plan, requested) {
  if (requested == null) return [...plan.shots];
  const indexById = new Map(plan.shots.map((shot, index) => [shot.id, index]));
  for (const id of requested) if (!indexById.has(id)) throw new Error(`unknown shot ${id}`);
  const indexes = requested.map((id) => indexById.get(id));
  for (let index = 1; index < indexes.length; index += 1) {
    if (indexes[index] !== indexes[index - 1] + 1) {
      throw new Error('--shots must follow the plan in one contiguous range');
    }
  }
  return requested.map((id) => plan.shots[indexById.get(id)]);
}

function ensureSeparateCompositions(shots) {
  const owners = new Map();
  for (const shot of shots) {
    const owner = owners.get(shot.composition);
    if (owner) throw new Error(`${owner} and ${shot.id} share composition ${shot.composition}; creative ownership cannot be split safely`);
    owners.set(shot.composition, shot.id);
  }
}

function shotSummary(shots, { includeComposition }) {
  const lines = ['| Shot | Boundary | Cues | Intent | Subject |', '|---|---:|---|---|---|'];
  if (includeComposition) {
    lines[0] += ' Composition |';
    lines[1] += '---|';
  }
  for (const shot of shots) {
    const safe = (value) => String(value).replaceAll('|', '\\|').replaceAll('\n', ' ');
    let row = `| ${safe(shot.id)} | ${shot.startMs}–${shot.endMs} ms | ${shot.cueIds.join(', ')} | ${safe(shot.intent)} | ${safe(shot.subject)} |`;
    if (includeComposition) row += ` ${safe(path.resolve(shot.projectDir, shot.composition))} |`;
    lines.push(row);
  }
  return lines.join('\n');
}

function unique(values) {
  return [...new Set(values)];
}

async function creatorMedia(projectDir, shots) {
  const files = [];
  for (const shot of shots) {
    const locators = [
      ...(Array.isArray(shot.material?.locators) ? shot.material.locators : []),
      ...(Array.isArray(shot.material?.provenance)
        ? shot.material.provenance.map((item) => item?.locator).filter(Boolean)
        : []),
    ];
    for (const locator of locators) {
      if (typeof locator !== 'string' || !locator.trim() || /^[a-z][a-z0-9+.-]*:/iu.test(locator)) continue;
      const file = resolveInput(projectDir, locator);
      files.push(await requireMaterial(file, `${shot.id} material`));
    }
  }
  return unique(files);
}

async function readRenderIndex(projectDir, requestedQuality) {
  const candidates = requestedQuality ? [requestedQuality] : ['final', 'draft'];
  const present = [];
  for (const quality of candidates) {
    const file = path.join(projectDir, 'lean-renders', quality, 'index.json');
    if (await kind(file) === 'file') present.push({ quality, file });
  }
  if (present.length > 1) {
    throw new Error('both draft and final previews exist; use --quality to select the render just produced');
  }
  for (const { quality, file } of present) {
    let index;
    try {
      index = JSON.parse(await readFile(file, 'utf8'));
    } catch {
      throw new Error(`render index is not valid JSON: ${file}`);
    }
    if (index?.schemaVersion !== 'lean-render-index-1' || !Array.isArray(index.shots)) {
      throw new Error(`render index has an unsupported shape: ${file}`);
    }
    return { file, index, quality };
  }
  throw new Error(`render review is not ready: missing ${path.join(projectDir, 'lean-renders', '{final,draft}', 'index.json')}`);
}

async function prepareDirector(projectDir, options) {
  const srtFile = await requireFile(resolveInput(projectDir, options.srt ?? 'input/original.srt'), 'original SRT');
  const designFile = await requireFile(resolveInput(projectDir, options.design ?? 'input/design.md'), 'design input');
  const roleGuide = await requireFile(path.join(SKILL_ROOT, 'references', 'creative-director.md'), 'director role guide');
  const leanProduction = await requireFile(path.join(SKILL_ROOT, 'references', 'lean-production.md'), 'lean production guide');
  const visualDirection = await requireFile(path.join(SKILL_ROOT, 'references', 'lean-visual-direction.md'), 'visual direction guide');
  const motionPatterns = path.join(SKILL_ROOT, 'references', 'motion-patterns.md');
  const optional = await kind(motionPatterns) === 'file' ? [motionPatterns] : [];
  const knownAssetIndex = path.join(projectDir, 'assets', 'index.md');
  if (await kind(knownAssetIndex) === 'file') optional.push(knownAssetIndex);
  const outputs = [
    path.join(projectDir, 'broll-plan.json'),
    path.join(projectDir, 'direction.md'),
    path.join(projectDir, 'direction', '<shot-id>.md'),
  ];
  const command = `${shellQuote(process.execPath)} ${shellQuote(path.join(SKILL_ROOT, 'scripts', 'lean-plan.mjs'))} --project ${shellQuote(projectDir)}`;
  const readFiles = [srtFile, designFile, roleGuide, leanProduction, visualDirection, ...optional];
  const body = `# Creative task — director

This file prepares a small handoff. It does not sandbox the host context, start a model, or change global settings or permissions.

## Read only what this role needs

${readFiles.map((file) => `- ${file}`).join('\n')}

Original SRT: ${srtFile}
Original design: ${designFile}

## Responsibility

Direct the complete film from the original inputs. Create a compact lean-1 plan, one shared direction and one short card per planned shot. Parent prepares the shared material index; report any actual material gap without inventing local files. Each shot card states its starting picture, meaningful change, settled result, incoming seam, and outgoing seam without prescribing hard coordinates.

Outputs:
${outputs.map((file) => `- ${file}`).join('\n')}

Do not create compositions, render media, copy the Skill, load production history, or invent missing evidence or source files.

## Return this validation command to Parent after writing the plan

${command}
`;
  return { body, shots: [], readFiles };
}

async function prepareCreator(projectDir, requested) {
  const loaded = await loadLeanPlan(projectDir);
  const selected = selectShots(loaded.plan, requested);
  ensureSeparateCompositions(loaded.plan.shots);
  const shots = selected.map((shot) => ({ ...shot, projectDir }));
  const first = loaded.plan.shots.indexOf(selected[0]);
  const last = loaded.plan.shots.indexOf(selected.at(-1));
  const contextShots = loaded.plan.shots.slice(Math.max(0, first - 1), Math.min(loaded.plan.shots.length, last + 2));
  const directionFile = await requireFile(path.join(projectDir, 'direction.md'), 'shared direction');
  const assetIndex = await requireFile(path.join(projectDir, 'assets', 'index.md'), 'shared material index');
  const directionCards = [];
  for (const shot of contextShots) {
    directionCards.push(await requireFile(path.join(projectDir, 'direction', `${shot.id}.md`), `${shot.id} direction card`));
  }
  const roleGuide = await requireFile(path.join(SKILL_ROOT, 'references', 'creative-creator.md'), 'creator role guide');
  const leanProduction = await requireFile(path.join(SKILL_ROOT, 'references', 'lean-production.md'), 'lean production guide');
  const media = await creatorMedia(projectDir, selected);
  const readFiles = unique([
    loaded.srtFile, loaded.designFile, roleGuide, leanProduction,
    directionFile, assetIndex, ...directionCards, ...media,
  ]);
  const ids = selected.map(({ id }) => id);
  const command = `${shellQuote(process.execPath)} ${shellQuote(path.join(SKILL_ROOT, 'scripts', 'lean-render.mjs'))} --project ${shellQuote(projectDir)} --quality draft --shots ${shellQuote(ids.join(','))}`;
  const body = `# Creative task — creator ${ids.join('–')}

This file prepares a small handoff. It does not sandbox the host context, start a model, or change global settings or permissions.

## Read only what this role needs

${readFiles.map((file) => `- ${file}`).join('\n')}

Original SRT: ${loaded.srtFile}
Original design: ${loaded.designFile}

The first and last direction cards outside the assigned range are seam context only. Do not edit their shots.

## Owned chapter

${shotSummary(shots, { includeComposition: true })}

Edit only the listed composition files. Keep plan timing, cue ownership, factual meaning, shared direction, material provenance, and neighboring seams intact. Choose the actual composition and motion independently inside those boundaries. Do not inspect other compositions, prior task logs, conversation history, or unrelated Skill files.

The parent performs mechanical rendering. After edits, return the owned shot ids and this exact command:

${command}
`;
  return { body, shots: ids, readFiles };
}

async function prepareReviewer(projectDir, requested, quality) {
  const loaded = await loadLeanPlan(projectDir);
  const requestedShots = selectShots(loaded.plan, requested);
  const requestedIds = requested == null ? null : requestedShots.map(({ id }) => id);
  const directionFile = await requireFile(path.join(projectDir, 'direction.md'), 'shared direction');
  const roleGuide = await requireFile(path.join(SKILL_ROOT, 'references', 'creative-reviewer.md'), 'reviewer role guide');
  const render = await readRenderIndex(projectDir, quality);
  const planIds = new Set(loaded.plan.shots.map(({ id }) => id));
  for (const shot of render.index.shots) {
    if (!planIds.has(shot.id)) throw new Error(`render index contains shot not present in the current plan: ${shot.id}`);
  }
  const previewLocator = render.index.preview?.output;
  if (typeof previewLocator !== 'string' || !previewLocator.trim()) throw new Error(`render index has no preview output: ${render.file}`);
  const preview = await requireFile(resolveInput(projectDir, previewLocator), 'render preview');
  const available = render.index.shots.filter((shot) => shot.sheet && ['ready', 'rendered', 'reused'].includes(shot.status));
  const reviewShots = requestedIds == null ? available : available.filter((shot) => requestedIds.includes(shot.id));
  if (requestedIds != null) {
    const ready = new Set(reviewShots.map(({ id }) => id));
    const missing = requestedIds.filter((id) => !ready.has(id));
    if (missing.length) throw new Error(`requested review shots are not rendered and ready: ${missing.join(', ')}`);
  }
  if (!reviewShots.length) throw new Error(`render review is not ready: ${render.file} has no reviewable shot sheets`);
  const sheets = [];
  for (const shot of reviewShots) sheets.push(await requireFile(resolveInput(projectDir, shot.sheet), `${shot.id} review sheet`));
  // The raw index contains cost/operation metrics. Parent reads it; the reviewer
  // receives the resolved scope and media without those judging cues.
  const readFiles = unique([loaded.srtFile, loaded.designFile, roleGuide, directionFile, preview, ...sheets]);
  const ids = reviewShots.map(({ id }) => id);
  const completeness = render.index.complete && available.length === loaded.plan.shots.length ? 'complete' : 'partial';
  const missingIds = loaded.plan.shots.map(({ id }) => id).filter((id) => !available.some((shot) => shot.id === id));
  const command = `${shellQuote(process.execPath)} ${shellQuote(path.join(SKILL_ROOT, 'scripts', 'lean-render.mjs'))} --project ${shellQuote(projectDir)} --quality ${shellQuote(render.quality)} --shots ${shellQuote(ids.join(','))}`;
  const summaries = loaded.plan.shots
    .filter((shot) => ids.includes(shot.id))
    .map((shot) => ({ ...shot, projectDir }));
  const body = `# Creative task — reviewer

This file prepares a small handoff. It does not sandbox the host context, start a model, or change global settings or permissions.

## Read only what this role needs

${readFiles.map((file) => `- ${file}`).join('\n')}

Original SRT: ${loaded.srtFile}
Original design: ${loaded.designFile}

## Review scope

Render state: **${completeness} ${render.quality} preview**. Reviewable shots: ${ids.join(', ')}.${missingIds.length ? ` Missing or stale shots: ${missingIds.join(', ')}.` : ''}

${shotSummary(summaries, { includeComposition: false })}

Judge the real sheets and moving preview against the original meaning and shared direction. Report concrete visual faults and the smallest useful revision to the original creator. Do not open or edit composition source, task logs, production history, or cost records; do not render.

Write the concise decision to ${path.join(projectDir, 'creative-tasks', 'reviewer', 'review.md')}.

Command to return to the original creator after requested repairs:

${command}
`;
  return { body, shots: ids, readFiles };
}

export async function prepareCreativeTask(options) {
  const projectDir = await requireProject(options.project);
  if (!ROLES.has(options.role)) throw new Error('--role must be director, creator, or reviewer');
  if (options.quality != null && (options.role !== 'reviewer' || !['draft', 'final'].includes(options.quality))) {
    throw new Error('--quality draft|final is only valid for reviewer');
  }
  const requested = parseShots(options.shots);
  if (options.role === 'director' && requested != null) throw new Error('--shots is not valid for director');
  if (options.role !== 'director' && (options.srt != null || options.design != null)) {
    throw new Error('--srt and --design are only valid for director');
  }
  const prepared = options.role === 'director'
    ? await prepareDirector(projectDir, options)
    : options.role === 'creator'
      ? await prepareCreator(projectDir, requested)
      : await prepareReviewer(projectDir, requested, options.quality);
  const suffix = options.role === 'creator' ? `creator-${prepared.shots.join('-')}` : options.role;
  const taskDir = path.join(projectDir, 'creative-tasks', suffix);
  await mkdir(taskDir, { recursive: true });
  const taskFile = path.join(taskDir, 'TASK.md');
  await writeFile(taskFile, prepared.body, 'utf8');
  return {
    taskFile,
    role: options.role,
    shots: prepared.shots,
    readFiles: prepared.readFiles,
    note: 'Handoff prepared; host context is not sandboxed.',
  };
}

function parseArgs(argv) {
  const options = {};
  for (let index = 0; index < argv.length; index += 2) {
    const name = argv[index];
    const value = argv[index + 1];
    if (!name?.startsWith('--') || value === undefined || value.startsWith('--')) throw new Error(`invalid argument ${name ?? ''}`);
    const key = name.slice(2);
    if (!['project', 'role', 'shots', 'srt', 'design', 'quality'].includes(key)) throw new Error(`unknown option --${key}`);
    if (options[key] !== undefined) throw new Error(`duplicate option --${key}`);
    options[key] = value;
  }
  return options;
}

async function main() {
  const result = await prepareCreativeTask(parseArgs(process.argv.slice(2)));
  process.stdout.write(`${JSON.stringify(result)}\n`);
}

if (process.argv[1] && path.resolve(process.argv[1]) === fileURLToPath(import.meta.url)) {
  main().catch((error) => {
    process.stderr.write(`${error.message}\n`);
    process.exitCode = 1;
  });
}
