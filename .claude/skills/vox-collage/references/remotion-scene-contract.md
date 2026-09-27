# Remotion Scene Contract

Use this reference while implementing selected scenes.

## Layer Fields

Each actor needs:

- stable `id`, `role`, and `z`;
- `motion_tier` of `primary`, `secondary`, `tertiary`, or `ambient` for independently timed cutouts, props, and occluders;
- final `x`, `y`, `scale`, `rotation`, and optional `anchor`;
- facing and grounding notes when the actor represents a person, creature, or placeable object;
- `source_ref` or live `content`;
- entrance verb, start frame, and duration;
- optional finite ambient motion;
- proof and safe-region constraints.

Final coordinates are authoritative. Derive entrance states from them.

## Hierarchy And Timing

Set the still composition before adding motion. Establish the primary read first, then place secondary and tertiary actors around it without obscuring a face, hand, prop, or proof target. Use the `z` stack to make foreground occlusion intentional rather than accidental.

Let the primary tier travel furthest and have the clearest landing; give secondary actors a smaller delayed entrance; keep tertiary actors restrained; keep ambient plate movement near-static. Do not start three or more independent actors on the same frame unless `intentional_group_entrance` records the narrative reason.

Treat paired sound as an event contract: `impact`, `whoosh`, `tick`, or silence must align with the action it supports, not merely with a convenient timestamp.

## Motion Vocabulary

Use material-native actions:

- `slide`: translate from one edge with ease-out and slight settle;
- `slap`: start slightly enlarged, become opaque quickly, then settle;
- `drop`: fall with one controlled bounce;
- `pivot`: rotate around a believable tape, staple, hinge, or corner;
- `peel`: clip or mask reveal from an anchored edge;
- `stamp`: fast scale/opacity landing with a short impact hold;
- `trace`: SVG stroke draw for a real relationship;
- `wipe`: full-frame paper field used sparingly for chapter change;
- `resolve`: scattered actors settle into the final explanatory composition.

Start from scale around 0.92-0.97 or 1.15-1.35 when using scale. Do not use `scale(0)`.

For 30 fps, use these as starting points, then tune by viewing:

- small paper/label entrance: 8-14 frames;
- hero cutout entrance: 12-22 frames;
- grouped stagger: 3-6 frames;
- annotation draw: 14-28 frames;
- impact shake: 3-7 frames with rapid decay;
- final reading hold: at least 12-24 frames when the argument needs it.

## Camera

Keep the camera parallel to the editorial plane unless the scene has a real spatial reason.

- Default to hard cuts, locked camera, or a restrained push from 1.00 to about 1.04-1.08.
- Use parallax by moving separated depth groups, not by pretending one raster has layers.
- Use overscan for camera shake or pan so no black edges appear.
- Preserve proof geometry and type legibility.

## Determinism

Derive animation from `useCurrentFrame()`, `useVideoConfig()`, `spring()`, and `interpolate()`. Use stable seeded functions for torn edges, dust, and grain. Do not use `Math.random()`, current time, asynchronous mutations, or infinite CSS animation.

## Critical Evidence

For a motion-graphic scene, render:

- `entry`: proposition is visible but unresolved;
- `settled`: composition and hierarchy are complete;
- `exit`: outgoing frame is preserved until transition ownership begins;
- playable clip with accepted audio.

Stills diagnose composition. The clip decides rhythm, easing, continuity, and physicality.

Write these artifacts back into the scene contract: `hero_frame.path` plus `playable_clip.path`, `playable_clip.audio_ref`, `playable_clip.phone_reviewed`, and `playable_clip.checkpoint_paths.entry|settled|exit`. Pending validation may warn about missing evidence; strict validation must probe and fully decode the referenced media.
