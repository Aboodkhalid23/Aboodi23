# Security Policy — osint-investigation

## What this file covers

This is the official security policy for the `osint-investigation` Claude skill. Because this project is **pure documentation** (Markdown files only — no executable code, no package dependencies, no API keys, no server infrastructure), its security model differs from a typical software project.

Security here means:

| Axis | What it means |
|---|---|
| **Content safety** | SKILL.md and reference files contain no prompt-injection instructions, no malicious tool triggers, no capability-escalation requests |
| **Ethical guardrails** | The skill refuses harmful requests reliably and consistently |
| **Minimal scope** | The skill requests no permissions beyond reading its own reference files within Claude's context window |
| **Transparent distribution** | Source code is open, MIT-licensed, and publicly auditable |

---

## Scope: what this skill can and cannot do

### What the skill does

- Guides Claude through structured OSINT workflows for investigative journalism
- Produces **lead sheets** — starting points for reporting, never final conclusions
- Covers: image geolocation, photo/video verification, entity profiling, social media account investigation
- Works in Portuguese (pt-BR) and English
- References only **publicly available, free or low-cost** investigative tools

### What the skill explicitly refuses to do

The following requests will be declined by design:

| Refused action | Reason |
|---|---|
| Real-time tracking of any individual | High harassment/stalking risk; no journalistic justification |
| Any investigation targeting minors | Absolute ethical boundary; no exceptions |
| Identifying private individuals without public-interest justification | Privacy protection; requires journalist to state justification first |
| Identifying vulnerable persons (victims, dissidents, asylum seekers, whistleblowers) | Without editor sign-off; protects source safety |
| Assisting surveillance against civil society | Not journalism; out of scope |
| Exploiting leaked private content | Legal and ethical violation |
| Password-reset or account-access techniques | Computer-misuse laws (CFAA, Lei 12.737/2012 BR, CMA UK) |
| Fabricating evidence or tool results | Accuracy is a non-negotiable editorial standard |

### Minimal permission scope

This skill requests **zero elevated permissions** from Claude or the user's system:

- No file system writes
- No network calls initiated by the skill itself
- No API key management
- No storage of investigation results
- No cross-session memory of investigated individuals
- Reads only: its own reference files (`references/*.md`) within the active context window

This can be verified by any security reviewer by reading `SKILL.md` from line 1 to end.

---

## Applicable security audit tools

Because this project has no executable code or package dependencies, general-purpose vulnerability scanners (Snyk, Socket, Dependabot) are **not applicable**. The relevant audit methods are:

| Tool / Method | What it checks | Applicable? |
|---|---|---|
| **Skill Vetter** | Dangerous instructions, abusive permission scope requests in skill files | Yes — full checklist in `docs/security-audit.md` |
| **Gen Agent Trust Hub** | AI agent trust signals: scope, transparency, harm reduction | Yes — framework applied in `docs/security-audit.md` |
| **Skills.sh Manager** | IDE panel display of skill audit results | Yes — skill exposes no dangerous triggers |
| **Manual content review** | Prompt injection patterns, capability escalation in Markdown | Yes — reproducible audit in `docs/security-audit.md` |
| **Adversarial behavioral testing** | Guardrail compliance under hostile prompts | Yes — 12-case test suite in `docs/security-audit.md` |
| **SHA-256 file integrity** | Distribution tamper detection | Yes — hashes in `docs/security-audit.md` |
| Snyk / Socket / Dependabot | Package vulnerabilities, supply-chain compromise | Not applicable — no code dependencies |
| SAST tools (Semgrep, CodeQL) | Code-level vulnerabilities | Not applicable — no executable code |

---

## Responsible disclosure

If you find content in this skill that:

- Contains prompt injection or jailbreak instructions
- Requests permissions beyond what is documented above
- Includes instructions that could enable stalking, harassment, or harm
- Contains factual errors in methodology that could endanger journalists

Please report it to:

**Email:** reichaves@gmail.com  
**GitHub:** Open an issue at `github.com/reichaves/osint-investigation/issues` with the label `security`

**Expected response time:** 72 hours for acknowledgment; 14 days for resolution.

We will not pursue legal action against good-faith security reporters.

---

## Legal and ethical frameworks

This skill is designed to comply with:

- **Brazil:** Marco Civil da Internet (Lei 12.965/2014), LGPD (Lei 13.709/2018), Lei de Acesso à Informação (Lei 12.527/2011)
- **EU:** GDPR Article 85 (journalism exemption)
- **UK:** Data Protection Act 2018 Section 124 (journalism exemption)
- **US:** First Amendment protections for investigative journalism; CCPA, BIPA awareness
- **International:** Berkeley Protocol on Digital Open Source Investigations (UN/UC Berkeley)

The skill instructs users to respect platform Terms of Service and warns explicitly against computer-misuse-law violations.

---

## Version

This policy applies to `osint-investigation` v1.0.0 and later.  
Last updated: 2026-05-03  
Author: Reinaldo Chaves (reichaves@gmail.com)
