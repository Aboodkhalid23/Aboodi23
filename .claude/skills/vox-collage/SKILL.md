---
name: xingchen-vox-collage
description: Create or revise Xingchen scenes in an original Vox-inspired editorial paper-collage language with separate image assets, code-owned typography and evidence graphics, deterministic Remotion motion, hero-frame lookdev, and anti-PPT visual QA. Use when the user explicitly asks for Vox-style, editorial collage, paper-cut explainer, kinetic editorial typography, collage B-roll, or wants to reconstruct this visual grammar inside a Xingchen video.
---

# Xingchen Vox Collage

Own the selected editorial-collage visual branch. Preserve the approved Xingchen thesis, proof, scene job, timing, and safe regions. Do not become a second story router or render truth.

## Route The Picture

Choose one route per scene:

- `editorial-explainer` (default): generate or source independent assets, keep exact text and evidence code-native, and animate deterministically in Remotion.
- `metaphor-broll`: use one visual proposition, a focused cast of object groups, and a concise assembly or transformation. Prefer deterministic layers; allow generated image-to-video only when exact layout, identity, text, counts, and proof do not matter.
- `source-collage`: preserve real source geometry, crop it into editorial sheets or cutouts, and add code-owned annotation. Never present generated media as evidence.

Do not call a paper texture or a Ken Burns move a Vox scene. The screen must reveal, compare, trace, build, transform, inspect, or resolve something the narration cannot show alone.

## Read Inputs

Read only the current scene truth:

- accepted script or real-audio timing;
- `scene_id`, `beat_id`, `knowledge_change`, `dominant_visual`, `motion_action`, `proof_ref`, `safe_region`, and `semantic_relation`;
- selected whole-film art direction and any explicit reference-style record;
- existing source media and project-local assets.

If the project runs under `xingchen-next`, keep its `Content Lock` and `Preview Lock`. A style bake-off, asset check, or hero-frame choice is a working decision, not another approval lock.

## Explore Before You Commit

Before locking routes or shot cards, write one short creative exploration in free-form prose — a paragraph, not a form. In your own words, answer:

- Which visual routes could carry this film, and which one did you choose and why?
- What material opportunities does the subject offer — papers, inks, objects, archives, or textures the argument can physically live in?
- Where might the film become sparse or repetitive, and what would rescue those passages?
- How does motion carry meaning here — what does each entrance, transformation, or settle explain — instead of decorating?

This exploration is an authoring default, not validator input: no schema, no required line count, no score. Keep it with the project's working notes and let it steer the shot cards. For a copyable visual-ambition brief and a worked example, read [creative-exploration.md](references/creative-exploration.md).

## Lock The Shot Before Assets

For every scene, write a shot card before prompting or cutting: the visual proposition, focal order, subject scale, facing, common ground or deliberate suspension, occlusion order, and subtitle-safe lane. Treat a change of shot as a new composition; do not reuse a character blindly when its scale, facing, or narrative role changes.

Keep moving people and props out of the environment plate. A matching character sheet is allowed as a staging reference, but split accepted actors into individual alpha-checked files before animation. The settled layout must make the narrative hierarchy legible while completely still.

## Build The Visual Contract

Create `visual/vox/` with:

- `DESIGN.md`: material world, palette, type roles, edge language, shadow logic, texture, motion character, anti-reference;
- `scene-spec.json`: scene jobs, hero frames, independent layers, camera, transitions, checkpoints, and rendered review evidence;
- `assets.json`: every source, generated, local, and code-native asset with status and provenance;
- `prompts/`: one prompt per generated bitmap asset;
- `lookdev/`: intended-resolution hero frames and playable critical clips;
- `renders/`: branch previews and visual evidence.

Initialize the structure:

```powershell
python .\scripts\init_vox_branch.py <project-root> --slug <slug> --width 1920 --height 1080 --fps 30
```

Read [visual-language.md](references/visual-language.md) while writing `DESIGN.md`. Read [asset-layer-contract.md](references/asset-layer-contract.md) before generating or cutting assets.

## Design The Hero Frame First

Hero-frame-first is the authoring default, not a universal hard gate. For the hook, hardest explanation or proof, and payoff:

1. Write one visual proposition, not a list of nouns.
2. Sketch two genuinely different spatial mechanisms using the same accepted scene job.
3. Select the strongest composition and construct its settled hero frame at intended resolution.
4. Verify focal hierarchy, negative space, proof scale, subtitle safety, and material consistency.
5. Decompose the accepted frame into independent actors before animating.

Do not approve motion from a prompt or storyboard. Render the hero frame and then a playable clip.

When a scene's meaning exists only in motion — a traversal, a transformation, a settle — a settled still cannot carry the argument. In that case, review a representative in-motion frame extracted from the playable clip and record a one-sentence rationale next to it stating why the still cannot stand in. This exception never relaxes source-collage readability: real source proof must stay legible and undistorted in whatever frame is reviewed.

Before strict validation, each scene must point to real review artifacts:

```json
{
  "hero_frame": {
    "description": "...",
    "focal_order": ["..."],
    "subtitle_safe_region": "...",
    "path": "visual/vox/lookdev/s01-hero.png",
    "input_fingerprint": "<evidence_input_fingerprint>"
  },
  "playable_clip": {
    "path": "visual/vox/lookdev/s01-preview.mp4",
    "audio_ref": "audio/narration.wav",
    "input_fingerprint": "<evidence_input_fingerprint>",
    "phone_reviewed": true,
    "phone_review_ref": "visual/vox/lookdev/s01-phone-review.md",
    "checkpoint_paths": {
      "entry": "visual/vox/lookdev/s01-entry.png",
      "settled": "visual/vox/lookdev/s01-settled.png",
      "exit": "visual/vox/lookdev/s01-exit.png"
    }
  }
}
```

## Generate And Prepare Assets

Use `$imagegen` for raster plates, isolated cutouts, props, archival-style illustrations, or textures. Follow its built-in-first policy.

- Generate each independently moving or reusable actor as a separate asset.
- Keep headlines, Chinese text, dates, numbers, charts, maps, labels, captions, and proof highlights out of generated bitmaps.
- Request isolated opaque cutouts on a removable flat chroma background when practical; use the installed ImageGen removal helper and inspect alpha edges.
- Use a generated actor sheet only to establish a coherent cast; split it into independently positioned cutouts and reject it as a final animated plate.
- Use a reference sheet only for a recurring person, place, or object that must stay recognizable across scenes.
- Save accepted assets inside the project. Do not reference `$CODEX_HOME/generated_images` from Remotion.
- Give every `reviewed` or `approved` code-native asset a project-relative `path`. When a path uses `file.html#fragment`, that literal DOM/SVG `id` must exist in the file.
- Preserve real source crops without non-uniform scaling or invented content.

For a dense existing poster, prefer regenerating or extracting separate actors. Manual bounding-box extraction is a last-mile repair, not the default production method.

## Compile Deterministic Motion

Load `remotion-render-adapter` for formal Remotion work. Copy the neutral primitives when the project lacks an equivalent library:

```powershell
python .\scripts\install_remotion_primitives.py <existing-remotion-project-dir>
```

Use the copied primitives as ingredients, not a scene template. Compose a film-specific picture.

Apply paper-native verbs:

- `slide`, `reveal`, `peel`, `pivot`, `stamp`, `drop`, `slap`, `settle`, `trace`, `wipe`;
- shallow depth-separated parallax;
- mask and crop reveals;
- finite grain, dust, scanner-light, or paper flutter;
- short impact shake only on a meaningful landing.

Build the settled layout first. Animate backward from final coordinates to hidden or off-frame states. Preserve the final hero frame until the transition begins.

Assign every independent actor a `primary`, `secondary`, `tertiary`, or `ambient` motion tier. Let primary actors travel and land most strongly, secondary actors arrive after the focal read is established, tertiary actors move least, and the plate remain almost still. Do not give three or more independent actors the same entrance frame unless the scene contract explains why their simultaneous arrival carries meaning.

Keep motion deterministic: derive every value from the Remotion frame and stable seeds. Do not use wall-clock time, unseeded randomness, asynchronous timeline construction, or infinite repeats.

Read [remotion-scene-contract.md](references/remotion-scene-contract.md) for layer props, motion timing, camera rules, and handoff fields.

## Prevent The PPT Failure

Block the branch when any of these is true:

- the dominant visual is a centered title or generic card;
- every scene repeats the same torn rectangle, grid, or left-text/right-image layout;
- narration is pasted onto the canvas;
- a flattened poster is described as independent object animation;
- charts, maps, or evidence are decorative placeholders;
- labels, connector lines, glow, or particles are being added to rescue a weak picture mechanism;
- a generated image contains essential Chinese text or audited numbers;
- a template selects scene type by index instead of scene meaning;
- a scale-only move is described as camera choreography.
- subtitles or labels are the only changing layer across an explanatory interval;
- the essential semantic actor becomes a postage stamp in the phone downsample while decorative space dominates;
- an adjacent-scene cut abandons material, object, rail, aperture, color-field, or motion continuity without recording an intentional reset.

Allow quiet frames and hard cuts. More layers and more movement are not automatic improvements.

## Validate And Review

While the branch is still being authored, validate its contract with pending evidence allowed:

```powershell
python .\scripts\validate_vox_branch.py <project-root> --allow-pending
```

`--allow-pending` converts missing hero-frame and playable-clip evidence into warnings. A `PASS` with warnings means the structure is usable; it is not visual approval.

The validator can only confirm that a review artifact exists, decodes, and matches its contract. It cannot confirm that anyone watched the clip at phone size, and it cannot judge readability or aesthetics — that judgment stays human. A `phone_review_ref` path or `phone_reviewed: true` flag proves the artifact is present, never that a human looked at it or approved the picture.

After the intended-resolution hero frame, accepted-audio playable clip, entry/settled/exit checkpoints, phone review, and full FFmpeg decode exist, run strict validation:

```powershell
python .\scripts\validate_vox_branch.py <project-root>
```

Strict validation checks project-local code-native files and fragments, hero-frame resolution and decodability, playable video and audio streams, full clip decode, checkpoint files, phone-review artifacts, adjacent-scene transition contracts, and synchronization between `project-state.json` and `scene-spec.json` when Lean state exists.

After rendering a clip, create visual evidence:

```powershell
python .\scripts\make_visual_evidence.py <clip.mp4> <evidence-dir>
```

After assembling a full master, extract consistent per-scene clips and entry/settled/exit frames from the Lean scene timings:

```powershell
python .\scripts\lock_vox_inputs.py <project-root> --write
python .\scripts\build_scene_evidence.py <project-root> <evidence-dir>
```

The lock command hashes the accepted audio inputs, canonical scene timing, and assembled source master. Run it again whenever any of those inputs changes. The extractor refuses to overwrite a non-empty evidence directory, verifies the lock, and writes the same `evidence_input_fingerprint` into its machine-readable index. Record that value in each reviewed `hero_frame.input_fingerprint` and `playable_clip.input_fingerprint`; a later input change then makes the old evidence fail strict validation instead of silently passing.

Inspect the contact sheet and the entry, settled, and exit frames. Then watch the playable clip at phone size. Use [visual-qa.md](references/visual-qa.md). Do not accept from process exit, code size, component count, or stills alone.

Check the settled frame for focal order, common grounding, facing, occlusion, and subtitle clearance. Check the clip for staggered entrances and whether each impact, whoosh, or tick lands on the visual event it is meant to explain.

Handoff accepted scene implementations to `xingchen-lookdev`, then use `remotion-render-adapter` for the formal render job. Keep rejected visual hypotheses visible until the full preview confirms the winner.

## Reference Study Boundary

Read [learned-branches.md](references/learned-branches.md) when reconstructing a public Vox-style result. Reuse causal grammar, not logos, title packaging, exact compositions, proprietary assets, or copied prompts.
