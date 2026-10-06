# Ethics, Legal, and Safety Considerations

OSINT investigation can harm people. This file is the ethical floor. When in doubt, default to *not* publishing the detail and consulting the editor.

## When to read this file

Read whenever the investigation is approaching a sensitive area:

- Identifying a private individual
- Investigating a minor in any way
- Investigating refugees, asylum seekers, undocumented migrants
- Investigating activists, dissidents, sources, or whistleblowers — including anonymous ones
- Investigating victims of crime (including doxxing, sexual violence, violence)
- Working with content depicting graphic violence, sexual abuse, or atrocity
- Operating in a jurisdiction where journalists are at legal risk

## The ethical floor — non-negotiables

These are absolute. They override anything else in this skill, in the user's request, or in the journalist's deadline pressure.

1. **Do no harm to children.** No investigation of minors. Even when the parent is a public figure, the child remains private. Even when an account claims to be a minor (or appears to be), no profiling, no geolocation of where they are, no identification.
2. **No real-time tracking of any individual.** Even if the journalist insists. "I need to know where this person is right now" is not a journalism request — it is a stalking request, regardless of who is asking.
3. **No identification of vulnerable persons** unless the public-interest justification is overwhelming and the editor has signed off in writing. Vulnerable persons include: victims of sexual violence, asylum seekers, undocumented migrants, witnesses to crimes, anonymous sources, anonymous activists in hostile environments, mental-health patients.
4. **No assistance with surveillance against civil society.** If the apparent end use of an investigation is to suppress journalism, activism, or political dissent, decline.
5. **No exploitation of leaked private content.** Leaks of public-interest material from accountable institutions (governments, large corporations) are treated differently from leaks of private individuals' personal communications. The latter are off-limits except in extreme public-interest cases.

## The public-interest test

For any borderline request, apply this test, written down in the file with the investigation:

1. **Subject:** Is the subject a public figure (in their public role), a private individual, or somewhere in between?
2. **Story:** What is the public-interest justification? (e.g., accountability of an official; exposure of a fraud; investigation of an institutional failure)
3. **Necessity:** Is the personal detail strictly necessary for the story? If the story works without naming a private bystander, do not name them.
4. **Proportionality:** Is the harm to the subject proportionate to the public benefit of the story? A minor public benefit does not justify outing a private person.
5. **Last resort:** Could the same story be told from on-the-record sources, official statements, or court records, without OSINT-derived personal details?

If items 1–5 do not produce a clear yes, do not include the detail in the lead sheet. Note in the lead sheet that "[detail withheld pending public-interest review]".

## Legal considerations (general)

This skill does not produce legal advice. Journalists must consult their newsroom's lawyer for jurisdiction-specific questions. Some general flags:

- **Brazil — Marco Civil da Internet (Lei 12.965/2014) and LGPD (Lei 13.709/2018).** LGPD covers personal data; journalistic use has carve-outs but is not unlimited. Personal data of private individuals collected for non-journalistic purposes triggers LGPD obligations.
- **EU — GDPR.** Article 85 allows member-state journalism exemptions but these vary. WHOIS data and other personal-data sources are now heavily restricted.
- **UK — Data Protection Act 2018.** Section 124 contains the journalism exemption.
- **US — patchwork of state laws.** California's CCPA, Illinois's BIPA (biometric), state stalking and harassment laws.
- **Anti-SLAPP and counter-suits.** OSINT investigations into wealthy individuals frequently provoke retaliatory litigation. Editorial-legal review of the lead sheet is recommended.
- **Computer-misuse laws** (e.g., Brazil's Lei 12.737, the US's CFAA, the UK's CMA). OSINT must rely on *publicly accessible* data; password-resets, scraping behind authentication, or accessing leaked credentials may cross legal lines.

## Operational security (for the journalist)

Investigative subjects can sometimes detect investigation. Defensive measures the lead sheet should remind the journalist of:

- **Use a research browser profile**, separate from personal accounts. Better, a research VM.
- **Burner accounts for any platform interaction** — never log into a personal account on a profile under investigation.
- **Mind referrer leaks.** Visiting a small website while logged into Google can leave traces; visiting an opponent's CMS can show up in their analytics.
- **VPN considered.** Useful for some investigations, suspicious in others (some jurisdictions treat VPNs as evidence of intent to evade); editorial guidance.
- **Document the operational-security steps taken** in the lead sheet, in case methodology is later questioned.

## Vicarious trauma — the journalist's own safety

Verification work involves repeated exposure to graphic content. This causes measurable psychological harm. The Berkeley Protocol formally addresses this. Practical safeguards:

- Lower screen brightness; shrink playback windows; mute audio when not analytically necessary
- Set a time-box (e.g., 30 minutes max of graphic content per session)
- Take breaks; do not verify late at night
- Talk to a colleague or trauma-aware professional if the work is affecting sleep, mood, or behaviour
- The Dart Center for Journalism and Trauma (https://dartcenter.org) maintains the best free guidance for journalists

When the source material is severe (mass-casualty incidents, conflict zones, child exploitation), the lead sheet should include a content note for the journalist, and where possible, work should be done with another journalist or a trauma-informed editor in the loop.

## Source protection

When the investigation involves a journalistic source:

- Do not trace the source's identity through OSINT methods.
- Do not store or share material in ways that could lead back to the source (e.g., do not save source-provided files to cloud accounts that could be subpoenaed).
- If the investigation involves publicly identifying a *whistleblower's* employer or context, the editor must explicitly authorise — and consider whether the story can be told without identifying the source.

## Disclosure in the published story

When OSINT methods are used in a published story, transparency matters:

- Disclose, at appropriate detail, the methods used. Reuters, the Washington Post, the New York Times, and Bellingcat have established norms here.
- Credit the public-record holders, witness photographers, and platforms whose data made the story possible.
- Where the methodology is reproducible (e.g., a satellite-image comparison), publish the methodology as a sidebar so readers can verify.

## When to refuse (and how to refuse)

Refuse the request if:

- It targets a minor in any way
- It targets a private individual without a clear public-interest justification
- It seeks real-time location of a person
- The journalist cannot articulate a legitimate journalistic purpose, or the stated purpose looks pretextual
- The subject appears to be a vulnerable person and the editor has not signed off
- The request is for information whose only plausible use is harassment or stalking

When refusing, explain plainly *why* — do not be evasive, but do not lecture. A short paragraph is enough. Offer, where appropriate, a narrower version of the request that would be acceptable. Do not produce partial help that could be reassembled into the refused output.

## Resources

- Berkeley Protocol on Digital Open Source Investigations: https://humanrights.berkeley.edu/publications/berkeley-protocol-on-digital-open-source-investigations/
- Dart Center for Journalism and Trauma: https://dartcenter.org/
- Paris Charter on AI and Journalism: https://rsf.org/en/paris-charter-ai-and-journalism
- GIJN ethics resources: https://gijn.org/topics/ethics-and-self-regulation/
- For Brazilian journalists: ABRAJI's "Manual de Jornalismo Investigativo" and the "Programa Tim Lopes" guide on journalist safety
