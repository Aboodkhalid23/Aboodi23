# Four cumulative gates

## Gate A — source and plan

No approval flags. Write `BRIEF.md`, `SOURCE_PROBE.json`, `STORYBOARD.md`, `storyboard.json`, and `input-manifest.json`. Record hashes, media properties, every SRT cue, caption mode, semantic structures, placement, evidence status, full-screen exceptions, and risks. Do not build review visuals or render.

Show the plan to the user and stop. Approval must refer to this exact job.

## Gate B — composition inputs

Requires `--approve-gate-a --approve-gate-b`. Prepare the browser-compatible continuous source, props, and renderer project. No final video.

## Gate C — review evidence

Requires `--approve-gate-a --approve-gate-b --approve-gate-c`. Public-lite generates eight timeline samples and a contact sheet; inspect every basic layout actually used, without requiring eight structures. Historical V2 inputs retain their eight-structure checks. Review face clearance, subtitle clearance, clipping, contrast and source meaning, plus camera entry/peak/return and first/last frames. No final MP4.

## Gate D — final export

Requires all four approval flags plus `--render`. Render the final artifact, probe it, decode the entire file, detect black segments, extract eight representative frames, build a contact sheet, and write `RENDER_MANIFEST.json` with hashes and media facts.

Never describe an unrendered project, component gallery, or contact sheet as a delivered video.
