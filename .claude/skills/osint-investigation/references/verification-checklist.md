# Verification Checklist — Berkeley Protocol-aligned

For verifying that a photograph or video is what its publisher claims it is. Built around the Berkeley Protocol on Digital Open Source Investigations (UN/UC Berkeley, 2022).

## When to read this file

Read when the journalist is asking *whether* a piece of content is genuine, not just where it was taken. Typical triggers:

- "Is this real?"
- "Has this been altered?"
- "Did this actually happen on [date]?"
- "Is this from the event the source claims?"

## The five Ws of verification

The Berkeley Protocol structures verification around five questions. Answer each, with evidence.

### 1. Who?

- Who posted the content? (account, real name if known, history, prior posts)
- Who created the content? (often different from poster — original creator vs aggregator)
- What is the relationship between the poster and the events depicted?
- Has the account been verified by the platform? (Note: platform verification ≠ identity verification)

### 2. What?

- What does the content show? — describe only what is *visible*, not what is *claimed*
- What claims is the publisher making about the content?
- Are the claims and the content consistent? (e.g., a "drone strike video" that shows fireworks)

### 3. Where?

- Run the geolocation workflow (`geolocation-framework.md`).
- Specifically: does the location in the image match the location claimed by the publisher?

### 4. When?

This is **chronolocation**. Strategies:

- **EXIF date** (rare, often stripped, sometimes spoofed — one signal among many).
- **Solar shadow analysis** — does shadow direction and length match the claimed date and time at the claimed location? Use suncalc.org.
- **Weather verification** — pull historical weather for the claimed location and date (e.g., wunderground.com archive, NOAA). If the image shows clear skies but it was raining, that is a discrepancy.
- **Satellite verification** — Sentinel-2 imagery for the date in question can confirm or deny whether something visible in the image (a fire, a flood, a building, a crowd) was there on the claimed date.
- **Reference objects** — a stadium-naming sponsor, a campaign poster, a seasonal decoration, a specific car model can constrain the year. Wikipedia for "[brand] Brazil sponsorship history" often nails this within minutes.
- **Reverse-image first-appearance** — TinEye's earliest hit gives the upper bound on when the image could have been taken.

### 5. Why?

- Why is this content being shared *now*?
- Who benefits from people believing it?
- Is there a coordinated campaign sharing it (multiple accounts, identical wording)?

The "why" question is part of source verification, not just content verification, and overlaps with `social-media-intelligence` skill.

## Manipulation checks

### Direct file-level checks

- **File metadata mismatch** — date the image was created vs date the file was last modified. Big gaps suggest editing.
- **Compression artefacts** — a JPEG that has been re-saved many times shows blockiness; an image that has been spliced often shows different compression in different regions (visible in **error-level analysis** tools like FotoForensics).
- **Resolution inconsistency** — composited images often show pixel-grid mismatches between regions.

### Visual checks

- **Shadows** — all shadows in the image must point consistent with a single light source (or the lighting must be obviously diffuse). Inconsistent shadows = composite.
- **Reflections** — what is reflected in glass, water, eyeglasses, polished surfaces? Reflections often betray composites.
- **Perspective** — straight lines that converge inconsistently with the rest of the scene betray paste-ins.
- **Edges** — composited objects often show telltale blur, halos, or hard edges that do not match the surrounding image's softness.

### AI-generated content checks (2026)

Modern image generators are very good. Things that still tend to fail:

- **Hands and fingers** — count fingers, check joint placement, look for fused or extra digits
- **Ears** — asymmetric, missing detail, or anatomically odd
- **Eyeglasses** — frames that do not match across the bridge, lenses with different distortion
- **Text** — large text often looks plausible at a glance but is gibberish on close reading
- **Reflections** — generators struggle with consistent multi-surface reflections
- **Crowds** — repeated faces, fused people, impossible body positions in the background

Detection tools (Hive, Sensity, Optic, open-source detectors) help but are imperfect — a "75% likely AI-generated" verdict is a lead, not a confirmation. Always combine with manual inspection.

### Video-specific checks

- **InVID / WeVerify** plug-in — splits video into keyframes and lets you reverse-search each. Essential for videos.
- **Frame-rate consistency** — sudden changes in motion smoothness can suggest splicing.
- **Audio analysis** — does ambient sound match the visual environment? Is the audio clean while the video is shaky (suggests overdubbed)?
- **Reflection / shadow continuity across frames** — composited people in moving footage often show shadow-direction errors that are stable in stills.

## Preservation — the chain of custody

Berkeley Protocol's biggest contribution to journalism: **collect before you analyse**. If a story will be published or used in court, the evidence must be preserved.

For each piece of source content:

1. **Save the original file** — do not edit, do not re-encode. Keep the file the platform served.
2. **Capture the source page** — full HTML and screenshot. Tools: SingleFile (browser extension), Hunchly (paid, designed for this).
3. **Archive the URL** — submit to archive.today *and* archive.org. Two archives, because either can fail.
4. **Hash the file** — SHA-256 hash recorded with timestamp. This proves the file you have today matches what you collected.
5. **Log the time of collection** — UTC. Note the platform's claimed posting time and your collection time separately.
6. **Note your tooling** — which browser, which extension, which OS. This is the chain-of-custody footnote that lets a reader, editor, or court reproduce your work.

Berkeley Protocol's detailed templates are open and can be adapted for newsroom use.

## Output format for verification investigations

A verification lead sheet adds these sections to the standard template:

- **Claim under verification** — exact wording of what the publisher said
- **Verdict** — Confirmed / Partially confirmed / Inconclusive / Disputed / False
- **Five-Ws table** — Who/What/Where/When/Why with evidence column
- **Manipulation findings** — what you tested, what you found, what was inconclusive
- **Preservation log** — files saved, URLs archived, hashes, timestamps

The verdict scale must be honest:

- **Confirmed** — multiple independent corroborations of all five Ws
- **Partially confirmed** — some elements confirmed, others not (specify which)
- **Inconclusive** — evidence insufficient to verify or debunk
- **Disputed** — corroborated and contradictory evidence both exist
- **False** — at least one core claim contradicted by evidence

## Vicarious trauma — protecting the journalist

Verification work involves looking at, sometimes repeatedly, graphic and disturbing content. The Berkeley Protocol formally addresses this. Practical safeguards:

- Lower the screen brightness and shrink the playback window
- Mute audio when not analytically needed
- Set a time-box (e.g., max 30 minutes of graphic content per session)
- Take regular breaks; do not verify late at night
- Talk to a colleague or trauma-aware professional if material is affecting sleep or mood

Resources: Dart Center for Journalism and Trauma (dartcenter.org). When the content is severe, recommend the journalist read the Dart Center guides before continuing.

## References

- Berkeley Protocol on Digital Open Source Investigations: https://humanrights.berkeley.edu/publications/berkeley-protocol-on-digital-open-source-investigations/
- First Draft / Bellingcat verification handbooks: https://www.bellingcat.com/resources/how-tos/
- Dart Center vicarious trauma resources: https://dartcenter.org/
