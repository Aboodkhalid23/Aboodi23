# Features and limits

New CLI jobs set `edition: public-lite`. Source timing, continuous voice, caption modes, face protection and artifact QA remain intact. Three layouts are available: `title` (one headline on an opaque background), `card` (one compact presenter-safe side card), and `flow` (two or three literal source items in simple cards, without invented steps).

Styles are `dark` and `paper`, fixed for the entire video. Single-presenter editorial composition supports full-frame emphasis, left/right split layouts and a bounded single window with frame-driven transitions. Duplicate presenter windows, multi-window choreography, 3D layouts and a full advanced template library are outside this workflow.

The v0.6 refinement assigns purple to keywords, cyan to process and a restrained warm accent to results and closing. Typography colors meet at least 4.5:1 contrast on the two stable background surfaces. Window outlines, keyword underline reveals and one short source-to-result indicator add motion before a stable hold. Process rows use compact spacing and separate emphasis surfaces; a drawing region remains reserved below them. The source video is never recolored by the theme.

The repository contains the Skill, planner, renderers, tests and reproducible examples. Private source media and local job outputs are not redistributed without explicit authorization.

## Captions and camera

`--presenter-layout single` is the v0.4 composite default; `original` preserves the earlier side-card layout. The single media element remains mounted for the entire timeline while its containing rectangle changes. `--presenter-motion subtle` adds a bounded 1.06× focus pulse to full-frame emphasis scenes. There is one continuous video/audio track; no duplicate or blended presenter images.

Single-presenter composition crops the source caption reserve and redraws all captions once from the current SRT. In `original` mode, covered captions are redrawn only as needed. Generated captions explicitly use the SRT; `none` adds none. Confirm SRT accuracy and alignment before rendering. Reserve the bottom 18%. Source movement and presenter windows are rejected for transparent output.

The Agent should write a source-grounded direction file after sentence-level analysis. `--direction FILE.json` maps SRT indices to `mode` (`hero`, `split`, `focus`, `process`, `closing`), `lines` (one to three literal source excerpts), optional `eyebrow` and zero-based `highlight`. The planner rejects text absent from that cue; cues longer than six seconds should use directions that fit their split source segments. A direction controls presentation, without changing the continuous source timing.

New public-lite jobs require Remotion. Historical V2 storyboards without the `edition` field retain their original renderer; capabilities already published cannot be recalled from Git history. The HyperFrames adapter remains for those historical inputs, without silently dropping public-lite features.

## Semantic doodles

Single-presenter composite jobs support `doodle: {type, label}` inside a direction item. Supported types are `phone-mirror`, `notes`, `agent-output`, `information-overload`, `climb-boulder`, `workstation-balance`, `paper-plane-route`, `route-activation` and `before-after-illustration`. The planner validates the label against the exact spoken cue. The Agent chooses a fitting drawing after reading the source; a drawing count is not a quality target.

Drawing strokes use normalized SVG path lengths, are frame-driven and hold after revealing. Both dark and paper styles supply an explicit contrasting ink. The drawing region is reserved independently of the title, presenter rectangle and subtitle reserve. The visible annotation marks every drawing as a conceptual illustration; it is not a screenshot, evidence asset or a demonstration of real device control. Original-layout and transparent jobs reject this direction field rather than silently discarding it.

## QA

Eight review frames sample the timeline rather than requiring eight structures. Inspect every layout and presenter treatment actually used at entry, hold and exit, first/last frames, movement, transitions, complete caption text and original face color. Technical checks and full decode do not prove full playback review or user acceptance.

For an engineering check use the reproducible [current example](../examples/current-demo/README.md). A private preview can use `npm run verify:lite -- INPUT.mp4 INPUT.srt OUTPUT DIRECTION.json` with a new local output folder. The helper renders a dark-style video, both-style review stills, each beat at 12/60/90 percent, full decode, black-frame detection and a contact sheet. Outputs default to ignored `.tmp/`; do not commit private input media or frames. Engineering tests do not replace production job approvals. The current workflow supports 16:9 horizontal input only.
