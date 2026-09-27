# HyperFrames paper-cut assembly

## Reconstruct the approved hero frame

Place the fixed clean plate first, then extracted layers at the exact scale and coordinates of the approved still. Add generated wordmarks and code-native labels last. Compare a static snapshot with the approved hero frame before adding motion.

Use depth roles: fixed paper environment, narrative focal layers, then foreground type/accents. Avoid centered web-card layouts and flat code-drawn infographic substitutes.

## Motion hierarchy

Use physical paper verbs:

- `slap`: scale 1.12–1.20 to 1 with slight rotation correction;
- `slide`: enter from an edge with a small skew/rotation;
- `drop`: enter from above and settle;
- `peel`: clip-path reveal;
- `stamp`: fast type impact;
- `drift`: finite 6–18px motion;
- `camera`: slow 3–6% push/pull/pan on a wrapper;
- `page-push`: overlapping scene handoff.

Animate the hero first and one explanatory element second. Keep decoration fixed. Camera motion and wordmarks may provide energy when only one subject moves.

## Transform ownership

Use separate wrappers when the same visual needs entrance motion and camera motion. Do not write competing transforms to one node. Keep camera movement on the scene-camera wrapper and object motion on child layers.

## HyperFrames contract

- Put the standalone `data-composition-id` element directly in `body`.
- Declare start, duration, track index, width, and height.
- Create a synchronous `gsap.timeline({paused:true})` and register it in `window.__timelines`.
- Animate transforms, opacity, and clip paths; avoid layout properties.
- Never animate display/visibility, use randomness, infinite repeats, asynchronous timeline construction, CSS transitions, or CSS keyframes.
- Use deterministic media paths and framework-owned audio playback.

## Transitions

Overlap outgoing and incoming scene bodies. Keep the outgoing frame assembled until the incoming scene or transition cover is opaque. Do not set the outgoing scene to zero opacity before the handoff. Do not reintroduce the untouched master still as a final settle.

## Text safety

Place generated wordmarks inside bounds that remain safe under the maximum camera scale and their entrance overshoot. Use motion assertions such as `staysInFrame`. Give secondary labels high-contrast paper strips or ink chips; avoid plain black text over dark collage textures.

## QA

Inspect first frame, every hero, text overshoots, 0.1 seconds before/after transitions, audio edit joins, and final hold. Run lint, check with transition samples, animation map, and focused keyframe onion shots. After final rendering, inspect the encoded MP4 with FFprobe, extract a contact sheet from the MP4, and run FFmpeg `blackdetect`.
