# osint-investigation — Claude Skill for Journalists

[![GitHub](https://img.shields.io/badge/GitHub-Repository-blue)](https://github.com/reichaves/osint-investigation)
[![License](https://img.shields.io/badge/License-MIT-green)](LICENSE)
[![Claude Skill](https://img.shields.io/badge/Claude-Skill-orange)](https://github.com/reichaves/osint-investigation)
[![Berkeley Protocol](https://img.shields.io/badge/Standard-Berkeley%20Protocol-purple)](https://humanrights.berkeley.edu/publications/berkeley-protocol-on-digital-open-source-investigations/)
[![Security Policy](https://img.shields.io/badge/Security-Policy-red)](SECURITY.md)


A structured OSINT (Open-Source Intelligence) skill for Claude, tailored to investigative journalists. Grounded in the **Berkeley Protocol on Digital Open Source Investigations** and Bellingcat-style verification workflows

---

## What this skill does

This skill turns Claude into a structured OSINT investigator. It covers four core investigation types — image/video geolocation, photo verification, person/entity profiling, and social media account investigation — and always produces a **lead sheet** the reporter can act on.

It is **not** a substitute for primary-source reporting — it produces *leads*, with honest confidence levels, that the journalist must confirm.

---

## Installation

Install via the [`claude-skills`](https://github.com/jamditis/claude-skills-journalism) plugin, or manually:

```bash
# Manual install — clone into your Claude skills directory
git clone https://github.com/reichaves/osint-investigation \
  ~/.claude/skills/osint-investigation
```

Claude Code will automatically discover and load the skill from `~/.claude/skills/`.

---

## File structure

```
osint-investigation/
├── README.md
├── LICENSE
├── SECURITY.md                               ← security policy and responsible disclosure
├── SKILL.md                                  ← main skill definition (loaded by Claude)
├── assets/
│   └── lead-sheet-template.md               ← bilingual (PT-BR / EN) output template
├── docs/
│   ├── security-audit.md                    ← reproducible 4-layer security audit plan
│   └── trust-communication.md              ← guide for communicating safety to newsrooms and partners
└── references/
    ├── geolocation-framework.md             ← full geolocation methodology + tools
    ├── verification-checklist.md            ← Berkeley Protocol-aligned verification steps
    ├── entity-profiling.md                  ← person & company OSINT methodology
    ├── social-account-investigation.md      ← investigating accounts and networks
    ├── tools-catalog.md                     ← curated tool list with limitations and access notes
    ├── ethics-and-safety.md                 ← legal, ethical, vicarious-trauma guidance
    └── brazil-osint-resources.md            ← public-record sources for Brazilian investigations
```

---

## Investigation types

| Type | Trigger phrases | Reference |
|---|---|---|
| **Geolocation** | "where was this taken", "geolocate", "que cidade é essa" | `references/geolocation-framework.md` |
| **Photo/video verification** | "is this real", "when was this taken", "essa foto é verdadeira" | `references/verification-checklist.md` |
| **Person/entity profiling** | "who is X", "due diligence", "perfil de risco de [empresa]" | `references/entity-profiling.md` |
| **Social media account** | "is this a bot", "who runs this", "investigar essa conta" | `references/social-account-investigation.md` |

---

## Critical guardrails

1. **Never claim certainty without triangulation.** High confidence requires ≥3 independent converging clues.
2. **Never invent evidence.** If a tool is unavailable, say so — do not fabricate matches.
3. **Never identify private individuals** without explicit journalistic justification.
4. **Always include ethical warnings** (verbatim) at the top and bottom of every lead sheet.
5. **Preserve, do not just analyse.** Archive sources (archive.org, archive.today) before analysis.
6. **Vicarious trauma is real.** Offer content warnings for graphic material.

---

## Output — the lead sheet

Every investigation ends in a structured **lead sheet** (template at `assets/lead-sheet-template.md`), bilingual (PT-BR / EN), with:

1. Ethical warning (mandatory)
2. Executive summary
3. Metadata summary
4. Observable clues
5. Candidate findings with confidence ratings (High / Medium / Low)
6. Confidence rationale
7. Visual and documentary evidence links
8. Follow-up questions for the journalist (concrete, actionable)
9. Sources consulted
10. Limitations
11. Closing disclaimer (mandatory)

---

## Brazilian investigations

For stories involving Brazilian people, companies, or events, the skill also loads `references/brazil-osint-resources.md`, which covers:

- Receita Federal (CNPJ), state commercial registries
- Portal da Transparência, CEIS/CEPIM/CNEP sanctions lists
- JusBrasil, TSE (DivulgaCandContas), CNJ
- IBAMA, ICMBio, MapBiomas, INPE/DETER
- PNCP (public procurement), Câmara and Senado open APIs
- CruzaGrafos, Brasil.IO, Querido Diário, Achados e Pedidos

---

## Ethics

This skill is for **investigative journalism in the public interest**. It will refuse requests that:

- Target minors
- Seek real-time location of any individual
- Target private individuals without journalistic justification
- Appear designed for harassment, stalking, or doxxing
- Assist surveillance against civil society

See `references/ethics-and-safety.md` for full ethical, legal, and operational-security guidance.

---

## Security

This skill is **pure documentation** — no executable code, no package dependencies, no API keys, no server infrastructure. Its security model is built on three pillars:

- **Minimal scope:** The skill reads only its own bundled reference files within Claude's context window. No file system writes, no network calls, no credential management.
- **Content auditability:** Every file is human-readable Markdown. Anyone can audit the full skill in under an hour.
- **Behavioral guardrails:** Refusal criteria for stalking, doxxing, minor investigation, and real-time tracking are unconditional and hardcoded into `SKILL.md`.

| Resource | Purpose |
|---|---|
| [`SECURITY.md`](SECURITY.md) | Security policy, responsible disclosure, permission scope documentation |
| [`docs/security-audit.md`](docs/security-audit.md) | Reproducible 4-layer audit: static content, permission scope, adversarial testing, distribution integrity |
| [`docs/trust-communication.md`](docs/trust-communication.md) | How to communicate safety to newsrooms, international partners, funders, and individual users |

To report a security concern, see [`SECURITY.md`](SECURITY.md).

---

## Methodology references

- [Berkeley Protocol on Digital Open Source Investigations](https://humanrights.berkeley.edu/publications/berkeley-protocol-on-digital-open-source-investigations/)
- [Bellingcat Online Investigation Toolkit](https://bellingcat.gitbook.io/toolkit)
- [OCCRP Aleph](https://aleph.occrp.org/)
- [GIJN Resources](https://gijn.org/resources/)
- [Dart Center for Journalism and Trauma](https://dartcenter.org/)

---

## Author

**Reinaldo Chaves** — Data journalist in Brazil  
Email: reichaves@gmail.com | GitHub: [@reichaves](https://github.com/reichaves)

---

## License

[MIT](LICENSE) — free to use, adapt, and redistribute with attribution.
