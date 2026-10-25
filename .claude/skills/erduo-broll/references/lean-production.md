# Creative relay production commands

Use the installed project-pinned HyperFrames executable, Node and FFmpeg. Do not
upgrade the global runtime as part of making a film. **Parent owns these commands.**
Resolve the installed Skill directory once, then give every task actual absolute
paths. The shell examples below run with the Skill directory as cwd; do not paste
relative script paths into a different project or search the host for them.

Prepare a short task file before starting a fresh role context:

```sh
node scripts/prepare-creative-task.mjs --project /path/to/project --role director
node scripts/prepare-creative-task.mjs --project /path/to/project --role creator --shots S01,S02
node scripts/prepare-creative-task.mjs --project /path/to/project --role reviewer --quality draft
```

The helper returns the task path and required read files, with absolute execution
commands in the task. It does not start agents or remove host-injected global
instructions. Use the host's fresh-context delegation, not a fork of the parent's
history. Originals are `input/original.srt` and `input/design.md` by default;
Director input overrides are available through `--srt` and `--design`.

Before creator dispatch, Parent has a valid plan, `direction.md`, one short
`direction/<id>.md` card per shot and `assets/index.md` with known local files and
sources. The Director can describe missing material; Parent resolves it with a
material specialist only when needed. A native graphic still needs prepared
fonts and animation dependencies. No duplicate technical plan or manual hashes.

Creators receive their owned continuous shots plus adjacent seam cards. Their
editable source stays in the one production project with disjoint file ownership;
shared assets/code are prepared once. They return ready shot IDs to Parent for
rendering. Reviewer tasks point to real available sheets and previews, identifying
missing shots for a partial preview. Pass `--quality draft|final` for the render
just produced; when both exist the helper requires an explicit choice so an old
final cannot hide a newer draft. The raw render index stays with Parent because
it contains timing/operation metrics. Do not pass creators' explanations or costs
to the independent reviewer.

One project contains originals, a compact plan, compositions, and shared assets.
`broll-plan.json` example (adjust to the actual SRT, never fabricate cue times):

```json
{
  "schemaVersion": "lean-1",
  "title": "One clear idea",
  "inputs": {"srt": "input/original.srt", "design": "input/design.md"},
  "profile": {"width": 3840, "height": 2160, "fps": 30},
  "shots": [{
    "id": "S01", "startMs": 0, "endMs": 6000, "cueIds": [1],
    "intent": "Understand the actual product change",
    "subject": "The supplied before and after screenshots",
    "material": {"route": "provided"},
    "composition": "compositions/S01.html"
  }]
}
```

Group cues by meaning. Cover zero through the last cue end, including gaps, with
contiguous shots. Every referenced cue must overlap its shot. Short projects can
have one shot. `cueIds` are one-based file order, independent of printed SRT
numbers. The renderer quantizes global boundaries to video frames so rounding
does not accumulate across shots; the plan keeps original milliseconds.
Defaults are 4K/30; respect portrait and other explicit profiles.
Record selected material/font source, licence and local file in `assets/index.md`. Never fabricate product evidence or silently buy generated media.

Each HTML file has a sized root with its shot id, profile width/height and local
duration `(endMs-startMs)/1000`. With the pinned HyperFrames **0.7.104** renderer,
use project-root paths such as `assets/photo.jpg` inside compositions, not
`../assets/photo.jpg`. Declare local `@font-face` rules in each HTML; linking a
shared font stylesheet alone does not satisfy this version's strict check.
Use stable element IDs and a sized timed `class="clip"` root. Explicitly initialize
and register the finite seekable timeline:

```js
window.__timelines = window.__timelines || {};
const tl = gsap.timeline({ paused: true });
// Set initial transforms/visibility immediately, or in CSS, before the timeline.
// gsap.set('#incoming', { opacity: 0, y: 40 });
// Add the shot's meaningful motion using locally available GSAP.
window.__timelines['S01'] = tl;
```

Keep an intentional visible opening subject. Initial hiding inside `tl.set(..., 0)`
can fail at the exact first frame; use CSS or immediate `gsap.set` instead. Animate
transforms/opacity, not `letterSpacing`, `left/top` or width/height. Separate
position, camera and emphasis wrappers so simultaneous tweens do not fight over
one transform. Preserve a readable settle and finite seek-safe motion. The
[original starter](../assets/motion-starter.html) demonstrates this contract with
local `assets/NotoSansSC.ttf` and `assets/gsap.min.js`; prepare those files before
adapting it, and change its shot ID/profile/duration to match the actual plan.

These pinned-version requirements take precedence over newer general
HyperFrames examples. Use local assets; rendering must not fetch media, scripts
or fonts from the network.

```sh
node scripts/lean-plan.mjs --project /path/to/project
node scripts/lean-render.mjs --project /path/to/project --quality draft --hyperframes /path/to/hyperframes
node scripts/lean-render.mjs --project /path/to/project --quality final --hyperframes /path/to/hyperframes
```

Draft and final have separate output folders. Draft uses at most 15fps and half
the output width/height. For a 1080p source, this pinned runtime still captures
at the source raster before downscaling; it has no sub-1080p capture preset.
A draft never counts as final media. After a local repair, rerun the same command; use
`--shots S02` to work on a selected shot. A complete preview requires all shots.
The renderer records actual work/reuse/time and refreshes previews after changed
inputs. It validates media once per changed render and reuses unchanged results.

Parent gives rendered media to the creator for self-check and to an independent
reviewer for visual judgement. Repair unreadable type, vague subjects, missing or
misleading material, weak action and broken seams in the owning creator's source;
rerun only affected shots, then review those shots and their joins. Final-quality
encoding is not aesthetic approval. Partial previews can contain non-adjacent
ready shots; inspect `preview.shotIds` and `complete` before interpreting a seam.

If rendering fails, Parent distinguishes source errors from runtime/permission
failures. Give the creator the specific failed shot and source error. A blocked
file server or missing executable is not fixed by changing artwork, lowering
frame rate, or making each creator retry. Use the already authorized working
execution surface, or report the real missing prerequisite. Record actual viewed
media and useful corrections briefly; scripts already own technical facts.
