# Trust Communication Guide — osint-investigation

**Purpose:** Help authors, editors, and stakeholders communicate the security and safety of the `osint-investigation` skill to different audiences.

---

## What you can honestly claim

Before drafting any communication, understand what the evidence actually supports:

| Claim | Supported? | Basis |
|---|---|---|
| "The skill contains no malicious code" | Yes | No executable code exists — pure Markdown |
| "The skill requests minimal permissions" | Yes | No system access, no API keys, no network calls |
| "The skill refuses stalking and doxxing requests" | Yes | Explicit refusal criteria in SKILL.md |
| "The skill will never investigate minors" | Yes | Absolute, unconditional prohibition in SKILL.md |
| "The skill is open source and auditable" | Yes | MIT license, public GitHub repository |
| "The skill is guaranteed to be misuse-proof" | No | No AI guardrail is 100% robust; this is why transparent use policies matter |
| "The skill replaces primary-source journalism" | No | Skill explicitly states it produces leads, not conclusions |

Honest framing builds more durable trust than overclaiming.

---

## Audience 1: Redações brasileiras (Newsrooms in Brazil)

### What editors and IT managers need to know

Brazilian newsrooms considering adoption of this skill have three main concerns:

1. **Legal exposure** — Does use of this skill create LGPD or Marco Civil liability?
2. **Source safety** — Could the skill inadvertently expose confidential sources?
3. **IT governance** — What does the skill access on our systems?

### Key talking points

**On legal exposure:**
> Esta skill não armazena dados pessoais, não processa informações em servidores externos e não envia dados para terceiros. Toda a operação ocorre dentro da janela de contexto do Claude, que segue as políticas de privacidade da Anthropic. A skill é projetada para trabalhar exclusivamente com fontes públicas e orienta o jornalista a aplicar o teste de interesse público antes de qualquer investigação sobre pessoas.

**On source safety:**
> A skill inclui orientações explícitas de proteção de fontes: proíbe o uso de técnicas de OSINT para identificar denunciantes, recomenda perfis de pesquisa isolados e gerenciamento de metadados. **A skill não tem acesso à comunicação da redação nem a arquivos locais.**

**On IT governance:**
> A skill é um conjunto de arquivos Markdown instalados em `~/.claude/skills/`. Não instala software, não abre portas de rede, não requer credenciais e não tem mecanismo de atualização automática. Qualquer gestor de TI pode auditar o conteúdo completo em menos de uma hora lendo os 9 arquivos do projeto.

### Email template for IT approval

```
Assunto: Solicitação de aprovação — skill de OSINT para jornalismo investigativo

Prezado(a) [nome],

Estou solicitando aprovação para usar a skill "osint-investigation" no Claude Code 
para investigações de jornalismo baseadas em fontes abertas.

RESUMO TÉCNICO:
- Tipo: documentação Markdown (sem código executável)
- Permissões: nenhuma além do contexto do Claude
- Dados externos: nenhum dado é enviado pela skill; todo acesso a ferramentas 
  externas é manual e iniciado pelo jornalista
- Auditoria: código-fonte público em github.com/reichaves/osint-investigation
- Licença: MIT

CONFORMIDADE:
- Não coleta dados pessoais (sem impacto direto na LGPD)
- Orientações de proteção de fontes embutidas
- Proíbe investigação de menores e rastreamento em tempo real

Estou à disposição para uma reunião técnica se necessário.

Atenciosamente,
[seu nome]
```

---

## Audience 2: International partners (GIJN, Bellingcat, OCCRP, RSF)

### What international partners need to know

Investigative journalism organizations evaluating this skill for training programs or tool directories need:

1. **Methodology alignment** — Does this follow recognized standards?
2. **Ethical rigor** — Does it embed harm-reduction practices?
3. **Tool accuracy** — Are limitations disclosed honestly?

### Key talking points

**On methodology:**
> This skill is grounded in the Berkeley Protocol on Digital Open Source Investigations (UC Berkeley Human Rights Center / UN OHCHR) and Bellingcat-style verification workflows. Every investigation type follows the Protocol's "Five Ws" framework and requires confidence-level disclosure before any claim is reported.

**On ethical rigor:**
> The skill embeds the Dart Center for Journalism and Trauma's vicarious trauma guidelines, includes operational security guidance for journalists in hostile environments, and contains an absolute prohibition on investigating minors, real-time tracking, and deanonymizing civil society actors without editor authorization.

**On tool accuracy:**
> Every tool in the catalog is accompanied by honest limitations: paywalls, API restrictions (including X/Twitter's 2026 API-access model), discontinued services (CrowdTangle), and AI-detection failure modes. The confidence-rating system (High/Medium/Low with explicit thresholds) prevents false certainty in published investigations.

### One-paragraph summary for tool directories

> **osint-investigation** is a Claude skill for investigative journalists that provides structured workflows for image geolocation, photo/video verification, entity profiling, and social media account investigation. It is grounded in the Berkeley Protocol and Bellingcat methodology, operates entirely on publicly available sources, and embeds mandatory ethical warnings, confidence-rating requirements, and refusal criteria for stalking, doxxing, and investigation of minors. The skill is open source (MIT), requires no code execution or elevated permissions, and is bilingual (Portuguese/English) with dedicated coverage of Brazilian public records. It produces structured lead sheets — starting points for reporting, not final conclusions.

---

## Audience 3: Individual journalists and researchers

### What individual users need to know

Journalists installing the skill independently need to understand:

1. **What it will and won't do** — To set correct expectations
2. **Safe use patterns** — When and how to use it responsibly
3. **Known limitations** — Where it might fail or mislead them

### Safe use guide

**Use it for:**
- Geolocating images and videos for stories about public events, conflicts, or environmental issues
- Verifying whether a viral photo is authentic before publishing
- Building a background dossier on a public official or company involved in a story you are actively reporting
- Assessing whether a social media account is authentic or part of a coordinated campaign

**Do not use it for:**
- Investigating private individuals who are not subjects of active public-interest stories
- Any investigation where the subject is a minor
- Tracking a person's location or movements in real time
- Identifying confidential sources, whistleblowers, or activists in hostile environments

**Known limitations:**
- The skill cannot execute tool searches autonomously — you must run each tool manually
- Confidence ratings reflect the *methodology*, not infallibility — High confidence still requires editorial judgment
- AI-generated image detection is improving but remains unreliable for sophisticated fakes as of 2026
- Platform API restrictions (especially X/Twitter) limit what automated tools can retrieve
- Brazilian public records are often incomplete, delayed, or in Latin-1 encoding — always cross-reference

### Installation verification

After installing, confirm the skill file matches the published source:

1. Open `~/.claude/skills/osint-investigation/SKILL.md`
2. Verify the header matches: `name: osint-investigation`, `author: Reinaldo Chaves`
3. Verify the refusal criteria are present (search for "never investigate" and "real-time tracking")
4. If in doubt, reinstall from the official repository

---

## Audience 4: Funders and grantmakers

### What funders need to know

Organizations funding journalism or press-freedom initiatives need:

1. **Impact framing** — What journalistic capacity does this enable?
2. **Risk assessment** — What misuse risks exist and how are they mitigated?
3. **Sustainability** — Is this an ongoing commitment or a one-off release?

### Key talking points

**On impact:**
> This skill lowers the technical barrier to evidence-based investigative journalism for reporters who do not have dedicated OSINT specialists on staff. It standardizes methodology across a newsroom, ensuring that geolocation and entity-profiling work follows Berkeley Protocol standards regardless of the individual reporter's experience level.

**On misuse risk:**
> The skill cannot be used for stalking, doxxing, or investigating minors — these are unconditional refusals hardcoded into the skill definition. Because the skill is pure documentation (no API, no server, no autonomous data collection), there is no infrastructure that could be exploited for mass surveillance. Each investigation requires explicit human action for every tool lookup.

**On sustainability:**
> The skill is MIT-licensed and published as an open-source repository. Maintenance consists of updating methodology and tool references as the OSINT landscape evolves — this is low-cost, document-level work. The skill does not depend on any proprietary service or paid API that could become unavailable.

### Grant application language

> The `osint-investigation` Claude skill provides Brazilian and international investigative journalists with structured, methodology-aligned OSINT workflows grounded in the Berkeley Protocol and Bellingcat standards. The skill is open source, operates exclusively on public data, and embeds non-negotiable ethical guardrails against investigative misuse. It addresses a documented capacity gap in newsrooms where dedicated OSINT specialists are unavailable, enabling reporters to produce evidence-based investigations with consistent methodological rigor and appropriate confidence-level disclosure.

---

## Security badges and signals

The following elements serve as trust signals you can reference in communications:

| Signal | Where to find it |
|---|---|
| Open source (MIT) | `LICENSE` in repository root |
| Security policy | `SECURITY.md` in repository root (GitHub auto-displays this) |
| Reproducible audit | `docs/security-audit.md` |
| Berkeley Protocol alignment | Stated in `SKILL.md` header and throughout reference files |
| Ethical refusal criteria | `SKILL.md` "Critical guardrails" section |
| Legal framework compliance | `references/ethics-and-safety.md` |
| No executable dependencies | Verify: `ls` shows only `.md` files |

---

## What not to claim

Avoid these overstatements in any communication:

- "This skill is completely safe" — No AI tool has absolute safety guarantees
- "Verified by [tool]" — Unless you have actually run the audit and have results
- "Endorsed by Bellingcat / Berkeley" — Unless explicit endorsement has been obtained
- "Compliant with LGPD" — The skill is *designed to minimize* LGPD exposure; formal compliance assessment requires a DPO review
- "Guaranteed to refuse all misuse" — Guardrails are strong but not technically unbypassable; the skill's design minimizes risk, it does not eliminate it

Honest, scoped claims protect both the project and the users who rely on it.
