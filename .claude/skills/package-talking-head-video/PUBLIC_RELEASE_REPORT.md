# Version 0.6.0 verification

## Current refinements

- Added frame-driven keyword markers, presenter-window border drawing, and a one-pass source-to-result indicator in the three device/document diagrams. Motion settles into a readable hold.
- Refined process row spacing, emphasis surfaces, drawing annotations and header contrast. Purple/cyan remain the primary roles, with a restrained warm result/closing accent in both styles. Typography colors pass 4.5:1 contrast checks on stable canvas and panel surfaces.
- 116 tests in 17 files passed. Current real and synthetic preview outputs pass full decode and black-frame checks; source color and the single continuous audio track are preserved.
- Real preview SHA-256: `79A53894D87D98ACF1324CA325337283120CCCDEFFA36C821EE739D07C28B8C0`.
- Visual samples are engineering review. Full continuous playback and user acceptance are recorded separately.

## Previous version 0.5.0 verification

## Current additions

- Source-grounded semantic line drawings are available in single-presenter composition. Three new diagrams and the six existing illustrations share the same frame-driven SVG pipeline, normalized drawing progress and explicit ink for dark/paper styles.
- README no longer presents old V2 screenshots as homepage examples. Current public screenshots are generated from the reproducible synthetic example and labeled accordingly.
- 114 tests in 17 files and TypeScript checks passed. Current synthetic and real local preview outputs pass full decode and black-frame checks.
- The local talking-head preview uses phone mirroring, note collection and Agent-output diagrams without changing the continuous source audio or SRT. Entry/hold/exit stills are checked for the added drawing regions; full playback and user acceptance are recorded separately.
- Preview SHA-256: `74A24D55C465DCCC16FD152BE0036C883CD08D40A44E5D09D9F23516A66A6936`.

## Previous version 0.4.0 verification

## Current behavior

Composite jobs use one continuous presenter video with full-frame emphasis, single-window left/right editorial composition, source-excerpt typography and frame-driven layout transitions. Source captions are redrawn once after cropping the original caption reserve. Original-layout jobs and historical V2 inputs remain readable. Transparent output does not support presenter windows.

## Current verification

- 112 tests in 17 files and TypeScript checks passed.
- Reproducible 8-second geometric example covers title/card/flow and dark/paper screenshots; no real person is represented by the synthetic source.
- A 14.5-second local talking-head preview uses source-grounded emphasis and seven timed beats. Output is H.264/AAC, 1920x1080, 30fps, 434 video frames, one audio track.
- Preview SHA-256: `2DE3B351B8DC443F4EC646D933C749D3F140A1C2E42695F2A7FD43C621F256D0`.
- Full decode and black-frame checks passed. Scene entry/hold/exit frames and representative timeline frames were inspected. Original media and local preview files remain outside the public repository.
- Full continuous playback and user acceptance are not claimed.

## Previous version 0.3.0 verification

## Current scope

New CLI jobs default to public-lite: three basic layouts (title/card/flow), two styles (dark/paper), optional bounded 1.06x presenter emphasis, original continuous voice, complete source-based captions and artifact verification. Historical V2 code remains readable and stays accessible in Git history.

Automated checks and sampled frames are engineering evidence; they do not establish user acceptance.

## Verification performed

- 109 automated tests passed; TypeScript checks, composition build, Skill format and public-file scan passed.
- Refreshed vulnerable transitive dependencies and Vitest to 4.1.11; npm audit reports zero vulnerabilities. Overlay argument tests accept native path separators on Windows and Linux.
- A local 39.9-second video job used source video and matching SRT with recorded input hashes.
- Public-lite output: 1920x1080, 30fps, H.264/AAC, 1197 video frames, 39.914667 seconds, one audio track.
- Output SHA-256: `43B81A03FDC78799F3ACC318848E71847E3FAF9BE6EC2EC26DD58051A7BEAF5D`.
- All three layouts were used with one consistent palette. Dark and paper style stills and a 1280x720 still were checked.
- Full FFmpeg decode passed; no black intervals detected. All layout stills, eight timeline samples and first/last frames were inspected.
- No full continuous playback review or user acceptance is claimed. Private job videos, source files, subtitles and screenshots remain outside the public candidate set.

## Historical report

The following report describes the old release, not the current public-lite output.

# Public release report

## Scope

- Repository target: `zhouyuechuan2025-ui/ai-self-media-video-packaging-skill`.
- Visibility target: public.
- Default renderer: Remotion.
- Optional adapter: HyperFrames.
- Public capabilities: 18 visual structures, 10 deterministic motion primitives, and 6 programmatic line-illustration scenarios.
- Workflow: plan first, wait for explicit confirmation, then implement; export remains separately gated.

## Real invocation evidence

- Case: `auto-editing-0`.
- Source video: 49.272993 seconds, HEVC/AAC, 1920×1080, 30fps.
- SRT: 21 cues; burned-in subtitle mode.
- Director plan: 21 beats, 6 palettes, 13 structures, 9 left placements, 8 right placements, and 4 short full-screen placements.
- Final local output: H.264/AAC, 1920×1080, 30fps, 49.322667 seconds, 38,520,178 bytes.
- Output SHA-256: `57D909FAABE95A68862C0418A4E110EC9BD557B79D3FDEE07FC0545C847679A8`.
- Full FFmpeg decode: pass.
- Black-frame scan: no black interval detected.
- Six README previews and a ten-frame contact sheet: extracted from that exact output and individually hashed in `examples/auto-editing-0/preview-manifest.json`.

The source MP4, source SRT, full output MP4, local paths, and private assets are intentionally absent from the public candidate set.

## Independent renderer checks

### Remotion

- Real authorized case render: pass.
- Repository synthetic fixture render: pass, 120/120 frames.
- Composition discovery/build: pass.

### HyperFrames 0.7.99

- Generated from the repository synthetic fixture.
- Lint: 0 errors, 0 warnings.
- Dynamic check: `ok=true` using installed system Chrome after the bundled headless shell failed to launch on this Windows host.
- Runtime: 0 errors.
- Layout: 9 samples, 0 findings.
- Motion: enabled, 81 samples, 0 findings.
- Contrast: 10/10 passed.
- Snapshots: 5 generated, 0 finding crops.

## Publication safety

- Public candidate scan checks source media, local absolute paths, credentials, private keys, files over 20MB, unfinished markers, and non-public terminology.
- Production dependencies audit: 0 vulnerabilities.
- README final line is locked by test to the approved current business WeChat `nanaya093`.
- Original media is ignored and not present in Git candidates.
- Repository stays `private: true` at the npm package level to prevent accidental npm publication; this does not affect GitHub visibility.

## Current state

Published publicly at <https://github.com/zhouyuechuan2025-ui/ai-self-media-video-packaging-skill>.

- Initial public commit: `4e5d98a595f98d8b387cf0e8476df2d9c159d3b2`.
- Default branch: `main`.
- Repository visibility: public.
- Remote read-back: completed for the repository metadata, README, `SKILL.md`, package manifest, real-case preview manifest, and public file tree.
- Publication boundary: pushed to GitHub only; not deployed, released to npm, or published elsewhere.
