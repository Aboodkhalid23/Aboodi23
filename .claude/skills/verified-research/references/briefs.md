# Subagent briefs

A subagent starts with nothing except your brief, so everything it needs has to be in it: the goal, the boundaries, today's date and where to write. Vague briefs such as "research the chip shortage" make subagents duplicate each other, miss the point or chase stale information.

Replace every `<placeholder>` and use absolute paths. SKILL_DIR is this skill's base directory, and RESEARCH_DIR is the research folder for this question.

## Researcher brief

```
You are a researcher on a team answering: "<the framed question>".
Today is <YYYY-MM-DD>. Anything that can change needs a current source.

Your sub-question (<S2>): <one specific question>
Why it matters: <how the answer feeds the final conclusion or decision>
In scope: <...>
Out of scope (covered by others): <S1: ...; S3: ...>
Constraints: <time window> | <geography or jurisdiction> | search in: <languages>
Prefer: <named primary sources, sites, databases>
Avoid: <for example, SEO listicles; vendor blogs for performance claims>
Be sure to find: <the specific numbers, dates, comparisons or counter-evidence needed>
Budget: about <N> tool calls, counting every search and fetch (failed ones too); stop earlier if you hit saturation.

First read SKILL_DIR/references/researching.md and follow it, especially the evidence-card format.
Append your cards to the notes file after every batch of about five tool calls, not just at the end.
Write your notes to RESEARCH_DIR/notes/<S2>-<slug>.md
Report only to me: don't message the user or publish anything.
Reply with at most 200 words: your summary, the main conflicts and gaps, and the notes path.
```

**A good brief (the key lines):**

> Your sub-question (S2): What did controlled studies from 2023–2026 measure about AI coding assistants' effect on how long professional developers take to complete tasks?
> Be sure to find: the METR 2025 randomized trial and any follow-ups or rebuttals, plus each study's design (lab or field, sample size, task type).
> Prefer: the papers themselves (arXiv, journal pages, company research posts that include methods).
> Out of scope: developer surveys and self-reported productivity (S3 covers them).

**A bad brief:** "Research AI coding productivity." It has no boundaries, no date, no sources and no output path.

## Verifier brief

```
You are an independent fact-checker. Today is <YYYY-MM-DD>.
You did not write this report. Don't judge or improve its argument; only check whether each claim is supported by the source cited for it.

First read SKILL_DIR/references/verification.md and follow it.
Claims to check: RESEARCH_DIR/checks/claims.md, claims <C1–C25 | all | all marked high>.
<If verifiers are split: Check only the claims that cite these sources: <list from the checklist's "By source" index>. Another verifier has the rest. For a claim that also cites a source not on your list, label only your part and say which part you checked.>
Open every cited source yourself. The researcher's quote in the checklist is a hint about where to look, not proof; it may be wrong.
Write your results to RESEARCH_DIR/checks/verification-<n>.md
Report only to me: don't message the user or publish anything.
Reply with the count for each label and the IDs of every claim not labeled SUPPORTED, each with a one-line reason.
```

Give each verifier no more than about 25 claims, and split larger sets across verifiers running in parallel. Always check every high-priority claim: those in the bottom line and key findings, plus numbers and quotes. For long reports, check the rest as the budget allows, and say in the method line how many claims were checked.

## Red-team brief

```
You are the red team for a research conclusion. Today is <YYYY-MM-DD>.
Your job is to find what is wrong, missing or overstated, not to agree.

Question: <the framed question>
Bottom line under review: <the draft's bottom line, verbatim>
Key findings it rests on: <3–7 bullets, each with its main source>

First read the "Red team" section of SKILL_DIR/references/analysis.md.
Search for: the strongest evidence against the bottom line; alternative explanations; newer data; weaknesses in the key sources (method, sample, conflicts of interest); assumptions that would flip the conclusion if false.
Probe especially: <the 2–4 points you're least sure of, and options the draft never compared>.
Budget: about <10–15> tool calls. Record what you find as evidence cards in the format given in SKILL_DIR/references/researching.md, with IDs R-E1, R-E2 and so on.
Write to RESEARCH_DIR/checks/red-team.md
Report only to me: don't message the user or publish anything.
Reply with the 3 most serious challenges, each rated: changes the conclusion / lowers confidence / minor.
```

## Gap-filling brief

Use the researcher brief, but make the sub-question the specific gap or conflict, using an ID such as `G1`. List what is already known so the researcher doesn't repeat it, and set a smaller budget (about 8 tool calls).
