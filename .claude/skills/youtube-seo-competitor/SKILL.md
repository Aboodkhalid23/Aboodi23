---
name: youtube-seo-competitor
description: >
  Advanced YouTube competitor intelligence. Detects direct competitors,
  extracts winning title/thumbnail/hook patterns from transcripts, infers
  retention strategies from pacing, correlates posting cadence with
  performance, and identifies format-market-fit gaps. Use when user says
  "YouTube competitor analysis", "what are [channel] doing", "competing
  videos", or "find my competitors on YouTube".
user-invokable: true
argument-hint: "[your-channel-url | niche | keyword]"
allowed-tools:
  - Read
  - Grep
  - Bash
  - WebFetch
  - Agent
---

# YouTube Competitor Intelligence (Advanced)

Competitor analysis on YouTube is about **pattern extraction**, not
imitation. Find what works, understand why, and apply the mechanism
(not the surface form) to the user's channel.

## Process

### 1. Identify competitors

If the user provides a competitor list → use it and add 1-2 mid-tier
comparables. Otherwise derive competitors using **only first-party
sources** (no third-party analytics tools — they rate-limit or error):

- **From target keywords (preferred)**: call the YouTube Data API
  `search.list?part=snippet&type=video&order=viewCount&q={keyword}` for
  the user's 3-5 primary keywords. Cluster the results by `channelId`
  and pick the 5 channels that appear most often in the top 20.
- **API-less fallback**: `yt-dlp "ytsearch20:{keyword}" --flat-playlist
  -J` returns the same ranked list with channel IDs — no API key, no
  scraping.
- **From the user's channel**: read the `relatedPlaylists` +
  `featuredChannelsUrls` (brandingSettings) via the API. As a secondary
  signal, pull the top 10 videos' descriptions via `fetch_channel.py`
  and extract `@handle` / channel-URL mentions.
- **Tier balance**: include 1-2 channels 5-10× the user's subscriber
  size (aspiration) and 2-3 within 2-5× (comparable).

If all of the above fail or the API quota is exhausted, **ask the user
for 3-5 competitor channel URLs directly** rather than falling back to
third-party scrapers.

### 2. Collect per-competitor data

For each competitor (use `scripts/fetch_channel.py` + API where
possible):

- **Channel stats**: subs, total views, video count, join date, country,
  topic IDs
- **Upload cadence**: last 25 videos → median + stddev of days-between
- **Format mix**: long-form / Shorts / live / premiere percentages
- **Top 10 all-time** by view count
- **Top 10 last-90-days** (recent winners — more actionable)
- **Bottom 10 last-90-days** (what is NOT working — as informative as
  the winners)
- **Median stats**: length, views per video, like-to-view ratio,
  comment velocity
- **Playlist structure**: count, median size, top playlist view counts
- **Community tab activity** (last 30 days)
- **Thumbnail contact sheet**: last 12 thumbnails as a 4x3 grid
- **Title corpus**: all titles from last 50 uploads
- **Caption/transcript** for top 5 videos via yt-dlp (used for hook
  extraction)

### 3. Pattern extraction

#### Title patterns
From the title corpus:
- **Length distribution** (median, IQR)
- **Emotional driver frequency**: curiosity / number / contrarian /
  benefit / fear / authority / novelty
- **Keyword position** (primary keyword character index)
- **Extracted formulas**: templates like `How I [Action] in [Time]`,
  `[Number] [Thing] That [Outcome]`, `I Tried [X] for [Time]`, `The
  [Adjective] [Noun] Nobody Talks About`. Deliver 3-5 formulas with
  source video examples.

#### Thumbnail patterns
From the contact sheet:
- Dominant color palette (hex codes)
- Face presence rate, typical facial emotion
- Text treatment (font, size, color, stroke)
- Composition style (close-up face / object / split / montage)
- Brand consistency score
- **Differentiation opportunity**: what stylistic space is *unoccupied*
  in the niche?

#### Hook patterns (from transcripts)
Extract the first 15 seconds of the top 5 videos per competitor:
- **Opening sentence type**: question / bold claim / scene-set /
  pattern-interrupt / promise
- **Time to first payoff**: when does the first valuable information
  or emotional beat hit?
- **Credibility flash timing**: when does the creator establish
  authority?
- **Explicit promise**: at what second does the creator tell the
  viewer what they will get?
- **Common failure**: long intros, logo animations, "hey guys" —
  flag if competitors do this poorly (opportunity for the user)

#### Retention strategy inference (from pacing)
From transcripts + video length:
- **Cuts per minute** (words-per-second proxy)
- **Question-cadence**: how often does the creator pose a question to
  keep attention?
- **Callbacks and loops** (mentions of "I'll come back to this")
- **B-roll density** (inferred from non-spoken gaps)
- **Chapter count per video** (from description)

#### Format-market-fit map
For each competitor, classify their top videos by format:
- Listicle
- Tutorial / how-to
- Documentary / mini-doc
- Reaction
- Case study
- Interview
- Storytime
- Challenge
- Review
- Essay / video essay
- News commentary

Plot format × performance. Formats with disproportionately high median
views are the competitor's "format-market-fit".

### 4. Cadence × performance correlation

Plot upload cadence against recent 90-day view velocity:
- Do competitors who upload 2x/week outperform those at 1x/week?
- Does the day-of-week matter? (cross-reference with Studio audience
  active time if available)
- Is there a "Shorts-per-long-form" ratio that correlates with growth?

### 5. Keyword gap matrix

| Keyword | You | Comp A | Comp B | Comp C | Opportunity |
|---------|-----|--------|--------|--------|-------------|
| ... | ❌ | ✅ | ✅ | ✅ | HIGH — 3 competitors validated, user absent |
| ... | ✅ | ❌ | ✅ | ❌ | MEDIUM — defensible, few competitors |
| ... | ✅ | ✅ | ❌ | ❌ | LOW — user already covers, saturation moderate |

### 6. Entity gap analysis

Extract the Knowledge Graph entities competitors mention most (from
titles, descriptions, transcripts). Compare to the user's entity
coverage. Entities with high competitor coverage and zero user
coverage represent classification gaps.

### 7. Moat identification

Where does the user have a **defensible advantage** that competitors
cannot or do not replicate? Sources of moat:
- Unique access (interviews, locations, data)
- Personal story or authority
- Production quality tier
- Posting speed on time-sensitive topics
- Cross-platform brand (existing Twitter/IG/podcast audience)
- Niche specificity (narrower scope, deeper authority)

## Output

### Competitor Snapshot (one block per competitor)

```
# {Competitor name} — {handle}

Subs: {N}  | Videos: {N}  | Joined: {date}
Topic IDs: {list}
Upload cadence: {median} days, stddev {X}
Format mix: {long %} / {shorts %} / {live %}
Median views/video (90d): {N}
Engagement rate: {%}

Top format: {format} ({X} of top 10 videos)
Winning title formulas:
  - "{pattern}" — e.g. "{actual title}"
  - "{pattern}" — e.g. "{actual title}"

Thumbnail style: {palette}, {face presence %}, {text treatment}
Hook pattern: {summary of first-15s strategy}
Retention strategy (inferred): {cuts/min, callbacks, B-roll density}
```

### Pattern Library (cross-competitor)

- **Title formulas** (3-5, each with competitor sources)
- **Thumbnail patterns** (palettes, composition, text)
- **Hook patterns** (first 15s structures, time-to-payoff distribution)
- **Format-market-fit winners** (formats × niche)
- **Cadence insights** (what posting rhythm correlates with growth)

### Keyword Gap Matrix

As in step 5.

### Entity Gap List

```
Entities mentioned by competitors ≥3x but NEVER by user:
- Entity 1 (topic cluster: X)
- Entity 2 (topic cluster: Y)
- ...
```

### 15-20 Content Ideas

Derived from keyword gaps × format-market-fit × moat. Each idea has:
- Working title (Browse + Search variants)
- Format
- Target keyword
- Why it works for THIS channel specifically
- Estimated difficulty (using formula from `youtube-seo-keywords`)
- Which competitor pattern it borrows + how it differentiates

### Moats

Concrete list of 3-5 defensible advantages with recommended content to
lean into.

### Recommended Experiments (2-4)

Testable hypotheses derived from patterns, e.g.:
- "Test a listicle format — 3 competitors over-index here and we
  haven't tried it. Expected lift: 2× median views if pattern holds."

## Delegation

- After competitor detection, optionally spawn `youtube-seo-keywords`
  to score the keyword gap with the full opportunity formula.
- Optionally spawn `youtube-seo-thumbnail` for a side-by-side
  comparison of the user's top thumbnails against competitor top
  thumbnails.

## Error Handling

| Scenario | Action |
|----------|--------|
| User has no clear competitors | Derive from top 3 target keywords instead |
| Mega-channel competitor only (>10M subs) | Note that tactics may not scale down; include a mid-tier comparable too |
| API quota exhausted | Switch to yt-dlp `ytsearch20:` mode; if still failing, ask user for a 3-5 channel URL list directly — do NOT use third-party scrapers |
| yt-dlp transcript fails | Retry with `--sub-lang en.*,a.en` (auto-caption fallback); if still failing, skip hook analysis with a note — do not guess |
| Channel private or has hidden subs | Analyze only public signals; label subscriber-dependent sections "unknown" |
| No API key | Use yt-dlp only; `tags`, `topicDetails`, `channelKeywords` unavailable — note gaps in the report rather than fabricating |
| WebFetch returns empty (bot detection) | Retry with the canonical `/channel/UC...` URL (more bot-friendly than `/@handle`); if still empty, ask user for channel description paste |
