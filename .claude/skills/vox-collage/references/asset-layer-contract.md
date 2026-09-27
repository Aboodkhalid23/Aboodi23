# Asset And Layer Contract

Use this reference before generating, extracting, or accepting assets.

## Shot Lock

Before creating assets, record for each shot:

- focal order and relative scale;
- facing and sight-line relationships;
- common ground line, or an explicit reason the actors float;
- front-to-back occlusion stack;
- subtitle-safe lane.

Do not treat a new shot as a crop of the previous shot when it changes any of those decisions. The environment plate contains no actor that must enter, leave, resize, or change z-order independently.

## Layer Roles

Every `scene-spec.json` layer must use one role:

- `plate`: substrate, environment, or large static field;
- `source`: real evidence with preserved geometry;
- `cutout`: isolated person, object, place, or archival illustration;
- `prop`: supporting object with independent timing;
- `type`: exact live headline or label;
- `data`: chart, map, number, timeline, or evidence graphic;
- `annotation`: arrow, circle, underline, stamp, marker, or connector;
- `occluder`: foreground paper edge or object used for depth/reveal;
- `texture`: non-semantic grain, dust, light, ink, or print imperfection.

## Separation Test

Keep an actor separate when any answer is yes:

- Does it enter, exit, pivot, scale, mask, or parallax independently?
- Must it remain exact while another element changes?
- Will it be reused in another scene?
- Does its z-order change?
- Does it carry proof, identity, or an exact label?

Merge repeated low-value decoration into a plate when separation adds no visual control.

## Generated Raster Rules

- Use one prompt per distinct asset or coherent variant.
- Record the final prompt path and accepted file path.
- Leave exact Chinese text, numbers, brand copy, and evidence labels out of the bitmap.
- Ask for crop room based on intended placement, not a generic centered portrait.
- For opaque cutouts, generate on a flat removable chroma background and validate the final alpha edge.
- A cast or actor sheet may establish visual consistency, but it is not an animation-ready layer: split every accepted actor into an individual alpha-checked cutout.
- For hair, glass, smoke, liquids, reflections, or translucent material, use a plate, mask, or confirmed native-transparency route; do not pretend a broken matte is acceptable.
- Reject duplicated limbs, accidental words, watermarks, identity drift, fake proof cues, and lighting inconsistent with `DESIGN.md`.

## Existing Poster Decomposition

If only a flattened poster exists:

1. identify bounding boxes and intended final centers;
2. extract crops;
3. remove backgrounds for opaque subjects;
4. erase duplicated neighboring objects;
5. inpaint or locally blur vacated landing regions;
6. animate actors back to original centers so the settled frame reconstructs the approved poster.

Do not leave sharp duplicate actors in the backdrop. Prefer a clean plate or separately generated actors over repeated manual cleanup.

## Asset Manifest Minimum

Record:

```json
{
  "id": "hero-cutout",
  "role": "cutout",
  "source_kind": "generated",
  "path": "visual/vox/media/images/hero-cutout.png",
  "prompt_ref": "visual/vox/prompts/hero-cutout.txt",
  "status": "approved",
  "alpha_checked": true,
  "notes": "No embedded text; designed for right-third placement"
}
```

Use `source_kind`: `source`, `local`, `generated`, or `code-native`. Generated assets never become proof.

For a reviewed or approved code-native actor, `path` is still required. Point to a project-relative source file, and use a fragment when several independently addressable actors share one SVG or HTML file:

```json
{
  "id": "viewing-rays",
  "role": "annotation",
  "source_kind": "code-native",
  "path": "visual/vox/media/code/hero-settled.html#viewing-rays",
  "status": "reviewed"
}
```

The fragment must be a literal DOM or SVG `id` in that file. A manifest name without an existing file and addressable fragment is not an independent layer.
