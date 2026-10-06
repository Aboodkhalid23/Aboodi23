# Entity Profiling — Person and Company OSINT

For building a profile of a person, organisation, or company from public sources, for journalism purposes

## When to read this file

Read when the journalist asks for:

- Background on a person ("who is X")
- Due diligence on a company or NGO (sponsor vetting, source vetting, story subject)
- Beneficial-ownership tracing
- A risk profile of an entity

## Critical guardrails for entity profiling

1. **Public-interest justification first.** For private individuals (people who are not public figures and have not voluntarily entered public life), profiling requires a journalistic public-interest justification. Ask the journalist to state it before proceeding. "I am writing a story about X because Y" — write it down and keep it with the file.
2. **Public figures vs private figures.** Public officials, executives of major companies, politicians, owners of regulated businesses are public figures *in their public roles*. Their private lives (medical records, family members not involved in their public role, romantic partners) remain private.
3. **Never profile minors.** Even if the parent is a public figure, do not investigate the child.
4. **Distinguish allegations from findings.** "Mentioned in a press article" ≠ "guilty". Report what was reported, with citation, and flag whether the case has gone to court / been adjudicated / is under investigation.

## Methodology — the five layers

Profile an entity by working outward through five concentric layers. Each layer adds context but also adds room for error — the further out you go, the more aggressive the corroboration must be.

### Layer 1: Identity confirmation

Before you investigate someone, confirm you have the right person. Common failure: confusing two people with similar names, especially in countries with common surnames.

For a person:
- Full name including middle name(s) where culturally relevant
- Date of birth (or at least year)
- A second identifier: place of birth, profession, employer, or photograph

For a company:
- Full registered name (often differs from trading name)
- Tax ID / corporate registry number (Brazil: CNPJ; US: EIN; UK: Companies House number)
- Country of registration
- A second identifier: registered address, founding date, or director's name

If you cannot confirm Layer 1 to high confidence, **stop**. A whole profile built on the wrong person is worse than no profile.

### Layer 2: Public-record footprint

The official paper trail.

**For a person:**
- Election authorities (Brazil: TSE for candidates; many countries have public candidate filings)
- Court records (Brazil: state and federal court portals; JusBrasil aggregator; CNJ)
- Property records where public (Brazil: limited; some states publish via Cartório eletrônico)
- Professional registrations (Brazil: OAB for lawyers, CRM for doctors, CRA for administrators)
- Asset declarations for public officials (Brazil: SIAPE-public, Portal da Transparência)
- Public salary databases for civil servants (Portal da Transparência, state portals)
- Sanctions lists: OFAC SDN, UN consolidated, EU consolidated, OpenSanctions aggregator

**For a company:**
- Corporate registry (Brazil: Receita Federal CNPJ + state JUCESP / JUCESC / etc.)
- Beneficial ownership registries (Brazil: RFB UBO declaration; UK: Companies House PSC; OpenOwnership aggregator)
- Tax-good-standing certificates (Brazil: CND/CPEN federal, state, municipal)
- Public-procurement records (Brazil: PNCP, Portal da Transparência, ComprasNet)
- Litigation: same court portals as for individuals
- Sanctions and debarment lists (Brazil: CEIS, CEPIM, CNEP for federal sanctions)
- Environmental fines and embargoes (Brazil: IBAMA SICAFI; ICMBio embargoed-areas list)
- Labour violations (Brazil: "lista suja" do trabalho escravo, MTE database)
- Securities filings (Brazil: CVM; US: SEC EDGAR; UK: Companies House)

### Layer 3: Press and public discourse

What has been written about the entity, by whom, and when.

- Major search engines, with **date filters** to capture how coverage evolved
- Local-language press archives — for Brazil, LexisNexis (paywalled), Hemeroteca Digital da Biblioteca Nacional (free, historical)
- Specialist journalism databases: GIJN's resource list, ICIJ Offshore Leaks, OCCRP Aleph
- Academic and grey literature: Google Scholar, SSRN, ResearchGate
- Speeches, interviews, podcast appearances — what does the entity say about itself?

For each press mention, capture:
- Outlet and author
- Date
- The actual claim (quoted, in context)
- Whether the entity responded; if so, what
- Whether the case progressed (e.g., a fraud allegation that became an indictment, or that was dismissed)

### Layer 4: Digital footprint

The entity's online traces.

**For a person:**
- Social media: LinkedIn (often the strongest single source on professional history), X, Facebook, Instagram, TikTok, YouTube, GitHub, Mastodon, Bluesky, country-specific (VK, Weibo, Naver)
- Personal website / blog (use Wayback Machine to see history)
- Email format inference (check tools like Hunter.io for domain patterns — but never use to harass)
- Username reuse: tools like Sherlock or WhatsMyName check for the same handle across many platforms

**For a company:**
- Domain WHOIS (current and historical via DomainTools, ViewDNS, archive.org)
- DNS records and hosting infrastructure (sometimes reveals related entities)
- Job postings (a lot is revealed by what a company is hiring for)
- LinkedIn employee count and roles
- Customer lists, case studies, press releases on the company website
- Tracker overlap (BuiltWith, SpyOnWeb) — sites sharing Google Analytics or AdSense IDs are often related

### Layer 5: Network analysis

Who else is connected to this entity, and how?

For people: co-directorships, family ties (publicly declared), business partnerships, board memberships, donations made and received. Build a small network diagram showing first-degree connections, with sources.

For companies: ownership chains (parent / subsidiary / sister companies), shared directors, shared addresses, shared phone numbers, shared website infrastructure. Brazilian corporate networks especially benefit from CruzaGrafos-style network-graph approaches because beneficial ownership often runs through intermediate vehicles.

Tools for this:
- **OpenSanctions / OpenCorporates / OpenOwnership** — global free open data
- **Aleph (OCCRP)** — global investigative dataset, free for journalists
- **CruzaGrafos** — Brazilian entity-network analysis on 89M+ public records
- **Maltego** — visual entity-link analysis
- **Hyphe / Kumu / Gephi** — for building and visualising networks

## The risk-rating matrix (for due diligence)

When the journalist needs a Risk Summary (e.g., for sponsor due diligence), score each category honestly:

| Category | Severity scale |
|---|---|
| Sanctions / debarment | Severe (sanctioned); High (debarred from public procurement); Medium (under investigation); Low (none found) |
| Litigation | Severe (criminal conviction); High (active criminal case); Medium (civil cases or settled); Low (none material) |
| Adverse press | Severe (multiple credible outlets, recent, serious allegations); High (one credible outlet, recent); Medium (older or unconfirmed); Low (none material) |
| Corporate transparency | Severe (offshore-only, opaque ownership); High (partial disclosure); Medium (standard disclosure but late filings); Low (full and timely) |
| Conflicts of interest | Severe (direct beneficiary of stories the entity influences); High (indirect); Medium (potential); Low (none identified) |

**Always** anchor the score in evidence. "Severe — see press citations [1] [2] [3] dated [date]" is acceptable; "Severe — gut feeling" is not.

## Ethical limits, restated

- Do not produce a residential address for any private individual.
- Do not produce a list of family members for any private individual.
- Do not produce a workplace location for any private individual without strong public-interest justification.
- Do not produce contact information (personal phone, personal email) for anyone.
- For public officials: official addresses, official phone numbers, and the names of family members already publicly disclosed in asset declarations are fair game.

When unsure, default to **not publishing the detail in the lead sheet** but instead noting "[detail available, withheld pending public-interest assessment]" — let the editor decide.

## References

- OCCRP investigative resources: https://www.occrp.org/en/resources
- ICIJ data: https://www.icij.org/investigations/
- GIJN resources for investigators: https://gijn.org/resources/
- Bellingcat Online Investigation Toolkit: https://www.bellingcat.com/resources/
- For Brazilian-specific public-record sources, see `brazil-osint-resources.md`
