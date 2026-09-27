# Paper Cut workflow

## Stages

Use `intake`, `storyboard-review`, `asset-review`, `asset-production`, `assembly`, `qa`, `preview-review`, then `delivery`. Write the current stage after each completed batch. Never infer approval from file existence.

## Gate 1 — narration and storyboard

Show the final narration and compact scene plan. Every scene needs a purpose, visual metaphor, exact hero-frame composition, fixed background, candidate moving layers, text plan, duration, transition, and relevant factual/safety notes.

Passing response: explicit approval of narration and storyboard. Revision requests do not pass.

## Gate 2 — visual proof, method, and budget

Show at least one real image-model hero frame when the user needs to judge collage quality. Show every planned full-frame still, extraction, clean plate, type asset, provider, attempt cap, current usage, and first-use download. State explicitly whether a video model will be used.

The cap counts provider calls, including rejected results. Local crop, alpha extraction, masking, compositing, color correction, shadow repair, and resizing do not count as new calls.

Passing response: explicit approval of the image-led direction, provider choices, layer plan, and caps.

## Gate 3 — encoded preview

Validate the composition, inspect hero frames and transitions, then render a draft. Present the actual encoded preview with known limitations.

Passing response: explicit approval of that preview. Only then render final quality.

## Resume and revision rules

- Read state and manifests before media folders.
- Reuse approved assets whose hash and intended role are unchanged.
- Do not regenerate an asset because the chat restarted.
- Invalidate only changed scenes and dependent assets.
- If timing changes but art does not, resume from assembly.
- If narration deletes a passage, edit audio and shift downstream timing; do not regenerate approved visuals or voice unnecessarily.
- If only text styling changes, preserve scene stills and generate only the approved wordmarks.

## Provider boundary

Environment checks are free and read-only. Installation, model downloads, cloud generation, voice cloning, and paid calls require approval. Never use a video-generation model as a silent fallback.
