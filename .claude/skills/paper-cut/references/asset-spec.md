# Asset specification

## Manifest record

```json
{
  "id": "scene-02-hero-title",
  "sceneIds": ["scene-02"],
  "role": "type",
  "sourcePath": "assets/originals/scene-02-hero-title.png",
  "processedPath": "assets/processed/scene-02-hero-title.png",
  "alphaRequired": true,
  "status": "approved",
  "provider": "approved-image-provider+local-alpha-crop",
  "attemptId": "provider-attempt-id",
  "sha256": "...",
  "notes": "Exact approved text; image call 4 of 12."
}
```

Roles: `background`, `subject`, `prop`, `texture`, `type`, `audio`, `reference`. Statuses: `planned`, `generated`, `processed`, `approved`, `rejected`, `superseded`.

## Scene-first separation

- Generate/approve the complete hero frame before separating layers.
- Keep all fixed environment, texture, and nonessential decoration in the background.
- Extract each independently moving focal subject or prop from the approved still.
- Keep native silhouette, torn edge, print texture, and shadow.
- Create a clean plate only for pixels exposed by extraction.
- Avoid green-screen regeneration when the original pixels can be masked.
- Preserve provider originals under `assets/originals/`; write every derivative separately.

## Text

- Keep subtitles, paragraphs, scientific labels, numbers, and revisable data as HTML/SVG.
- Generate only short, approved hero wordmarks when collage typography materially improves the scene.
- Reject any wordmark with a wrong character, punctuation, baked checkerboard, clipped paper edge, or inconsistent shadow.

## Visual consistency

Lock paper stock, edge treatment, print process, grain, shadow direction/depth, palette, and illustration register across prompts. Do not normalize a full-frame scene into a square canvas. Normalize only standalone cutouts where consistent occupancy is useful.

## Local derivatives

Cropping transparent margins, alpha cleanup, masking, local inpainting, compositing, mirroring, resizing, color correction, shadow repair, paper outlines, and texture overlays are local derivatives and do not consume provider attempts.

Reject disconnected edge debris, clipped silhouettes, inconsistent paper, obvious watermark residue, unintended geographic symbols, or unreadable generated text.
