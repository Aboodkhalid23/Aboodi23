# المونتير 1ب — الجودة واللهجة Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Output keeps the raw footage's quality (resolution up to 4K, 30/60 fps, one final lossy encode, HDR tone-mapped), a fast preview render exists, Iraqi speech is corrected against the episode script, and YouTube chapters are produced.

**Architecture:** A per-episode `work/format.json` (canvas W×H, fps) decided in `fetch` drives every later stage. Intermediates are near-lossless (CRF 10 veryfast); beat clips are the single final-quality encode (CRF 16 medium) and are concatenated with stream copy. A new `align.py` rewrites transcript words from the script with `difflib`. Preview = the same compose into `work/preview/` at 640×360.

**Tech Stack:** as part 1 (ffmpeg with zscale/tonemap, faster-whisper `hotwords`/`initial_prompt`, Remotion `--scale`).

**Spec:** `docs/superpowers/specs/2026-09-27-editor-v2-quality-dialect-features.md` sections أ، ب، ج، ز (chapters + preview only).

## Global Constraints
- Canvas tiers (16:9): source landscape height ≥ 2160 → 3840×2160; ≥ 1440 → 2560×1440; else 1920×1080. Portrait/odd sources are fitted inside the canvas (pad with style paper colour for face beats is out of scope; black pad is fine).
- FPS: 60 if source avg fps ≥ 50, else 30.
- Intermediate encodes (`source.mp4`, `clean.mp4`, Remotion output): `-crf 10 -preset veryfast` (Remotion `--crf=10`). Beat clips (final quality): `-crf 16 -preset medium`. `final.mp4` = stream copy of beat clips + AAC 192k audio.
- HDR input (color_transfer `arib-std-b67` or `smpte2084`) is tone-mapped to bt709 SDR in `fetch`.
- Delivery never re-encodes unless `--max-mb` is passed.
- Preview: 640×360, same fps, `-preset ultrafast -crf 28`, Remotion `--scale` = 640/1920, files in `work/preview/`, output `edit/preview.mp4`.
- All user-facing text Arabic.

## Review Focus
1. 4K 60 fps source → compose must not silently fall back to 1080/30 anywhere (graphics, face frame, audio length math uses fps from format).
2. Script with Markdown headers, `[ملاحظات]`, emojis, and numbers written as digits vs words → alignment still matches; match ratio reported.
3. Speaker ad-libs a whole paragraph not in the script → those words keep their transcribed text and timing.
4. Chapter list with a first chapter not at 0 or chapters < 10 s apart → validator error, not a broken description.
5. Preview and full render share a cache folder by mistake → full render would reuse low-res clips (must be separate).

---

### Task 1: Format decision, quality-preserving fetch, HDR

**Files:** Modify `editor/pipeline/fetch.py`, `editor/pipeline/paths.py` (add `format_file` = `work/format.json`); Create `editor/pipeline/fmt.py`; Test `editor/tests/test_fetch.py`

**Interfaces:**
- Produces: `Format` dataclass `(width: int, height: int, fps: int)`; `decide_format(info: MediaInfo) -> Format` (tiers above); `load_format(ep) -> Format` (defaults to 1920×1080@30 if file missing); `save_format(ep, fmt)`.
- `fetch` no longer downscales: scales only down to fit the canvas box, keeps aspect, sets fps, `-crf 10 -preset veryfast`, tone-maps HDR with `zscale=t=linear:npl=100,format=gbrpf32le,zscale=p=bt709,tonemap=hable:desat=0,zscale=t=bt709:m=bt709:r=tv,format=yuv420p`, tags output bt709. Writes `format.json`.

- [ ] Tests: `test_decide_format_tiers` (3840×2160→4K canvas; 2560×1440→1440; 1280×720→1080; fps 59.94→60, 25→30); `test_fetch_keeps_4k` (synthetic 3840×2160 2 s → `source.mp4` 3840×2160, format.json 3840×2160@30); `test_fetch_60fps_stays_60`; `test_fetch_tonemaps_hdr` (synthetic clip tagged `-color_primaries bt2020 -color_trc arib-std-b67 -colorspace bt2020nc` → output color_transfer `bt709`). Update `test_fetch_rotated_is_upright` expectation: height stays 1280 (no downscale needed; fits 1920×1080 box? — rotated 720×1280 exceeds 1080 height, so height == 1080 still holds).
- [ ] Run → FAIL; implement; run → PASS; commit `feat(editor): keep source quality, 4K/60fps canvas, HDR tone-map`.

### Task 2: Compose at canvas quality + single final encode + preview

**Files:** Modify `editor/pipeline/clean.py` (FPS/SAMPLES from format; `-crf 10 -preset veryfast`), `editor/pipeline/compose.py`, `editor/pipeline/graphics.py` (`scale: float` param → `--scale`, `--crf=10`), `editor/pipeline/deliver.py` (only when max_mb given), `editor/pipeline/__main__.py` (`render --preview`, `deliver --max-mb`); Test `editor/tests/test_compose.py`, `editor/tests/test_cli.py`

**Interfaces:**
- `compose(ep: Episode, preview: bool = False) -> Path` — canvas/fps from `load_format`; preview → 640×360, clips in `work/preview/`, output `ep.edit / "preview.mp4"`; full → `ep.final`. `FRAME_BOX` scales with canvas (0.6 of W×H, centred at (0.2W, 0.2H)); Remotion `--scale = W / 1920`.
- `snap_to_frames` and `SAMPLES_PER_FRAME` take fps from format (48000 // fps).
- `prepare_delivery(ep, max_mb: float | None = None) -> Path` — `None` → return `ep.final` untouched.

- [ ] Tests: `test_compose_4k_canvas` (slow: 4K synthetic source, 3 beats incl. one graphic → final 3840×2160, graphic frame 3840 wide); `test_preview_is_small_and_separate` (slow: preview.mp4 640×360; `work/preview/beat_0.mp4` exists and `work/beat_0.mp4` untouched); `test_final_is_single_generation` (final video stream bitrate > preview's ×4 — sanity, and beat clips encoded with `crf=16` read from x264 SEI `ffprobe -show_entries stream_tags` / `strings` contains `crf=16.0`); `test_delivery_untouched_by_default`.
- [ ] Update existing compose tests for format (1080/30 fixture unchanged).
- [ ] Run → FAIL; implement; run full suite → PASS; commit `feat(editor): full-quality compose, single final encode, preview render`.

### Task 3: Iraqi dialect — script alignment + vocabulary prompt

**Files:** Create `editor/pipeline/align.py`; Modify `editor/pipeline/transcribe.py`, `editor/pipeline/__main__.py` (`prep --script PATH`); Test `editor/tests/test_align.py`, `editor/tests/test_transcribe.py`

**Interfaces:**
- `script_words(text: str) -> list[str]` — strips Markdown (`#`, `*`, `>`, `|`, links `[t](u)` → `t`), bracketed `[...]` and parenthesised `(...)` notes, emojis/symbols; returns words.
- `find_script(ep: Episode) -> Path | None` — newest `*final*.md` in `ep.root`, else `02-draft.md`, else None.
- `align_words(words: list[Word], script: list[str]) -> tuple[list[Word], float]` — `difflib.SequenceMatcher(None, [normalize_ar(w.text)], [normalize_ar(s)], autojunk=False)`; `equal` keep; `replace` → script words over the span's time, split proportionally to character length; `delete` keep; `insert` drop. Returns (words, ratio of transcript words inside `equal`+`replace` blocks).
- `align(ep, script_path) -> float` — saves raw to `work/transcript_raw.json`, aligned to `ep.transcript`, prints warning `الكلام يختلف هواية عن السكربت` if ratio < 0.5.
- `transcribe(..., model_name="large-v3")`; passes `initial_prompt=IRAQI_PROMPT` and `hotwords` = contents of `edit/vocab.txt` joined by spaces when present. `IRAQI_PROMPT = "هلا بيكم، اليوم راح نحچي عن قصة غريبة. شلون صار هيچ؟ خلي نشوف شنو الي صار بالضبط."`

- [ ] Tests: `test_script_words_strips_markdown`; `test_align_fixes_misheard_words` (heard `شركه ايفر غراند كانت اكبر` vs script `شركة إيفرغراند كانت أكبر` → texts from script, first/last timestamps unchanged); `test_align_keeps_adlib` (extra 4 heard words absent from script keep text+timing); `test_align_ratio_low_warns`; `test_transcribe_passes_prompt_and_hotwords` (FakeModel records kwargs; vocab.txt `إيفرغراند\nهوي كا يان` → hotwords contains both).
- [ ] Run → FAIL; implement; run → PASS; commit `feat(editor): correct Iraqi transcription against the script`.

### Task 4: YouTube chapters

**Files:** Modify `editor/pipeline/plan.py` (`EditPlan.chapters: list[dict]` default `[]`; validation), Create `editor/pipeline/chapters.py`; Modify `__main__.py` (`render` writes chapters); Test `editor/tests/test_chapters.py`

**Interfaces:**
- Chapter dict `{"t": float (cleaned timeline), "title": str}`.
- Validation (only when chapters non-empty): first `t` == 0; ascending; gaps ≥ 10 s on the final timeline; at least 3 chapters (YouTube rule). Errors prefixed `chapter <i>:`.
- `write_chapters(plan: EditPlan, path: Path) -> Path` — first chapter at `00:00` (covers teaser), others at `t + teaser_total`; format `mm:ss title` (or `h:mm:ss` past an hour).

- [ ] Tests: `test_chapter_times_shift_by_teaser`; `test_first_chapter_must_be_zero`; `test_chapters_too_close`; `test_hour_format`.
- [ ] Run → FAIL; implement; run → PASS; commit `feat(editor): YouTube chapters from the plan`.

### Task 5: Skill + docs update

**Files:** Modify `.claude/skills/editor/SKILL.md`, `editor/styles/README.md` (no change unless needed), spec part 1 note.

- [ ] SKILL: step "write `edit/vocab.txt` (≤40 names/terms from `01-research.md`, one per line) before prep"; prep takes `--script`; after plan → `render --preview` first, send preview, full `render` after owner says ok; `chapters` in plan (3+, first at 0); no captions anywhere; deliver sends original file, `--max-mb` only if chat refuses.
- [ ] Run full suite (`-m "slow or not slow"`) → PASS; commit `docs(editor): skill steps for vocab, preview, chapters`; push.
