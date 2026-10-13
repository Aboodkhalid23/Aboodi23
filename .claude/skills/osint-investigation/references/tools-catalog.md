# Tools Catalog — OSINT for Journalism

A curated tool list for OSINT investigations, with **honest limitations** noted. Inspired by Bellingcat's Online Investigation Toolkit, but trimmed to the tools most useful for journalists in 2026

This is not a complete tool dump. The aim is fewer tools, better understood. When the investigation needs something niche, search Bellingcat's full toolkit (https://bellingcat.gitbook.io/toolkit) or GIJN's resource centre.

## How to read this file

For each tool: **what it does → when to use → limitations / cost**. Limitations are the most important field — many tools advertised as "OSINT" are unreliable, paywalled at the wrong tier, or already discontinued.

---

## Image and reverse search

### Yandex Images
- **What:** Reverse-image search, with strong vision model.
- **Use for:** Non-US/EU content; faces; buildings; "this object somewhere in the world".
- **Limits:** Russian-government-aligned company; some users prefer to access via VPN; results bias toward content indexed in CIS countries. Free.

### Google Lens
- **What:** Reverse-image search with strong product and text recognition.
- **Use for:** US/EU content, products, OCR on signage, plant / animal ID.
- **Limits:** Weak on faces (deliberately); skews to commerce results. Free.

### Bing Visual Search
- **What:** Reverse-image search.
- **Use for:** Sometimes catches what Google and Yandex miss.
- **Limits:** Weaker model than the above two for most queries. Free.

### TinEye
- **What:** Finds the *first known appearance* of an image online, with crawl date.
- **Use for:** Determining whether an image is recycled / re-shared from earlier. Indispensable for verification.
- **Limits:** Indexes only what it has crawled — coverage is patchy outside English-language web. Free tier sufficient for most uses; paid for API.

### PimEyes
- **What:** Face-search across the open web.
- **Use for:** *Only* when the journalist has explicit editorial sign-off and a public-interest justification. Identifying public figures from photos.
- **Limits:** Privacy-fraught — results can include ordinary people's photos from old social-media profiles. **Default: do not use.** Subscription required.

---

## Metadata and forensics

### ExifTool
- **What:** Command-line tool that reads (and writes) image and video metadata.
- **Use for:** EXIF extraction, PDF metadata, video container metadata.
- **Limits:** EXIF can be spoofed; treat as one signal. Free / open source.

### FotoForensics
- **What:** Web-based forensic image analysis (Error Level Analysis, metadata, JPEG quality).
- **Use for:** First-pass manipulation check.
- **Limits:** Heuristics, not proofs. ELA artefacts can be misread. Free.

### InVID / WeVerify browser extension
- **What:** Splits videos into keyframes for reverse search; magnifier; metadata.
- **Use for:** Any video verification.
- **Limits:** Browser extension; not a deep forensic tool. Free.

---

## Maps and Earth

### Google Earth Pro
- **What:** Satellite imagery with historical-imagery slider; overlay tools; measurement.
- **Use for:** Skyline matching, building footprint, dated satellite verification.
- **Limits:** Imagery dates are not regular — gaps of months or years. Free.

### Google Street View
- **What:** Street-level panoramas.
- **Use for:** The single most important geolocation tool. Match angles, signs, facades.
- **Limits:** Coverage is poor in many countries; imagery may be years out of date. Free.

### Mapillary
- **What:** Crowdsourced street-level imagery, open data.
- **Use for:** Filling Street View gaps; verifying changes between Street View captures.
- **Limits:** Coverage very patchy. Free.

### KartaView
- **What:** Similar to Mapillary, separate database.
- **Use for:** Cross-checking Mapillary or where Mapillary lacks coverage.
- **Limits:** Even patchier than Mapillary. Free.

### OpenStreetMap + Overpass Turbo
- **What:** OpenStreetMap is the data; Overpass Turbo is the query tool.
- **Use for:** "Find every X within Y of Z" — narrowing candidate locations from a feature list. E.g., petrol stations within 50 m of railway crossings.
- **Limits:** Requires writing Overpass QL queries (Bellingcat's GUI helps for non-coders). Coverage uneven globally.

### Sentinel Hub EO Browser
- **What:** Free Sentinel-2 satellite imagery (~10 m resolution, refreshes ~5 days).
- **Use for:** Dated satellite verification — was a fire visible? Was a building there?
- **Limits:** 10 m resolution insufficient for individual vehicles or small structures. Free for journalists.

### Planet Explorer
- **What:** Daily ~3 m satellite imagery.
- **Use for:** Higher-resolution dated verification.
- **Limits:** Paid; some access via journalism partnerships (Planet has an Education and Research Program).

### SunCalc.org / SunCalc.net
- **What:** Calculates sun position for any latitude/longitude/date/time.
- **Use for:** Chronolocation — does the shadow direction match the claim?
- **Limits:** Assumes a clear sky; diffuse light makes shadow analysis impossible. Free.

### PeakVisor
- **What:** Mountain-identification app for hikers, used by OSINT for matching skylines to known peaks.
- **Use for:** Identifying mountains visible in a photo.
- **Limits:** Designed for hikers — interface assumes you are roughly there. Free / paid tiers.

---

## Corporate, sanctions, and public records (global)

### OpenCorporates
- **What:** Global corporate registry aggregator.
- **Use for:** Initial company lookup across many jurisdictions.
- **Limits:** Coverage uneven; data freshness varies; Brazilian coverage is partial. Free / paid API.

### OpenOwnership
- **What:** Beneficial-ownership data aggregator.
- **Use for:** Tracing who really owns a company.
- **Limits:** Only as good as the source jurisdictions' disclosures (which are often poor). Free.

### OpenSanctions
- **What:** Sanctions, PEPs, and watchlists aggregated globally.
- **Use for:** Quick sanctions-screening of any name.
- **Limits:** False positives common with common names — always confirm against the source list. Free / paid.

### OFAC SDN list
- **What:** US Treasury's Specially Designated Nationals list.
- **Use for:** Authoritative US sanctions check.
- **Limits:** US-centric. Free.

### Aleph (OCCRP)
- **What:** OCCRP's investigative-data repository — leaks, registries, court records.
- **Use for:** Cross-jurisdictional searches; finding a name across many leaks at once.
- **Limits:** Free for journalists with verified access; some datasets restricted.

### ICIJ Offshore Leaks Database
- **What:** Aggregated leaked offshore data (Panama Papers, Pandora Papers, etc.).
- **Use for:** Specific offshore-structure searches.
- **Limits:** Only includes the leaks ICIJ has processed. Free.

### LittleSis
- **What:** Database of US elite networks (officials, donors, executives).
- **Use for:** US connection-mapping.
- **Limits:** US-only. Free.

---

## Identity and account discovery

### Sherlock
- **What:** Open-source CLI: input a username, get a list of platforms where that username exists.
- **Use for:** Finding the same handle on Reddit, Twitter, GitHub, etc.
- **Limits:** Same-username ≠ same-person; many false positives. Free.

### WhatsMyName
- **What:** Web-based equivalent to Sherlock with a curated platform list.
- **Use for:** Same as Sherlock, friendlier interface.
- **Limits:** Same as Sherlock. Free.

### Maigret
- **What:** Sherlock-style but with deeper output (some profile metadata).
- **Use for:** When Sherlock returns too few hits.
- **Limits:** Same false-positive risk. Free.

### Hunter.io
- **What:** Email pattern inference for company domains.
- **Use for:** Determining a company's email format ([first].[last]@company.com etc.).
- **Limits:** Do not use to harass. Free / paid tiers.

### Epieos / Holehe
- **What:** Free email-presence checks across services.
- **Use for:** Confirming an email exists on platforms (without password resets).
- **Limits:** Coverage limited; results are not legal proof. Free.

---

## Domain and infrastructure

### Wayback Machine (archive.org)
- **What:** Largest web archive.
- **Use for:** Historical website state; deleted pages; deleted social-media posts (sometimes).
- **Limits:** Some pages were never crawled; some have been retroactively removed. Free; submit explicit captures of what you find.

### archive.today (also archive.ph, archive.is)
- **What:** Alternative web archive.
- **Use for:** When a page blocks archive.org; preserving social-media posts; politically sensitive content.
- **Limits:** Captchas; intermittent reliability. Free.

### DomainTools / ViewDNS / WhoisFreaks
- **What:** Current and historical WHOIS data.
- **Use for:** Tracing domain ownership over time.
- **Limits:** GDPR has masked most personal WHOIS data since 2018. Mostly paid for historical data.

### BuiltWith / Wappalyzer
- **What:** Identify the technologies a website is built on (analytics IDs, tag managers, hosts).
- **Use for:** Linking websites that share infrastructure.
- **Limits:** Free tiers limited.

### SpyOnWeb / DNSlytics
- **What:** Surface websites sharing the same Google Analytics or AdSense ID.
- **Use for:** Networks of related websites with the same operator.
- **Limits:** Modern operators often rotate IDs. Free / paid.

---

## Network analysis and visualisation

### Maltego
- **What:** Visual entity-link analysis platform with many "transforms" (data connectors).
- **Use for:** Building investigative graphs.
- **Limits:** Steep learning curve; many useful transforms are paid. Community Edition free.

### Gephi
- **What:** Open-source network visualisation.
- **Use for:** Visualising large networks once data is collected.
- **Limits:** Requires data prep. Free.

### Kumu
- **What:** Web-based network visualisation; collaborative.
- **Use for:** Sharing network maps with editors.
- **Limits:** Free tier limited; pay for private maps. Free / paid.

### CruzaGrafos
- **What:** Brazilian-focused network analysis on 89M+ public records.
- **Use for:** Brazilian corporate / political / litigation networks.
- **Limits:** Brazilian focus. Free for journalists with verified access.

---

## Newsletters and communities (for staying current)

- **Bellingcat newsletter** — fortnightly conflict/disinformation/HR investigations
- **Sector035 — Week in OSINT** — weekly tool updates and techniques
- **OSINT Curious** — weekly community roundup
- **GIJN** (Global Investigative Journalism Network) — investigative-journalism-specific resources
- **DFRLab Digital Sherlocks** — disinformation tracking

## A note on tool churn

OSINT tools die. Twint died in 2022 when X cracked down on scraping. CrowdTangle was killed by Meta in 2024. Whatever specific tools are listed above will, on a multi-year horizon, partially go stale. The skill prioritises **method** over tool — when a tool dies, a method survives.

When recommending a tool to the journalist, sanity-check it is still alive in 2026 with a quick web search before you cite it.
