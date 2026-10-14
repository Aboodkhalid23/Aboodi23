# Blocking visual quality gates

These checks apply to every real invocation. Passing unit tests, typecheck, build, or render is not visual acceptance.

## 1. Presentation mode

Original-layout beats declare exactly one of the first two modes. Single-presenter jobs use the third mode:

- **Presenter-safe:** the live presenter remains visible. Foreground content is restricted to x=5%–32% or x=68%–95%; center x=35%–65% is completely clear; the lower 18% is reserved for burned-in captions.
- **Opaque full-screen:** the graphic covers the full 1920×1080 canvas with an opaque background. It may use the center because the presenter is intentionally replaced for that beat.
- **Single-presenter composition:** one persistent source video is reframed into a full-frame or single-window rectangle. Protect the actual forehead, face and chin inside that rectangle; typography occupies separate regions. Cropping removes the old subtitle reserve and matching SRT captions are redrawn once. Inspect moving boundaries at entry, hold and exit, without duplicate presenter layers.

Reject graphic overlap with a visible face. In original mode, foreground graphics stay outside the center lane; if the center is needed, use opaque full-screen. In single-presenter composition, reserve the relocated person's actual region rather than assuming the face remains at the original center. Keep the bottom 18% for captions in either mode.

## 2. Side-card density

Presenter-safe side surfaces must be content-fit.

- Do not stretch a card from a fixed top to a fixed bottom.
- Maximum card height is 64% of the frame.
- Do not leave a decorative empty lower half.
- Use one rail when there is one idea. Use two rails only when the narration genuinely contains two complementary groups.
- Headings, items, and takeaway must participate in normal document flow; do not pin a footer far below sparse content.

## 3. Full-screen composition

- The background must be fully opaque from edge to edge; no transparent final gradient stop.
- The visual hierarchy needs one clear primary element, one supporting structure, and one result or source label.
- A process route or illustration may cross the center only in this mode.
- Critical content stays out of the lower 18% caption reserve unless the source is explicitly caption-free.

## 4. Stable review frames

Public-lite selects eight timeline samples. Check that each sample is readable; if it lands in entry/exit, inspect an additional stable frame of that beat. Also inspect first/last frames and basic camera entry/peak/return. Historical V2 stills are selected at 72% of each beat, after entry but before exit. A single screenshot cannot establish motion quality.

Gate C must include:

1. eight actual timeline frames for public-lite, covering every basic layout used; historical V2 retains eight distinct semantic structures;
2. the exact timestamp, structure, presentation mode, and SHA-256 for every frame;
3. a 4×2 contact sheet built from those exact frames;
4. manual frame review, recorded as pass/fail for face safety, density, clipping, contrast, semantic fit, and subtitle clearance.

## 5. Blocking decision

Any of the following blocks Gate D:

- presenter lane partially covered;
- opaque scene not actually opaque;
- side card visibly padded with unused space;
- content clipped, overlapping, or too small to read;
- screenshot captured before the composition reaches a stable readable state;
- structure selected for visual variety rather than spoken meaning;
- evidence treated as decoration or an illustration treated as proof;
- any manual review item left unchecked.

After fixes, regenerate the real screenshots and review the new images. Do not reuse screenshots from a rejected render.
