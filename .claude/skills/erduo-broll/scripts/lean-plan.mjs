#!/usr/bin/env node

import { lstat, readFile } from 'node:fs/promises';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const PLAN_FILE = 'broll-plan.json';
const ROUTES = new Set(['native', 'provided', 'search', 'generate', 'mixed']);
const SAFE_SHOT_ID = /^[A-Za-z][A-Za-z0-9_-]{0,63}$/u;

function fail(message) {
  throw new Error(`Invalid lean plan: ${message}`);
}

function relativeFile(projectDir, locator, label) {
  if (typeof locator !== 'string' || !locator.trim()) fail(`${label} must be a non-empty project-relative path`);
  if (path.isAbsolute(locator)) fail(`${label} must be project-relative`);
  const resolved = path.resolve(projectDir, locator);
  const relative = path.relative(projectDir, resolved);
  if (!relative || relative === '..' || relative.startsWith(`..${path.sep}`) || path.isAbsolute(relative)) {
    fail(`${label} must stay inside the project`);
  }
  return resolved;
}

async function sourceFile(projectDir, locator, label) {
  const file = relativeFile(projectDir, locator, label);
  let metadata;
  try {
    metadata = await lstat(file);
  } catch {
    fail(`${label} is missing: ${locator}`);
  }
  if (!metadata.isFile()) fail(`${label} must be a regular file: ${locator}`);
  return file;
}

function parseTimestamp(value) {
  const match = /^(\d{2,}):(\d{2}):(\d{2})[,.](\d{3})$/u.exec(value);
  if (!match) return null;
  const [, hours, minutes, seconds, milliseconds] = match.map(Number);
  if (minutes > 59 || seconds > 59) return null;
  return (((hours * 60) + minutes) * 60 + seconds) * 1_000 + milliseconds;
}

/** Parse ordinary SRT into stable, one-based cue ids. */
export function parseOriginalSrt(text) {
  if (typeof text !== 'string') fail('original SRT is not text');
  const blocks = text.replace(/^\uFEFF/u, '').replaceAll('\r\n', '\n').trim().split(/\n{2,}/u).filter(Boolean);
  if (blocks.length === 0) fail('original SRT has no cues');

  const cues = blocks.map((block, index) => {
    const lines = block.split('\n').map((line) => line.trimEnd());
    const timingIndex = lines.findIndex((line) => line.includes('-->'));
    if (timingIndex < 0) fail(`SRT cue ${index + 1} has no timing line`);
    if (timingIndex > 1) fail(`SRT cue ${index + 1} has unexpected content before its timing`);
    if (timingIndex === 1 && !/^\d+$/u.test(lines[0].trim())) fail(`SRT cue ${index + 1} has an invalid cue number`);
    const match = /^\s*(\S+)\s+-->\s+(\S+)(?:\s+.*)?$/u.exec(lines[timingIndex]);
    if (!match) fail(`SRT cue ${index + 1} has invalid timing`);
    const startMs = parseTimestamp(match[1]);
    const endMs = parseTimestamp(match[2]);
    if (startMs === null || endMs === null || endMs <= startMs) fail(`SRT cue ${index + 1} has invalid timing`);
    return { id: index + 1, startMs, endMs, text: lines.slice(timingIndex + 1).join('\n').trim() };
  });

  for (let index = 1; index < cues.length; index += 1) {
    if (cues[index].startMs < cues[index - 1].endMs) fail(`SRT cues ${index} and ${index + 1} overlap or are out of order`);
  }
  return cues;
}

function requiredText(value, label) {
  if (typeof value !== 'string' || !value.trim()) fail(`${label} must be a non-empty string`);
}

function positiveInteger(value, label, { min = 1, max = Number.MAX_SAFE_INTEGER } = {}) {
  if (!Number.isInteger(value) || value < min || value > max) fail(`${label} must be an integer from ${min} to ${max}`);
}

function validatePlan(plan, { projectDir, cues }) {
  if (!plan || typeof plan !== 'object' || Array.isArray(plan)) fail('plan must be a JSON object');
  if (plan.schemaVersion !== 'lean-1') fail('schemaVersion must be lean-1');
  requiredText(plan.title, 'title');
  if (!plan.inputs || typeof plan.inputs !== 'object' || Array.isArray(plan.inputs)) fail('inputs must be an object');
  requiredText(plan.inputs.srt, 'inputs.srt');
  requiredText(plan.inputs.design, 'inputs.design');
  if (!plan.profile || typeof plan.profile !== 'object' || Array.isArray(plan.profile)) fail('profile must be an object');
  positiveInteger(plan.profile.width, 'profile.width', { min: 64, max: 16_384 });
  positiveInteger(plan.profile.height, 'profile.height', { min: 64, max: 16_384 });
  positiveInteger(plan.profile.fps, 'profile.fps', { min: 1, max: 120 });
  if (plan.profile.width % 2 || plan.profile.height % 2) {
    fail('profile.width and profile.height must be even for h264 output');
  }
  if (!Array.isArray(plan.shots) || plan.shots.length === 0) fail('shots must be a non-empty array');

  const cueById = new Map(cues.map((cue) => [cue.id, cue]));
  const referencedCues = new Set();
  const ids = new Set();
  const shots = plan.shots.map((shot, index) => {
    const label = `shots[${index}]`;
    if (!shot || typeof shot !== 'object' || Array.isArray(shot)) fail(`${label} must be an object`);
    requiredText(shot.id, `${label}.id`);
    if (!SAFE_SHOT_ID.test(shot.id)) fail(`${label}.id must be an ASCII filename-safe identifier`);
    if (ids.has(shot.id)) fail(`${label}.id duplicates ${shot.id}`);
    ids.add(shot.id);
    positiveInteger(shot.startMs, `${label}.startMs`, { min: 0 });
    positiveInteger(shot.endMs, `${label}.endMs`, { min: 1 });
    if (shot.endMs <= shot.startMs) fail(`${label}.endMs must be greater than startMs`);
    if (!Array.isArray(shot.cueIds) || shot.cueIds.some((id) => !Number.isInteger(id))) fail(`${label}.cueIds must be an array of cue ids`);
    if (new Set(shot.cueIds).size !== shot.cueIds.length) fail(`${label}.cueIds must not repeat a cue id`);
    for (const cueId of shot.cueIds) {
      const cue = cueById.get(cueId);
      if (!cue) fail(`${label}.cueIds references missing SRT cue ${cueId}`);
      if (cue.endMs <= shot.startMs || cue.startMs >= shot.endMs) fail(`${label}.cueIds cue ${cueId} does not overlap this shot`);
      referencedCues.add(cueId);
    }
    for (const cue of cues) {
      if (cue.endMs > shot.startMs && cue.startMs < shot.endMs && !shot.cueIds.includes(cue.id)) {
        fail(`${label}.cueIds must include overlapping SRT cue ${cue.id}`);
      }
    }
    requiredText(shot.intent, `${label}.intent`);
    requiredText(shot.subject, `${label}.subject`);
    if (!shot.material || typeof shot.material !== 'object' || Array.isArray(shot.material) || !ROUTES.has(shot.material.route)) {
      fail(`${label}.material.route must be native, provided, search, generate, or mixed`);
    }
    requiredText(shot.composition, `${label}.composition`);
    relativeFile(projectDir, shot.composition, `${label}.composition`);
    return shot;
  });

  if (shots[0].startMs !== 0) fail('shot coverage must start at 0');
  for (let index = 1; index < shots.length; index += 1) {
    if (shots[index].startMs !== shots[index - 1].endMs) fail(`shot coverage has a gap or overlap between ${shots[index - 1].id} and ${shots[index].id}`);
  }
  const finalCueEndMs = cues.at(-1).endMs;
  if (shots.at(-1).endMs !== finalCueEndMs) fail(`shot coverage must end at final SRT cue end ${finalCueEndMs}ms`);
  for (const cue of cues) {
    if (!referencedCues.has(cue.id)) fail(`SRT cue ${cue.id} is not assigned to a shot`);
  }
  return plan;
}

/**
 * Load a concise, agent-authored lean plan and its authoritative source inputs.
 * The returned `cues` use one-based SRT order, regardless of printed SRT numbering.
 */
export async function loadLeanPlan(project) {
  const projectDir = path.resolve(project);
  const planFile = path.join(projectDir, PLAN_FILE);
  let plan;
  try {
    plan = JSON.parse(await readFile(planFile, 'utf8'));
  } catch (error) {
    fail(error instanceof SyntaxError ? `${PLAN_FILE} is not valid JSON` : `${PLAN_FILE} is missing or unreadable`);
  }
  if (!plan?.inputs || typeof plan.inputs !== 'object') fail('inputs must be an object');
  const srtFile = await sourceFile(projectDir, plan.inputs.srt, 'inputs.srt');
  const designFile = await sourceFile(projectDir, plan.inputs.design, 'inputs.design');
  const cues = parseOriginalSrt(await readFile(srtFile, 'utf8'));
  validatePlan(plan, { projectDir, cues });
  return { projectDir, planFile, srtFile, designFile, cues, plan };
}

async function main(argv) {
  if (argv.length !== 2 || argv[0] !== '--project' || !argv[1]) {
    throw new Error('Usage: node scripts/lean-plan.mjs --project <dir>');
  }
  const { plan, cues } = await loadLeanPlan(argv[1]);
  process.stdout.write(`Lean plan valid: ${plan.title} — ${plan.shots.length} shots, ${cues.length} cues, ${cues.at(-1).endMs}ms\n`);
}

if (process.argv[1] && path.resolve(process.argv[1]) === fileURLToPath(import.meta.url)) {
  main(process.argv.slice(2)).catch((error) => {
    process.stderr.write(`${error.message}\n`);
    process.exitCode = 1;
  });
}
