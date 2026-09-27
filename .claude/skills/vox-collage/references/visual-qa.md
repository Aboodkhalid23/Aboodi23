# Visual QA

Review the rendered result, not the prompt or source code.

## Cold Frame Review

Hide subtitles and production notes. Inspect the contact sheet at thumbnail size.

- Is the focal object immediate?
- At phone downsample size, is the essential semantic actor still identifiable, or has it become a postage stamp inside decorative space?
- Does the sequence show a real state change?
- Are adjacent frames meaningfully different without becoming visually unrelated?
- Does the material world remain coherent?
- Does any frame collapse into a centered slide or generic card grid?
- Are proof and exact type readable without zooming?

## Motion Review

Watch once at normal speed, once muted, and once frame-by-frame around entrances and transitions.

Also watch once with subtitles and exact labels hidden. Caption changes do not count as picture-state changes.

- Does each movement have a semantic or physical reason?
- Do paper actors settle rather than float forever?
- Are entrances staggered by hierarchy instead of everything arriving together?
- Does a camera move direct attention rather than manufacture energy?
- Are text, faces, logos, and evidence stable?
- Does the final hero frame reconstruct cleanly without duplicate ghosts?
- Do cuts preserve continuity anchors where needed?
- Can each adjacent-scene handoff name a carried material, object, rail, aperture, color field, or motion vector, or an explicit intentional reset?

## Anti-PPT Blockers

Block when:

- six or more consecutive scenes share the same container geometry;
- the video is readable as a slide deck with transitions removed;
- large text is the dominant visual because the picture is missing;
- motion consists mainly of opacity, scale, labels, and connector lines;
- subtitles or labels are the only changing layer through an explanatory interval;
- essential semantic actors are too small to identify in the phone downsample even though the subtitles are readable;
- a cut breaks the material world without a carried anchor or an intentional reset;
- generated plates are used as full-frame backgrounds behind summary bullets;
- code paths or component counts are offered instead of viewing evidence.

## Technical Evidence

Require:

- positive duration and expected dimensions/fps;
- full FFmpeg decode without error;
- nonblack/nontransparent sampled frames;
- contact sheet and named checkpoint frames;
- actual asset paths, with no placeholders or remote-expired URLs;
- final preview duration aligned to accepted audio when audio exists.

These requirements only prove that review artifacts exist and decode. Artifact existence never proves that a human watched the result or approved it — the `Approve` / `Revise` / `Block` call below is a human judgment.

Return `Approve`, `Revise`, or `Block`, with scene ids or timestamps and the narrowest repair.
