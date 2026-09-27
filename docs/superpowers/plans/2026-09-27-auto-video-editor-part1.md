# المونتير الآلي — الجزء 1 (الأساس) Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** From a raw one-camera talking-head video, produce a finished 16:9 long-form episode in the Vox style: silences and retakes removed, something changes every 4–6 s (face zooms, free Wikimedia images, code-rendered graphics), with a fast teaser hook — no AI generation yet.

**Architecture:** A Python package `editor/pipeline` with one module per stage, each reading/writing files in `episodes/<ep>/edit/`. Claude writes `edit_plan.json` from a compact text brief (the only step that costs tokens); code validates it. ffmpeg does all heavy video work; Remotion renders only short graphic clips (2–6 s each) that ffmpeg splices in.

**Tech Stack:** Python 3.11, ffmpeg/ffprobe (apt), faster-whisper 1.2.1, gdown, PyYAML, requests, pytest; Node 22, Remotion 4.0.x, @fontsource/cairo, world-atlas + d3-geo; Chromium at `/opt/pw-browsers/chromium_headless_shell-1194`.

**Spec:** `docs/superpowers/specs/2026-09-27-auto-video-editor-design.md` (this plan = "تقسيم البناء" part 1 only)

## Global Constraints

- User-facing messages (CLI errors, skill text) are **Iraqi Arabic only**. Code identifiers, file names, commit messages in English.
- Repo is public: never commit video/audio or secrets. `.gitignore` adds `*.mp4`, `*.mov`, `*.wav`, `*.m4a`, `episodes/*/edit/assets/`, `episodes/*/edit/work/`, `editor/remotion/node_modules/`, `editor/remotion/out/`.
- Output: 1920×1080, 30 fps constant, H.264 `-crf 20 -preset medium`, AAC 192k, audio loudness-normalized to −14 LUFS (`loudnorm=I=-14:TP=-1.5:LRA=11`).
- Beat durations: body 4.0–6.0 s, hook zone 1.5–2.5 s. Hook zone = first 30 s of the final video (teaser included).
- No two consecutive beats share the same `kind` (all `face*` kinds count as distinct kinds from each other, but see face-share rule).
- Face share (`face`, `face_zoom_in`, `face_zoom_out`, `face_framed`) is 35–55 % of body duration.
- All on-screen text is rendered by Remotion (Chromium shapes Arabic RTL correctly); never ffmpeg `drawtext`.
- Claude reads only `work/plan_input.txt` to plan — never the video, never full JSON transcripts.
- Timestamps in `edit_plan.json` are on the **cleaned** timeline (after cuts), seconds, 2 decimals.
- Wikimedia images: only licenses matching `CC0`, `Public domain`, `CC BY*`, `CC BY-SA*`; width ≥ 1280 px; every used image logged in `credits.txt`.

## Review Focus

1. Phone footage that is variable-frame-rate or has rotation metadata → output must still be 30 fps constant and upright (Task 2 normalizes to `work/source.mp4`).
2. A raw video with no detectable speech (silent/music only) → stop with `الصوت فارغ أو مو واضح`, not an empty video (Task 3).
3. A Claude plan that runs past the cleaned duration, leaves a gap, or overlaps → validator rejects with the exact beat index (Task 5).
4. A Wikimedia search that returns nothing or only tiny/non-free images → the beat falls back to a `graphic` of type `text` using the beat's `query`, recorded in `work/fallbacks.json`; the render never fails (Task 7).
5. Audio drifting out of sync with video over a 30-minute render → compose builds one continuous audio track from the cleaned audio and only concatenates video; final A/V duration difference ≤ 0.1 s (Task 9).

---

## File Structure

```
editor/
  requirements.txt
  pytest.ini
  pipeline/
    __init__.py
    __main__.py        CLI: python -m editor.pipeline <stage> <episode_dir>
    paths.py           Episode: all file paths of one episode
    media.py           ffprobe/ffmpeg helpers (probe, run)
    fetch.py           stage 1: Drive link or local file → work/source.mp4
    transcribe.py      stage 2: → transcript.json
    clean.py           stage 3: → cuts.json + clean.mp4 + clean_words.json
    brief.py           writes work/plan_input.txt for Claude
    plan.py            EditPlan model + validate_plan
    styles.py          load_style from editor/styles/*.md
    wikimedia.py       stage 5: free images
    graphics.py        renders graphic beats via Remotion
    compose.py         stage 6: final.mp4
    deliver.py         stage 7: size check / recompress
  styles/
    README.md
    vox.md
  remotion/            Remotion project (package.json, src/*)
  tests/
    conftest.py        synthetic fixtures
    test_*.py
scripts/setup-editor.sh
.claude/skills/editor/SKILL.md
```

---

### Task 1: Scaffolding, setup script, synthetic fixture

**Files:**
- Create: `editor/requirements.txt`, `editor/pytest.ini`, `editor/pipeline/__init__.py`, `editor/pipeline/paths.py`, `editor/pipeline/media.py`, `editor/tests/conftest.py`, `editor/tests/test_media.py`, `scripts/setup-editor.sh`
- Modify: `.gitignore` (lines from Global Constraints), `.claude/settings.json` (add a second SessionStart hook: `"$CLAUDE_PROJECT_DIR"/scripts/setup-editor.sh >/dev/null 2>&1 || true`, timeout 600)

**Interfaces:**
- Produces:
  - `Episode(root: Path)` dataclass with properties: `edit` (`root/"edit"`), `work` (`edit/"work"`), `assets` (`edit/"assets"`), `source` (`work/"source.mp4"`), `transcript` (`edit/"transcript.json"`), `cuts` (`edit/"cuts.json"`), `clean_video` (`work/"clean.mp4"`), `clean_words` (`edit/"clean_words.json"`), `plan_input` (`work/"plan_input.txt"`), `plan` (`edit/"edit_plan.json"`), `fallbacks` (`work/"fallbacks.json"`), `credits` (`edit/"credits.txt"`), `final` (`edit/"final.mp4"`). `Episode.ensure()` creates edit/work/assets.
  - `probe(path: Path) -> MediaInfo` with fields `duration: float, width: int, height: int, fps: float, has_audio: bool, rotation: int`.
  - `run_ffmpeg(args: list[str]) -> None` — prepends `ffmpeg -y -hide_banner -loglevel error`, raises `MediaError(msg_ar)` on non-zero exit.
  - Fixture `talking_video(tmp_path) -> Path`: 20 s, 1280×720, 25 fps, `testsrc2` video; audio = 1 kHz tone at 0–4 s, silence 4–7 s, tone 7–12 s, silence 12–13 s, tone 13–20 s.

`requirements.txt` pins: `faster-whisper==1.2.1`, `gdown>=5`, `PyYAML>=6`, `requests>=2.31`, `pytest>=8`. `setup-editor.sh`: `apt-get install -y ffmpeg` if `ffmpeg` missing, `pip install -r editor/requirements.txt`, `npm ci --prefix editor/remotion` if `editor/remotion/package-lock.json` exists. Idempotent, quiet.

- [ ] **Step 1: Write tests** `test_probe_fixture` (duration 20.0±0.1, 1280×720, fps 25, has_audio True) and `test_run_ffmpeg_error_is_arabic` (bad input → `MediaError` whose message contains `ffmpeg`, and Arabic text `فشل`).
- [ ] **Step 2:** `cd editor && pytest tests/test_media.py -v` → FAIL (module missing).
- [ ] **Step 3:** Implement the files above; `probe` uses `ffprobe -print_format json -show_streams -show_format`, rotation from `side_data_list[].rotation` or `tags.rotate`, default 0.
- [ ] **Step 4:** Run `bash scripts/setup-editor.sh && cd editor && pytest -v` → PASS.
- [ ] **Step 5:** Commit `feat(editor): scaffold pipeline package, setup script, fixtures`.

---

### Task 2: Fetch + normalize (stage 1)

**Files:** Create `editor/pipeline/fetch.py`, `editor/tests/test_fetch.py`

**Interfaces:**
- Consumes: `Episode`, `probe`, `run_ffmpeg`.
- Produces: `fetch(source: str, ep: Episode) -> Path` — `source` is a Google Drive file/folder URL or a local path. Downloads (gdown; folder → the largest video file) into `work/raw.<ext>`, then normalizes into `ep.source`: 30 fps CFR, rotation applied, max 1920×1080 keeping aspect, H.264 CRF 18, AAC 48 kHz. Returns `ep.source`. Skips if `ep.source` exists and is newer than raw.
- Errors: non-Drive URL → `MediaError("الرابط مو رابط گوگل درايف")`; download 403/404 → `MediaError("ما گدرت أسحب الفيديو. تأكد إن الملف مشارك: أي شخص عنده الرابط")`.

- [ ] **Step 1: Tests** `test_fetch_local_normalizes_to_30fps` (fixture → probe(ep.source).fps == 30, duration 20±0.1); `test_fetch_rotated_is_upright` (fixture re-muxed with `-display_rotation 90` → assert output `width < height`, `height == 1080`, `rotation == 0`); `test_fetch_rejects_non_drive_url` (`"https://example.com/a.mp4"` → `MediaError`, message == `الرابط مو رابط گوگل درايف`).
- [ ] **Step 2:** Run → FAIL.
- [ ] **Step 3:** Implement `fetch`. Drive IDs via `gdown.download(url=..., fuzzy=True)` / `gdown.download_folder`.
- [ ] **Step 4:** `pytest tests/test_fetch.py -v` → PASS.
- [ ] **Step 5:** Commit `feat(editor): fetch and normalize raw footage`.

---

### Task 3: Transcribe (stage 2)

**Files:** Create `editor/pipeline/transcribe.py`, `editor/tests/test_transcribe.py`

**Interfaces:**
- Produces:
  - `Word` dataclass `(text: str, start: float, end: float)`; `save_words(words, path)`, `load_words(path) -> list[Word]` (JSON list of `{"t","s","e"}`).
  - `transcribe(ep: Episode, model_name: str = "large-v3-turbo", model=None) -> list[Word]` — faster-whisper `WhisperModel(model_name, device="cpu", compute_type="int8")`, `language="ar"`, `word_timestamps=True`, `vad_filter=True`. `model` param injects a fake for tests. Writes `ep.transcript`. Zero words → `MediaError("الصوت فارغ أو مو واضح")`.

- [ ] **Step 1: Tests** with a `FakeModel` whose `transcribe()` returns segments with `.words` (objects with `word,start,end`): `test_transcribe_writes_words` (3 words round-trip through `load_words`, leading spaces stripped from `text`); `test_transcribe_empty_raises` (no words → message `الصوت فارغ أو مو واضح`). Add `@pytest.mark.network` `test_transcribe_real_model_smoke` (skipped unless `EDITOR_NETWORK=1`).
- [ ] **Step 2:** Run → FAIL.
- [ ] **Step 3:** Implement.
- [ ] **Step 4:** Run → PASS (network test skipped).
- [ ] **Step 5:** Commit `feat(editor): word-level transcription`.

---

### Task 4: Clean — silences and retakes (stage 3)

**Files:** Create `editor/pipeline/clean.py`, `editor/tests/test_clean.py`

**Interfaces:**
- Consumes: `Word`, `load_words`, `run_ffmpeg`.
- Produces:
  - `normalize_ar(text: str) -> str` — strip tashkeel and tatweel, `أإآ→ا`, `ى→ي`, `ة→ه`, drop punctuation, lowercase Latin.
  - `split_phrases(words, pause: float = 0.7) -> list[list[Word]]` — new phrase when gap between words > `pause`.
  - `drop_retakes(phrases, window: float = 30.0, match: int = 3) -> list[list[Word]]` — phrase A is dropped if a later phrase B starts within `window` s after A ends and the first `match` normalized words of B equal the first `match` of A (or A has fewer than `match` words and is a prefix of B). Keeps the last attempt.
  - `keep_segments(phrases, pad: float = 0.12, merge_gap: float = 0.25) -> list[tuple[float, float]]` — each phrase → `(first.start - pad, last.end + pad)`, clamped ≥ 0, merged when gap < `merge_gap`.
  - `remap_words(words, segments) -> list[Word]` — words inside kept segments shifted onto the cleaned timeline.
  - `clean(ep: Episode) -> float` — writes `ep.cuts` (`[[s,e],...]`), `ep.clean_words`, and `ep.clean_video` (ffmpeg `trim/atrim` + `concat` filter, 30 fps); returns cleaned duration.

- [ ] **Step 1: Tests**
  - `test_normalize_ar`: `normalize_ar("أَنَّ الشَّرِكَةَ")` == `"ان الشركه"`.
  - `test_drop_retakes_keeps_last`: phrases `["شركة ايفرغراند كانت"]`(0–2), `["شركة ايفرغراند كانت أكبر شركة"]`(3–6) → one phrase remains, starting at 3.0.
  - `test_drop_retakes_ignores_far_repeats`: same two phrases but second at 100 s → both kept.
  - `test_keep_segments_removes_silence`: words from fixture timing (speech 0–4, 7–12, 13–20; pause 0.7) → segments == `[(0,4.12),(6.88,12.12),(12.88,20.0)]` (±0.01; the 0.76 s gap is > `merge_gap` so it is not merged), total 16.48.
  - `test_clean_video_duration_matches_segments` (fixture + hand-written `transcript.json`) → `probe(ep.clean_video).duration` == sum of segments ± 0.1.
- [ ] **Step 2:** Run → FAIL.
- [ ] **Step 3:** Implement.
- [ ] **Step 4:** Run → PASS.
- [ ] **Step 5:** Commit `feat(editor): remove silences and retakes`.

---

### Task 5: Edit plan model, validator, and Claude brief

**Files:** Create `editor/pipeline/plan.py`, `editor/pipeline/brief.py`, `editor/tests/test_plan.py`

**Interfaces:**
- Produces:
  - `KINDS = ("face","face_zoom_in","face_zoom_out","face_framed","image","ai_image","ai_video","graphic")`; `FACE_KINDS` = first four; `GRAPHIC_TYPES = ("number","headline","quote","map","timeline","chart","text")`.
  - `Beat` dataclass: `start: float, end: float, zone: str ("hook"|"body"), kind: str, query: str|None = None, prompt: str|None = None, treatment: str|None = None, graphic: dict|None = None, sfx: str|None = None`.
  - `EditPlan` dataclass: `style: dict` (`{"primary": str, "sections": list}`), `style_reason: str`, `teaser: list[tuple[float,float]]` (clips on cleaned timeline, played first), `beats: list[Beat]`, `shorts: list` (unused in part 1).
  - `load_plan(path) -> EditPlan`, `save_plan(plan, path)`.
  - `validate_plan(plan, clean_duration: float) -> list[str]` — Arabic error strings, empty = valid. Timeline covered = teaser (placed at 0) followed by the full cleaned video; beats cover `[0, teaser_total + clean_duration]` with no gap/overlap > 0.05 s. Checks every Global Constraints rule (durations by zone, hook zone = first 30 s, consecutive kind, face share, `graphic.type` in `GRAPHIC_TYPES`, `image` has `query`). In part 1, `ai_image`/`ai_video` are rejected with `"الذكاء الاصطناعي مو مفعّل بعد (الجزء 2)"`. Each message starts with `beat <i>:`.
  - `write_brief(ep: Episode, styles_summary: str) -> Path` — writes `ep.plan_input`: header with cleaned duration and the rules in Arabic, the styles summary, then one line per clean phrase `[mm:ss.s–mm:ss.s] text`. No JSON.

- [ ] **Step 1: Tests**
  - `test_valid_plan_passes` (hand-built plan over 40 s: 3 teaser beats of 2 s, hook beats 2 s up to 30 s, body beats 5 s, alternating kinds, face share 40 %) → `[]`.
  - `test_body_beat_too_long` → one error containing `beat 7:` and `6`.
  - `test_gap_detected`, `test_overlap_detected`, `test_past_duration_detected`, `test_same_kind_twice`, `test_face_share_too_low` → each yields exactly one error with the offending index.
  - `test_ai_kind_rejected_in_part1`.
  - `test_brief_has_no_json_and_one_line_per_phrase`.
- [ ] **Step 2:** Run → FAIL.
- [ ] **Step 3:** Implement.
- [ ] **Step 4:** Run → PASS.
- [ ] **Step 5:** Commit `feat(editor): edit plan model, validator and planning brief`.

---

### Task 6: Style library — format + Vox

**Files:** Create `editor/styles/README.md`, `editor/styles/vox.md`, `editor/pipeline/styles.py`, `editor/tests/test_styles.py`

**Interfaces:**
- Produces: `Style` dataclass: `name, summary (2 lines, Arabic), fits: list[str], palette: dict[str,str]` (keys `paper`, `ink`, `accent`), `fonts: dict` (`title`, `body`), `texture: str` (`paper|grain|clean`), `image_treatment: str` (`paper_cutout|ken_burns|film_grain`), `transition: str`, `beat_seconds: float`, `music_mood: str`, `sfx: list[str]`, `ai_suffix: str`. `load_style(name) -> Style` parses YAML front matter of `editor/styles/<name>.md`; body = free Arabic notes. `styles_summary() -> str` = `name: summary` lines of all styles.
- `vox.md` values: palette `paper #F2EBDD`, `ink #1A1A1A`, `accent #FFD400`; fonts `Cairo` both; texture `paper`; image_treatment `paper_cutout` (part 1: image on torn-paper card with drop shadow, no background removal); transition `slide`; beat_seconds 5; music_mood `curious, light pizzicato, investigative`; sfx `[whoosh, paper, pop]`; ai_suffix `"collage cutout style, halftone print texture, off-white paper background"`.
- `README.md`: documents every field above (Arabic) and how to add a style.

- [ ] **Step 1: Tests** `test_load_vox` (accent == `#FFD400`, image_treatment == `paper_cutout`), `test_missing_style_arabic_error` (`load_style("nope")` → `KeyError` message contains `ستايل`), `test_summary_lists_vox`.
- [ ] **Step 2:** Run → FAIL. **Step 3:** Implement. **Step 4:** Run → PASS.
- [ ] **Step 5:** Commit `feat(editor): style library format and Vox style`.

---

### Task 7: Free images from Wikimedia Commons (stage 5)

**Files:** Create `editor/pipeline/wikimedia.py`, `editor/tests/test_wikimedia.py`

**Interfaces:**
- Consumes: `EditPlan`, `Beat`, `Episode`.
- Produces:
  - `CommonsImage` dataclass `(title, url, width, height, license, artist, page_url)`.
  - `search_commons(query: str, limit: int = 8, session=None) -> list[CommonsImage]` — `https://commons.wikimedia.org/w/api.php` with `action=query&generator=search&gsrnamespace=6&prop=imageinfo&iiprop=url|size|extmetadata&iiurlwidth=1920&format=json`, header `User-Agent: Aboodi23-editor/0.1 (github.com/Aboodkhalid23/Aboodi23)`. Filters by license list + width ≥ 1280 (Global Constraints).
  - `collect_images(plan: EditPlan, ep: Episode, session=None) -> EditPlan` — for each `image` beat downloads first acceptable result to `ep.assets/img_<i>.<ext>`, sets `beat.treatment` default from style, appends `title — artist — license — page_url` to `ep.credits`; no result or network error → beat becomes `kind="graphic", graphic={"type":"text","text": beat.query}`, logged to `ep.fallbacks`. Same image never used twice. Returns updated plan (and saves it).

- [ ] **Step 1: Tests** with a fake session returning canned JSON: `test_filters_small_and_nonfree` (3 results: 800 px CC BY, 2000 px "All rights reserved", 2000 px CC BY-SA → only the last), `test_collect_falls_back_to_text_graphic` (empty results → kind `graphic`, type `text`, fallbacks.json has 1 entry), `test_credits_written`, `test_no_duplicate_images`.
- [ ] **Step 2:** Run → FAIL. **Step 3:** Implement. **Step 4:** Run → PASS.
- [ ] **Step 5:** Commit `feat(editor): free Wikimedia images with license filter and fallback`.

---

### Task 8: Remotion graphics (Vox)

**Files:**
- Create: `editor/remotion/package.json` (pin `remotion`, `@remotion/cli`, `@remotion/renderer` to `4.0.529`, `react`/`react-dom` 18, `@fontsource/cairo`, `world-atlas@2`, `d3-geo`, `topojson-client`), `package-lock.json`, `tsconfig.json`, `src/index.ts`, `src/Root.tsx`, `src/style.ts`, `src/graphics/{Number,Headline,Quote,MapZoom,Timeline,Chart,BigText,ImageCard,FaceFrame}.tsx`
- Create: `editor/pipeline/graphics.py`, `editor/tests/test_graphics.py`

**Interfaces:**
- One Remotion composition per graphic type, ids: `number`, `headline`, `quote`, `map`, `timeline`, `chart`, `text`, `image` (image with `treatment`), `face_frame_bg` (still: paper background + frame, face is overlaid later by ffmpeg). 1920×1080, 30 fps, `durationInFrames` from props.
- Props for all: `{style: {palette, fonts, texture}, durationSec: number, ...typeFields}`; type fields: number `{value, label, prefix?}` (counts up with easing, Arabic-Indic digits off — Western digits); headline `{outlet, title, highlight}` (yellow marker sweeps across `highlight` substring); quote `{text, who}`; map `{country: ISO-3166 alpha-3, label}` (world-atlas 110m, zoom to country, accent fill); timeline `{items: [{year, label}]}`; chart `{bars: [{label, value}], unit}`; text `{text}`; image `{src (file:// path), treatment}` (ken_burns: 1.0→1.08 scale; paper_cutout: torn-paper card, 2° tilt, shadow).
- Every composition renders RTL (`direction: rtl`), Cairo font loaded from `@fontsource/cairo`, paper texture = CSS noise via SVG `feTurbulence` (no external files).
- Python: `render_graphic(beat: Beat, style: Style, out: Path) -> Path` — writes props JSON to `work/props_<n>.json`, runs `npx remotion render src/index.ts <id> <out> --props=<file> --browser-executable=/opt/pw-browsers/chromium_headless_shell-1194/chrome-linux/headless_shell --concurrency=4 --codec=h264 --crf=18` with cwd `editor/remotion`. `render_face_frame_bg(style, out_png) -> Path` via `npx remotion still`.

- [ ] **Step 1: Test** `test_render_each_graphic_type` (parametrized over the 8 video types, 2 s each, Arabic text `شركة إيفرغراند` where text applies) → output exists, `probe` duration 2.0±0.1, 1920×1080. `test_render_face_frame_bg` → PNG exists. Mark `@pytest.mark.slow`.
- [ ] **Step 2:** Run → FAIL.
- [ ] **Step 3:** Implement Remotion project + `graphics.py`. Verify the headless_shell path with `ls` first; if different, use the one under `/opt/pw-browsers`.
- [ ] **Step 4:** `pytest -m slow tests/test_graphics.py -v` → PASS. Also render `headline` still to `work/` and open it with the Read tool to eyeball Arabic shaping/RTL (letters connected, right-aligned).
- [ ] **Step 5:** Commit `feat(editor): Remotion Vox graphics`.

---

### Task 9: Compose final video (stage 6)

**Files:** Create `editor/pipeline/compose.py`, `editor/tests/test_compose.py`

**Interfaces:**
- Consumes: `Episode`, `EditPlan`, `Beat`, `render_graphic`, `render_face_frame_bg`, `load_style`, `run_ffmpeg`, `probe`.
- Produces: `compose(ep: Episode) -> Path` — writes `ep.final`.
  1. **Audio track:** teaser clips' audio (from `clean.mp4`) + full `clean.mp4` audio, concatenated, `loudnorm` per Global Constraints → `work/audio.m4a`.
  2. **Timeline map:** final time `t` → cleaned time: `t < teaser_total` maps into teaser clips; else `t - teaser_total`.
  3. **Per-beat video clip** (`work/beat_<i>.mp4`, video only, exactly `end-start` s, 1920×1080 30 fps):
     - `face`: trim of `clean.mp4` at mapped times, scaled/padded to 1920×1080.
     - `face_zoom_in` / `face_zoom_out`: same, with crop that scales 1.0↔1.15 linearly centered on frame center (upper third bias: center y at 40 %).
     - `face_framed`: face trim scaled to 60 % overlaid centered on `face_frame_bg` PNG.
     - `image` / `graphic`: `render_graphic`.
  4. **Concat** beat clips with the concat demuxer (`-c copy`, all clips encoded identically), then mux with `work/audio.m4a` → `ep.final` (`-shortest` not used; lengths must match).
  - Beat clips are cached: skip if exists and plan hash for that beat unchanged (`work/beat_<i>.hash`).

- [ ] **Step 1: Tests** (fixture + hand-written plan: 2 teaser clips 2 s, then beats alternating `face`, `face_zoom_in`, `graphic text`, `face_zoom_out`, `face_framed`, covering the whole timeline):
  - `test_final_duration` → `probe(final).duration` == teaser_total + clean_duration ± 0.1.
  - `test_av_in_sync` → audio stream duration vs video stream duration differ ≤ 0.1 s.
  - `test_output_format` → 1920×1080, fps 30.
  - `test_graphic_beat_visible` → extract frame at the middle of the `graphic` beat; mean color close to Vox paper `#F2EBDD` (each channel ±25) — proves the graphic, not the face, is on screen.
  - `test_rerun_uses_cache` → second `compose` call re-encodes no beat clip (mtimes unchanged).
- [ ] **Step 2:** Run → FAIL. **Step 3:** Implement. **Step 4:** Run → PASS.
- [ ] **Step 5:** Commit `feat(editor): compose final video from beats`.

---

### Task 10: Deliver, CLI, and the `editor` skill

**Files:** Create `editor/pipeline/deliver.py`, `editor/pipeline/__main__.py`, `.claude/skills/editor/SKILL.md`, `editor/tests/test_cli.py`; Modify `CLAUDE.md` (skills table: add row `منتجة حلقة أو ريل من فيديو خام | editor`)

**Interfaces:**
- `prepare_delivery(ep: Episode, max_mb: int = 1024) -> Path` — if `final.mp4` ≤ `max_mb`, return it; else re-encode to `edit/final_small.mp4` raising CRF by 3 per attempt (max CRF 32) until it fits; return that path.
- CLI `python -m editor.pipeline <stage> <episode_dir> [--source URL_OR_PATH]`, stages: `fetch`, `transcribe`, `clean`, `brief`, `validate`, `images`, `compose`, `deliver`, and `prep` (= fetch→transcribe→clean→brief) and `render` (= validate→images→compose→deliver). Prints Arabic progress lines; on `MediaError` prints the Arabic message and exits 1. `validate` prints each error and exits 2 if any.
- `SKILL.md` (Arabic; frontmatter `name: editor`, description with triggers `منتج`, `مونتاج`, `منتجلي الحلقة`, `سوّ مونتاج`): steps for Claude —
  1. Ask for the Drive link if not given; remind once that network must be Full (short, 1 line).
  2. `python -m editor.pipeline prep episodes/<ep> --source <link>`.
  3. Read **only** `work/plan_input.txt`; if the episode has `02-draft.md`/final script, read only its hook section.
  4. Pick style (part 1: `vox` only), tell the user one line `الستايل: … لأن …`.
  5. Write `edit_plan.json`: teaser = 3–4 strongest 1.5–2.5 s moments (use `viral-hooks` rules); hook beats fast; body beats 4–6 s; images for named people/companies/places (`query` in English for Commons); `graphic` for numbers, dates, headlines, quotes, maps.
  6. `validate` → fix until clean → `render`.
  7. Send `final.mp4` (or `final_small.mp4`) + `credits.txt` with SendUserFile; short Arabic summary.
- [ ] **Step 1: Tests** `test_cli_prep_and_render_end_to_end` (fixture as `--source` local path, fake transcript injected by setting `EDITOR_FAKE_TRANSCRIPT=<path>` env honored by `transcribe` stage, a pre-written valid plan, images stage with no network → fallbacks) → exit 0 and `final.mp4` exists; `test_cli_validate_exit_code` (bad plan → exit 2, Arabic output); `test_prepare_delivery_recompresses` (max_mb tiny → returns `final_small.mp4`, smaller than original).
- [ ] **Step 2:** Run → FAIL. **Step 3:** Implement. **Step 4:** `cd editor && pytest -v` (all, including slow) → PASS.
- [ ] **Step 5:** Commit `feat(editor): CLI, delivery, and editor skill`; push the branch.

---

### Task 11: Real-episode dry run (needs network = Full)

Not code. Blocked until the user switches network access to Full.
- [ ] Record a short test clip request to the user (30–60 s phone video) or use their first real raw episode.
- [ ] Run the skill end-to-end; note wall-clock time per stage in `episodes/<ep>/edit/run-notes.md` (committed; no media).
- [ ] Fix any issue found via `systematic-debugging`, one commit per fix.
