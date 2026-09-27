---
name: paper-cut
description: Create, resume, revise, and render editable image-led paper-cut collage explainer videos with approved AI-generated hero-frame stills, original-frame layer extraction, HyperFrames HTML/CSS/GSAP motion, narration, paper SFX, optional collage typography, and deterministic QA. Use for Paper Cut, Vox-style paper collage, code-animated collage B-roll without a video model, layered cutout animation, or turning a topic, script, article, or reference video into an editable horizontal or vertical collage explainer.
---

# Paper Cut

Make the image model responsible for art direction and hero-frame composition. Make HyperFrames responsible for motion, camera, timing, transitions, audio, and reproducibility. Do not substitute code-drawn vector art for a requested paper-collage still, and do not substitute a video model unless the user explicitly changes the method.

## Start or resume

1. Find `paper-cut-project.json`. If present, read it and `assets-manifest.json`, resume from `stage`, and preserve approvals.
2. For a new project, collect only the topic/source, target duration, aspect ratio, language, narration/caption/music requirements, and visual direction.
3. Run `scripts/check_environment.py`; report only and do not install anything silently.
4. Read [references/workflow.md](references/workflow.md) and obey all three gates.
5. Before asset production, read [references/image-led-production.md](references/image-led-production.md) and [references/asset-spec.md](references/asset-spec.md).
6. Before authoring or rendering, read the installed HyperFrames entry, core, animation, keyframes, creative, and CLI skills.

## Non-negotiable method

- Storyboard before generation. Every scene needs a precise hero-frame composition, not a generic asset list.
- Show real image-model hero frames at Gate 1/2 when the user needs to judge the look; a code vector diagram is not a substitute.
- Generate or approve the complete scene still first. Treat it as the visual source of truth.
- Extract the few layers that truly need motion from that approved still. Preserve the original background, texture, silhouettes, print registration, torn edges, and native shadows.
- Prefer local masking/matting from the original still. Generate a clean plate only when extraction leaves an unavoidable hole. Never regenerate every subject on green solely to simplify animation.
- Move only narrative focal elements. Use generated typographic cutouts and slow camera motion to add energy while the rest of the scene preserves the approved still.
- Keep the layered composition visible through the whole shot. Never swap to the untouched master still for the final second.
- Use overlapping scene transitions. Never leave an uncovered gap that can produce a white, black, or stale frame.
- Keep image-generation attempts, originals, derivatives, hashes, and approvals in `assets-manifest.json`.
- Do not call paid or quota-consuming image, voice, sound, or video providers before Gate 2 explicitly approves the provider and maximum attempts.
- Distinguish subtitles from designed keywords. “No subtitles” removes sentence-by-sentence captions; it does not remove a few editorial wordmarks unless the user also says “no on-screen text.”

## Project records

Maintain:

- `video-script.md`: approved narration and factual/rights notes;
- `storyboard.md`: timestamps, hero frames, layers, text, motion, and transitions;
- `paper-cut-project.json`: stage, approvals, providers, attempt caps/usage, timings, and delivery paths;
- `assets-manifest.json`: every original, processed derivative, generated type asset, audio asset, attempt ID, and SHA-256;
- `DESIGN.md`: shared paper stock, print process, palette, typography, shadow, and motion rules.

Read [references/storyboard-schema.md](references/storyboard-schema.md) before writing machine-readable state.

## Gate 1 — narration and storyboard

Provide:

- one-sentence thesis and factual-risk notes;
- final narration with estimated spoken duration;
- a scene table with timestamps, purpose, visual metaphor, exact hero-frame composition, fixed background, candidate moving layers, on-screen text, and transition;
- aspect ratio and visual direction;
- map, identity, copyright, financial, medical, legal, or scientific claims needing verification.

Ask for explicit approval. Record it in `approvals.storyboard`. Revision feedback does not pass the gate.

## Gate 2 — visual proof and budget

Provide:

- one representative image-model hero frame or the complete scene still set needed for visual judgment;
- the exact fixed-background versus moving-layer plan for every scene;
- which layers will be extracted from the approved still and which holes require a clean plate;
- all proposed generated typographic cutouts with exact approved text;
- image, voice, and sound providers, maximum attempts, current usage, and known cost/credit implications;
- a clear statement that no video model will be used unless approved.

Ask for explicit approval before generation. Preserve provider originals and make derivatives separately.

## Asset production

Follow [references/image-led-production.md](references/image-led-production.md).

1. Generate/approve scene hero frames in storyboard order.
2. Inspect every still at full resolution for text errors, sensitive borders, anatomy, edge debris, inconsistent paper, and unintended symbols.
3. Select only the focal motion layers. Typical choices are a sun plus heat waves, one pressure lid, one route pair, or one wordmark.
4. Extract those pixels from the approved frame with their paper edge and shadow when possible.
5. Build a clean plate by local inpainting/compositing only where the extracted subject exposes a hole.
6. Generate transparent typographic collage assets only after the exact text list is approved. Keep secondary labels code-native for legibility and editability.
7. Crop transparent margins without flattening alpha or replacing the original shadow.

Use `scripts/normalize_asset.py` only for standalone cutouts that benefit from a normalized square canvas. Do not normalize wide wordmarks or full-frame scene layers.

## Assemble in HyperFrames

Read [references/hyperframes-assembly.md](references/hyperframes-assembly.md).

- Build each approved hero frame statically before motion.
- Create a synchronous paused GSAP timeline and register it in `window.__timelines`.
- Use deterministic transforms, opacity, clip paths, and finite cycles only. No randomness, infinite repeats, async timeline construction, CSS transitions, or CSS keyframes.
- Animate the main subject first, one explanatory element second, and use a 3–6% slow push/pull/pan as background energy.
- Use generated wordmarks as transparent PNG layers with restrained slap/slide/stamp entrances. Keep text safely inside camera-scaled bounds.
- Treat the outgoing scene transition as its exit. Keep both scenes overlapped until the handoff is fully covered.

## Audio revisions

Read [references/audio-and-chatcut.md](references/audio-and-chatcut.md) when narration or sound is present.

- Treat narration timestamps as timing truth.
- For a script deletion, locate the spoken words by transcription, make a non-destructive audio cut with a short crossfade, audition the join, then shift every downstream scene, SFX, text, camera, assertion, and composition duration by the exact removed interval.
- Do not regenerate an approved voice when a clean edit is sufficient.

## Gate 3 and deterministic QA

Run:

```powershell
python scripts/validate_project.py <project-dir>
npx hyperframes lint <project-dir>
npx hyperframes check <project-dir> --samples 15 --at-transitions
```

For substantive work, also run the HyperFrames animation map and focused `keyframes --shot` diagnostics. Inspect:

- first visible frame and every hero frame;
- 0.1 seconds before/after every transition;
- all generated wordmarks under maximum camera scale;
- the narration edit join;
- final frame and final hold.

Render only a draft preview before Gate 3. After explicit approval, render delivery quality and inspect the final encoded MP4 itself. Verify resolution, duration, fps, video/audio streams, first/last frames, transition contact sheet, and run FFmpeg black-frame detection. Record the final file and QA evidence in project state.

## Completion

Deliver the editable HyperFrames project, state files, approved MP4, QA evidence, provider/attempt summary, generated originals, local derivatives, and known limitations. External upload or publication requires explicit authorization.
