# Lead Sheet Template — bilingual (PT-BR / EN)

This is the canonical output template for any OSINT investigation produced by this skill.

Match the journalist's working language. When ambiguous, ask. The structure is identical in both languages — only the section headings and the mandatory warnings change.

---

## Template — Português (BR)

```markdown
> ⚠️ **AVISO — investigação preliminar.** Este é um lead sheet construído a partir de fontes públicas, não uma conclusão verificada. Confirme cada localização, identidade ou linha do tempo candidata com fontes primárias (apuração no local, registros oficiais, fontes humanas identificadas) antes de publicar.

# [Título da investigação] — Lead Sheet OSINT

**Solicitação:** [reproduza, em uma frase, o que o jornalista pediu]
**Tipo de investigação:** [geolocalização / verificação de imagem ou vídeo / perfil de pessoa ou entidade / investigação de conta]
**Data/hora desta análise (UTC):** YYYY-MM-DD HH:MM
**Material analisado:** [descrição breve + URLs ou nomes de arquivo]

---

## 1. Resumo executivo
*(3–5 frases em linguagem direta. O que foi pedido, o que foi encontrado, com qual nível de confiança, e qual o próximo passo recomendado.)*

---

## 2. Metadados disponíveis
| Campo | Valor | Observação |
|---|---|---|
| EXIF (data/hora) | | |
| EXIF (GPS) | | |
| Câmera/dispositivo | | |
| Software | | |
| Plataforma de origem | | |
| Timestamp da postagem | | |
| Conta/perfil que postou | | |
| Primeiro registro online | | |

*(Se o material não tem metadados extraíveis, registre "Não disponível — provavelmente removido pela plataforma ao upload" e siga adiante.)*

---

## 3. Pistas observáveis
*(Liste apenas o que está visível no material. Cada item é uma observação, não uma interpretação. Evidências serão interpretadas na seção 4.)*

- **Linguísticas:** [idiomas em placas, formato de placas de carro, moedas, números de telefone, TLDs visíveis]
- **Ambiente construído:** [arquitetura, sinalização viária, postes, mobiliário urbano]
- **Veículos:** [modelos, placas, lado da rua]
- **Ambiente natural:** [vegetação, topografia, céu]
- **Solar (chronolocation):** [direção e comprimento das sombras]
- **Pessoas e elementos humanos:** [vestuário, uniformes — sem identificação individual sem justificativa]

---

## 4. Localizações / identidades / datas candidatas

| Candidato | Confiança | Evidência principal |
|---|---|---|
| [Local / pessoa / data candidata 1] | Alta / Média / Baixa | [O que sustenta + link/fonte] |
| [Candidato 2] | | |

**Critério de confiança aplicado:**
- **Alta:** três ou mais pistas independentes convergentes + ao menos uma confirmação por mapa (Street View, satélite, ou posição solar)
- **Média:** duas pistas convergentes, ou uma forte sem confirmação por mapa
- **Baixa:** pista única ou inferência fracamente sustentada
- **Inconclusivo:** evidência insuficiente para narrowing além de [nível]

---

## 5. Justificativa da confiança
*(Por que este nível e não um nível acima ou abaixo? Quais pistas faltam para subir o nível?)*

---

## 6. Evidência visual e documental
*(Links diretos. Sempre que possível, com cópia arquivada.)*

- [Descrição] — [URL] (arquivado: [URL archive.today / archive.org])
- [Street View match] — [URL]
- [Reverse-image hit] — [URL] (data: ...)

---

## 7. Próximas perguntas para a apuração
*(Concretas. O repórter deve poder agir hoje em cada item.)*

1. [Ex.: "Solicitar à prefeitura de X o alvará de construção do imóvel nas coordenadas Y, Z, registrado em [data]"]
2. [Ex.: "Pedir comentário oficial à empresa X sobre a presença identificada no local Y"]
3. [Ex.: "Cruzar a placa identificada com o sistema de denúncias da PRF — solicitar via LAI"]
4. [...]

---

## 8. Fontes consultadas
*(Toda URL acessada. Quando possível, link de arquivo. Inclui ferramentas e bases de dados, não apenas matérias.)*

- [Fonte 1 — URL — arquivado em URL]
- [Fonte 2 — URL — arquivado em URL]
- [...]

---

## 9. Limitações desta análise
*(O que não pôde ser checado, e por quê. Ferramentas indisponíveis, dados pagos, acesso a registros bloqueado, etc.)*

- [Limitação 1]
- [Limitação 2]

---

## 10. Considerações éticas e de segurança aplicadas
*(Se a investigação envolveu pessoa privada, conta anônima, conteúdo sensível, ou jurisdição de risco — registre como o teste de interesse público foi aplicado e quais detalhes foram retidos.)*

- [Ex.: "Endereço residencial identificado durante a apuração não publicado neste lead sheet — uso editorial apenas, com base no critério de necessidade."]
- [Ex.: "Conta anônima identificada como possível ativista em jurisdição hostil — não deanonimizada."]

---

> Esta análise usa dados públicos e raciocínio visual. Pode conter erros, omissões ou interpretações equivocadas — inclusive a partir de material falsificado. Verifique antes de publicar e dê crédito a fotógrafos, testemunhas e detentores de registros públicos cujo trabalho tornou o lead possível.
```

---

## Template — English

```markdown
> ⚠️ **WARNING — preliminary investigation.** This is a lead sheet built from public sources, not a verified finding. You must confirm every candidate location, identity, and timeline with primary sources (on-site reporting, official records, named human sources) before publication.

# [Investigation title] — OSINT Lead Sheet

**Request:** [in one sentence, restate what the journalist asked]
**Investigation type:** [geolocation / image-or-video verification / person or entity profiling / account investigation]
**Analysis date/time (UTC):** YYYY-MM-DD HH:MM
**Material analysed:** [brief description + URLs or file names]

---

## 1. Executive summary
*(3–5 sentences, plain language. What was asked, what was found, at what confidence, and what the recommended next step is.)*

---

## 2. Metadata summary
| Field | Value | Note |
|---|---|---|
| EXIF (date/time) | | |
| EXIF (GPS) | | |
| Camera/device | | |
| Software | | |
| Source platform | | |
| Posting timestamp | | |
| Posting account | | |
| First online appearance | | |

*(If no metadata could be extracted, record "Not available — likely stripped by the platform on upload" and proceed.)*

---

## 3. Observable clues
*(List only what is visible. Each item is an observation, not yet an interpretation. Interpretation goes in section 4.)*

- **Linguistic:** [languages on signage, plate formats, currencies, phone numbers, visible TLDs]
- **Built environment:** [architecture, road markings, power poles, street furniture]
- **Vehicles:** [models, plates, side of the road]
- **Natural environment:** [vegetation, topography, sky]
- **Solar (chronolocation):** [shadow direction and length]
- **People and human elements:** [clothing, uniforms — no individual identification without justification]

---

## 4. Candidate locations / identities / dates

| Candidate | Confidence | Primary evidence |
|---|---|---|
| [Candidate 1] | High / Medium / Low | [What supports it + link/source] |
| [Candidate 2] | | |

**Confidence criteria applied:**
- **High:** three or more independent converging clues + at least one map confirmation (Street View, satellite, or solar-position match)
- **Medium:** two converging clues, or one strong clue without map confirmation
- **Low:** single clue or weakly supported inference
- **Inconclusive:** evidence insufficient to narrow beyond [level]

---

## 5. Confidence rationale
*(Why this level and not a level above or below? What evidence would raise the level?)*

---

## 6. Visual and documentary evidence
*(Direct URLs. With archived copies wherever possible.)*

- [Description] — [URL] (archived: [archive.today / archive.org URL])
- [Street View match] — [URL]
- [Reverse-image hit] — [URL] (date: ...)

---

## 7. Follow-up questions for the journalist
*(Concrete. The reporter should be able to act on each item today.)*

1. [e.g., "Pull the building permit at City Hall for the property at coordinates X,Y, filed on [date]"]
2. [e.g., "Request comment from Company X regarding the presence identified at Location Y"]
3. [e.g., "Cross-check the identified vehicle plate against PRF records via FOIA"]
4. [...]

---

## 8. Sources consulted
*(Every URL accessed. With archive links where possible. Include tools and databases, not only articles.)*

- [Source 1 — URL — archived at URL]
- [Source 2 — URL — archived at URL]
- [...]

---

## 9. Limitations of this analysis
*(What could not be checked, and why. Tools unavailable, paywalled data, blocked records, etc.)*

- [Limitation 1]
- [Limitation 2]

---

## 10. Ethical and safety considerations applied
*(If the investigation involved a private individual, anonymous account, sensitive content, or risky jurisdiction — record how the public-interest test was applied and what details were withheld.)*

- [e.g., "Residential address identified during research not published in this lead sheet — editorial use only, on a necessity basis."]
- [e.g., "Anonymous account identified as a possible activist in a hostile jurisdiction — not deanonymised."]

---

> This analysis uses publicly available data and visual reasoning. It can be wrong, incomplete, or misled by manipulated source material. Always verify before publishing, and credit the original photographers, witnesses, and public-record holders whose work made the lead possible.
```

---

## Notes on filling the template

- **Always include all ten sections.** A section with "no findings" or "not applicable" is more useful than a missing section — it shows the journalist what was checked.
- **Section 7 (follow-up questions) is the most-used section by reporters.** Give them three to five concrete next moves, not vague "verify with sources" advice.
- **Section 9 (limitations) is the second-most-important.** Honest limitations make the lead sheet defensible if the story is later contested.
- For verification investigations specifically, add a **Verdict** sub-section between sections 1 and 2 (Confirmed / Partially confirmed / Inconclusive / Disputed / False).
- For entity profiling, replace section 4 with a **Risk Summary table** as defined in `references/entity-profiling.md`.
