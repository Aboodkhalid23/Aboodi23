# Image-led production

## Source-of-truth rule

Treat each approved complete scene still as the visual source of truth. The still locks composition, paper stock, halftone density, torn edges, palette, lighting, shadow direction, and relative scale. Animation must preserve that lock.

## Generate whole scenes before parts

Prompt from the storyboard's exact composition: subject positions, negative space, visual hierarchy, paper materials, print process, and intended text-safe zones. Do not generate a bag of generic suns, globes, maps, and people and then improvise a composition in code.

When the user asks to see a storyboard, show real raster hero frames from the image model. A flat vector schematic may accompany them as an annotation, but cannot replace them.

## Choose motion layers

For each scene, rank elements:

1. narrative hero — normally animate;
2. explanatory mechanism — animate only if it clarifies causality;
3. atmosphere and decoration — normally keep fixed;
4. text — animate selectively;
5. camera — add a slow 3–6% push, pull, or pan.

Two to four active channels are usually enough. If everything moves, the scene loses the approved composition and increases masking failures.

## Extraction order

1. Extract the selected element from the approved still with structure-aware masking/matting.
2. Preserve native paper edge, halftone texture, contact shadow, and irregular outline.
3. If the shadow cannot be separated cleanly, either keep it with the layer or rebuild a restrained directional CSS shadow that matches the still.
4. Repair only the exposed hole in the fixed background. Prefer local inpainting or selective compositing.
5. Generate a replacement clean plate only when local repair cannot preserve the scene.

Do not regenerate selected elements on green solely because chroma removal is easy. Regeneration changes shape, texture, lighting, and shadow and often breaks continuity with the approved still.

## Transparent typography

Use an image model for a few hero wordmarks when typography itself is part of the collage art. Before generation:

- approve the exact characters and punctuation;
- limit each asset to one short phrase;
- request direct alpha transparency, real torn paper, print texture, and an integrated physical shadow;
- inspect every character at full resolution;
- preserve the original and make a separate alpha-cropped derivative.

Keep secondary labels code-native for factual accuracy, contrast, and easy revision. Never rely on generated type for paragraphs or subtitles.

Treat subtitles and editorial type as separate switches. A request for no subtitles still permits a restrained keyword/wordmark plan unless the user explicitly requests no text anywhere on screen.

## Clean-plate and settle behavior

The clean plate plus extracted layers is the scene for its entire duration. Do not place the untouched master still on top at the end as a settle frame: that creates a visible one-frame or one-second jump and hides the motion layers.

## Sensitive maps and boundaries

Determine whether directional language refers to a country, a region, or a global pattern. If geographic boundaries are not necessary, use borderless environmental contrasts, abstract ocean/land textures, pressure diagrams, or circulation paths. Do not introduce country borders, administrative lines, flags, disputed outlines, or labels merely as decoration.

## Reuse test

Before another image call, ask:

- Can the approved still be cropped, masked, mirrored, recolored, or locally repaired?
- Can a secondary label remain HTML text?
- Is the difference visible at delivery resolution?

If yes, use a local derivative and record it without consuming another provider attempt.
