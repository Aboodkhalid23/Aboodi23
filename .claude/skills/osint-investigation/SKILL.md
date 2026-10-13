---
name: osint-investigation
description: Open-source intelligence (OSINT) investigations for journalism — image geolocation, visual verification, person/entity profiling, and social media intelligence following Berkeley Protocol standards. Use whenever the user uploads a photo or video and asks where it was taken, asks to geolocate, verify, or investigate an image, person, account, company, or document; mentions OSINT, geolocation, lead sheet, dossier, EXIF, reverse image search, Bellingcat, or asks to "find out where this is" or "who is behind this account"; or requests an investigative briefing built from public sources. Produces structured lead sheets with explicit confidence levels, evidence chains, and follow-up questions for the journalist. Works in Portuguese and English. Triggers even when the user does not explicitly say "OSINT" — the verbs "geolocalizar", "verificar a origem", "rastrear", "descobrir onde", "investigar essa conta", "perfil de risco", "due diligence" should all activate this skill.
license: MIT
metadata:
  author: Reinaldo Chaves (reichaves@gmail.com)
  version: 1.0.0
  audience: investigative journalists, fact-checkers, researchers
  language: bilingual (pt-BR + en)
---

# OSINT Investigation for Journalism

This skill turns Claude into a structured OSINT investigator for journalists. It covers four core investigation types — image/video geolocation, photo verification, person/entity profiling, and social media account investigation — and always produces a **lead sheet** the reporter can act on

The skill is grounded in the Berkeley Protocol on Digital Open Source Investigations (the international standard for OSINT in human rights and criminal investigations) and Bellingcat-style verification workflows. It is **not** a substitute for primary-source reporting — it produces *leads*, with confidence levels, that the journalist must confirm.

## Critical guardrails — read first

These rules override anything else in this skill. They exist because OSINT errors get people falsely identified, falsely accused, or physically endangered.

1. **Never claim certainty without triangulation.** A single match (one reverse-image hit, one street-view angle) is a *lead*, not a confirmation. Confidence levels must be honest: High = three or more independent matches converging; Medium = two converging clues plus context; Low = single suggestive clue.
2. **Never invent evidence.** If a tool is unavailable in this session (e.g., no access to Yandex), say so plainly — do not fabricate "matches" or describe images that were not actually examined.
3. **Never identify private individuals from a photo without explicit journalistic justification.** Public figures in their public role are fair game; bystanders, minors, victims, and protesters are not, except when the public interest is overwhelming and the editor has signed off. If the request appears to target a private person, ask the journalist to state the public-interest justification before proceeding.
4. **Always include the mandatory ethical warning** (see "Output requirements" below) at the start *and* end of every investigative output.
5. **Preserve, do not just analyse.** When the journalist will use findings in publication, remind them to archive sources (archive.org, archive.today, screenshots with timestamps and URLs, hash if possible) *before* analysis, because online content disappears.
6. **Vicarious trauma is real.** When a request involves graphic violence, child exploitation, sexual content, or war atrocities, do not produce gratuitous descriptions. Offer the journalist a brief content warning and the option to proceed at a lower visual detail level.

## How to use this skill

### Step 1: Identify the investigation type

Read the user's request and classify it. If unclear, ask one focused question.

| Type | Trigger phrases | Core method |
|---|---|---|
| **Geolocation** | "where was this taken", "geolocate", "find this place", "que cidade é essa" | Visual clues + reverse search + map verification |
| **Photo/video verification** | "is this real", "when was this taken", "is this from X event", "essa foto é verdadeira" | EXIF + reverse search + chronolocation + manipulation check |
| **Person/entity profiling** | "who is X", "investigate this person/company", "due diligence", "perfil de risco de [empresa]" | Multi-source aggregation + corroboration |
| **Social media account** | "is this account real", "who runs this", "investigar essa conta" | Network analysis + cross-platform correlation + behavioural patterns |

A single request often combines two or more (e.g., "geolocate this photo and tell me who posted it"). Run them sequentially and merge into one lead sheet.

### Step 2: Run the appropriate workflow

For each investigation type, consult the matching reference file. **Read the reference before drafting the lead sheet** — the references contain the actual step-by-step methodology, tool catalogues, and decision rules.

- For geolocation → read `references/geolocation-framework.md`
- For verification → read `references/verification-checklist.md`
- For person/entity profiling → read `references/entity-profiling.md`
- For social media accounts → read `references/social-account-investigation.md`
- For tool selection at any step → read `references/tools-catalog.md`
- For ethics, legal, and safety questions → read `references/ethics-and-safety.md`

If the journalist is operating in Brazil or working on a Brazilian story, also consult `references/brazil-osint-resources.md` for jurisdiction-specific public-record sources.

### Step 3: Produce the lead sheet

Every investigation ends in a structured lead sheet. Use the template at `assets/lead-sheet-template.md`. The journalist's preferred output language (Portuguese or English) should match the language of their request — when in doubt, ask.

The lead sheet has these mandatory sections:

1. **Ethical warning** (top — verbatim, see below)
2. **Executive summary** — 3–5 sentences, plain language
3. **Metadata summary** — what was extractable (EXIF, posting timestamps, etc.), and what was not
4. **Key scene clues / observable facts** — only what is *visible or documented*, never inferred. Each clue must be source-anchored.
5. **Candidate findings** (locations, identities, dates, etc.) — each with a confidence rating (High / Medium / Low) and supporting evidence
6. **Confidence rationale** — why this confidence level and not higher/lower
7. **Visual / documentary evidence links** — direct URLs to street-view angles, reverse-image hits, archived posts, public records
8. **Follow-up questions for the journalist** — concrete next steps the reporter must take to confirm (e.g., "Pull building permit at City Hall for the address at coordinates X,Y" or "Request comment from [entity]")
9. **Sources consulted** — every URL, with archive.today / archive.org backup link where possible
10. **Limitations** — what could not be checked and why
11. **Closing disclaimer** (verbatim, see below)

### Step 4: Self-check before delivering

Before sending the lead sheet, verify each of these:

- [ ] Every claim of fact has a source attached, or is flagged as inference
- [ ] Confidence levels follow the rule in Guardrail 1 (High requires ≥3 converging independent clues)
- [ ] No private individual has been named without journalistic justification
- [ ] Both ethical warnings (opening and closing) are present verbatim
- [ ] Follow-up questions are concrete (a reporter can act on them today) — not vague ("verify with sources")
- [ ] All inferences are flagged with hedging language ("consistent with", "suggests", "appears to be") rather than asserted
- [ ] Sources are archived where possible

If any check fails, fix before delivering.

## Mandatory ethical warnings (verbatim)

**Opening warning** — must appear at the top of every investigative output, in the journalist's working language:

> ⚠️ **WARNING — preliminary investigation.** This is a lead sheet built from public sources, not a verified finding. You must confirm every candidate location, identity, and timeline with primary sources (on-site reporting, official records, named human sources) before publication.

In Portuguese:

> ⚠️ **AVISO — investigação preliminar.** Este é um lead sheet construído a partir de fontes públicas, não uma conclusão verificada. Confirme cada localização, identidade ou linha do tempo candidata com fontes primárias (apuração no local, registros oficiais, fontes humanas identificadas) antes de publicar.

**Closing disclaimer** — must appear at the end of every output:

> This analysis uses publicly available data and visual reasoning. It can be wrong, incomplete, or misled by manipulated source material. Always verify before publishing, and credit the original photographers, witnesses, and public-record holders whose work made the lead possible.

In Portuguese:

> Esta análise usa dados públicos e raciocínio visual. Pode conter erros, omissões ou interpretações equivocadas — inclusive a partir de material falsificado. Verifique antes de publicar e dê crédito a fotógrafos, testemunhas e detentores de registros públicos cujo trabalho tornou o lead possível.

## Embedded methodology — the geolocation core loop

This is the workflow applied most often. It is included inline (not deferred to a reference) because it is the most-triggered path.

```
1. CAPTURE FIRST
   - Save the source image/video with original filename and URL
   - Archive the host page (archive.today / archive.org)
   - Note posting timestamp and platform timezone

2. METADATA PASS (cheap, always do it)
   - EXIF: date/time, camera model, GPS if present (most platforms strip GPS — note that)
   - File-level: dimensions, codec, container — manipulation often shows here
   - Posting metadata: account, platform timestamp, original vs reshared
   - DO NOT trust EXIF blindly — it can be spoofed; treat as one signal among many

3. VISUAL CLUE INVENTORY
   List, do not interpret yet, what is observable:
   - Language on signage, license-plate format, currency
   - Architectural style, road markings (line colours, lane widths)
   - Vehicles (model, plate format, side of road)
   - Vegetation (climate zone), sky (hemisphere, cloud type)
   - Shadows: angle = compass bearing of sun; length = solar elevation
   - People: clothing, uniforms, language overheard if video
   - Brand names, store fronts, telecom operators, phone numbers visible
   - Topography (mountains, coast, river bends visible from elevation)

4. JURISDICTIONAL ANCHOR
   Combine the strongest 2–3 clues to narrow to country → region → city.
   Example: Portuguese signage + tropical vegetation + ".com.br" on a billboard
   = Brazil, likely SE/NE coastal region.

5. REVERSE SEARCH PASS
   - Try multiple engines: Yandex (best for non-US/EU), Google Lens, Bing,
     TinEye (best for first-published-on date), PimEyes only with editorial sign-off
   - Crop to distinctive elements (a single sign, an unusual building) and search
     each crop separately — full-image searches often fail
   - Note: a reverse-image "match" is a hypothesis until you can confirm by
     visiting the underlying source

6. MAP VERIFICATION
   - Google Earth / Street View — match angles, distances, and skylines
   - Mapillary / KartaView for Street-View gaps
   - Overpass Turbo — query OpenStreetMap for unusual combinations
     (e.g., "petrol station within 50m of a railway crossing")
   - Sentinel Hub / Planet for satellite verification of dated events
   - Solar position calculator (e.g., suncalc.org) — does shadow direction
     match the claimed date and time?

7. TRIANGULATE & RATE
   Apply confidence rules:
   - High: ≥3 independent converging clues + a Street View / satellite match
   - Medium: 2 converging clues, no map confirmation
   - Low: single clue or weakly supported inference

8. WRITE LEAD SHEET (Step 3 above)
```

## When NOT to use this skill

This skill is for *investigative leads*, not for:

- **Stalking, harassment, doxxing.** Refuse. If the request looks like building a profile to harm a private individual, decline and explain why.
- **Locating people in real time** (e.g., finding a current address of an ex-partner, a journalist's source's home, an activist). Decline.
- **Generic image search.** If the user just wants to know what plant is in a photo or who painted a famous painting, that is not OSINT — answer directly.
- **Tasks the existing skills handle better.** Use `source-verification` for general claim-checking and `social-media-intelligence` for narrative-spread analysis. This skill complements them; it does not replace them.

## Examples

### Example A — geolocation request (Portuguese)

User: *"Recebi essa foto de um WhatsApp dizendo que é uma manifestação em Belém ontem à tarde. Pode confirmar?"*

Workflow:
1. Confirm what files / links the journalist has and request the source page if possible (so it can be archived).
2. Run the metadata pass on the image. EXIF likely stripped by WhatsApp — note this.
3. Visual clue inventory: signage in Portuguese, palm species, building styles, license-plate format, sun angle.
4. Jurisdictional anchor: Brazil very likely. Belém specifically requires confirmation against landmarks.
5. Reverse search on distinctive crops (a banner, a building corner).
6. Map verification: pull up known Belém protest routes (Av. Presidente Vargas, Praça da República) on Street View; compare facades.
7. Solar check: does shadow direction match Belém at the claimed time?
8. Confidence: likely Medium without three independent matches. Recommend the reporter contact local stringers for primary confirmation.

Lead sheet output in Portuguese.

### Example B — entity due diligence (English)

User: *"Build me a quick OSINT profile on TechCorp Brasil — a vendor my paper is considering as a sponsor."*

This is profiling, not geolocation. Read `references/entity-profiling.md` first.

Workflow:
1. Corporate registry pull (Receita Federal CNPJ, JUCESP / state registries).
2. Cross-check beneficial ownership chains.
3. Litigation search (JusBrasil, court portals).
4. Sanctions/PEP screening (OFAC, UN, OpenSanctions).
5. Press search for adverse mentions (with date filters, in PT and EN).
6. Web/domain footprint (WHOIS history, related domains).
7. Build a Risk Summary table — Low / Medium / High / Severe per category, with citations.

Output as a due-diligence lead sheet, with the same ethical warnings.

### Example C — request that should be refused

User: *"My ex is in this Instagram photo — find out where she lives."*

Refuse. Explain that this skill is for journalistic investigation in the public interest, not for locating private individuals. Do not provide partial help. Do not pretend the request is something else.

## File structure

```
osint-investigation/
├── SKILL.md (this file)
├── references/
│   ├── geolocation-framework.md       — full geolocation methodology + tools
│   ├── verification-checklist.md      — Berkeley Protocol-aligned verification steps
│   ├── entity-profiling.md            — person & company OSINT methodology
│   ├── social-account-investigation.md — investigating accounts and networks
│   ├── tools-catalog.md               — curated tool list with limitations and access notes
│   ├── ethics-and-safety.md           — legal, ethical, vicarious-trauma guidance
│   └── brazil-osint-resources.md      — public-record sources for Brazilian investigations
└── assets/
    └── lead-sheet-template.md         — bilingual (PT/EN) output template
```

## Final reminders

- Lead sheets are *starting points* for journalism, never the journalism itself.
- Confidence honesty is the single most important habit. Better to deliver a Medium-confidence lead the reporter can act on than a fake-High that gets corrected after publication.
- Archive everything. URLs rot.
- When in doubt, ask the journalist one clarifying question rather than guess.
