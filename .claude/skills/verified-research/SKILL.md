---
name: verified-research
description: Rigorous multi-source research that ends in a sourced, fact-checked answer with calibrated confidence. Use this skill whenever the user asks to research, investigate, look into, dig into, compare or evaluate options, tools, vendors or products, review the evidence or literature, fact-check a claim or statistic, trace where something came from, find out what is current or true about something, or do market, competitor, legal/regulatory, technical or scientific research - even if they never say "research". It scales itself, from a quick cited answer for a simple lookup to parallel researcher subagents plus independent claim-by-claim verification for comparisons, surveys and contested questions. Prefer it over generic deep-research skills whenever accuracy and checkable citations matter. Not for pure coding, creative writing, or questions fully answered by a file the user provided.
compatibility: Works best with web search and fetch tools plus a subagent tool (Agent or Task); falls back to single-agent mode without one. Helper scripts need Python 3 (standard library only).
---

# Verified Research

Research the question, then prove the answer. Every claim in the final output is backed by a source that was actually opened, checked by someone who didn't write it, and labeled with how sure we are.

## Why it works this way

Two findings shape everything below:

- **Effort and parallelism buy coverage.** Spending more search effort, split across parallel subagents with clean contexts, is the biggest driver of finding the decisive material. Anthropic's multi-agent research system beat a single agent by about 90% on its internal research eval.
- **Coverage does not buy accuracy.** Deep-research agents usually keep their links valid but get many cited facts wrong (a 2026 audit measured 39–77% factual accuracy on cited facts for frontier models), and accuracy *drops* as tool calls pile up. So checking is a separate phase done with fresh eyes, and budgets are real limits, not suggestions.

When a step below feels like overhead, remember which of these two failures it prevents. Installing this skill opts in to parallel subagents for Standard and Deep research; the tier budgets below keep their cost proportionate.

## Step 0: pick the tier, and be willing to escalate

Decide how much work the question deserves before doing any. Over-researching wastes the user's time and money, and long runs make more errors; under-researching a contested question produces a confident wrong answer.

| Tier | Typical question | Who works | Research budget (every search and fetch counts, failed ones too) | Checking | Output |
|---|---|---|---|---|---|
| **Quick** | One fact, number, date, version, definition, "is X still true?" | You alone | 2–8 tool calls in total | Re-read the supporting sentence | Chat answer, about 150–200 words |
| **Standard** | Comparison, evaluating a tool or vendor, focused how/why, fact-checking a claim, 2–4 facets | 2–4 researchers, ~10–15 calls each; alone: ~35 calls | Verifier: about one fetch per cited source; red team only if contested or high-stakes (~5–10 calls) | Report (600–1,200 words of prose; tables extra) + chat summary |
| **Deep** | Broad survey, landscape, literature review, contested or high-stakes decision, many entities | 4–6 researchers, ~15–20 calls each (up to ~10–12 researchers only if the user asks for exhaustive or "go deep"); alone: ~60 calls | Red team (~10 calls), then verifier(s): about one fetch per cited source | Report (1,200–2,500 words of prose; tables extra) + chat summary |

Checking is budgeted separately because it's where accuracy comes from; keep research inside its budget so checking stays affordable. Done alone, a whole Standard run should come in under about 70 searches and fetches, and a Deep run under about 120 (file writes and script runs don't count).

Start at the lowest tier that could plausibly answer the question. Escalate when the evidence demands it: sources conflict, the trail runs through layers of re-reporting, or the "simple" fact depends on definitions.

Tell the user in one plain sentence what you're about to do, for example "I'll check the official release schedule" or "I'll research this from several angles and fact-check the result; it'll take a few minutes." Don't use the tier names with the user; they're internal. For Standard and Deep work, if you have a task-list tool, add items for the phases (for example "Plan the research", "Gather evidence", "Verify claims", "Write the report") without mentioning subagents.

**No subagent tool?** (No Agent or Task tool, for example because you are yourself a subagent.) Run the same phases yourself, within the "alone" budgets above:
- Research the sub-questions one at a time. **After every batch of about five tool calls, append the evidence cards you have so far to that sub-question's notes file.** Work that exists only in your context is lost if the run is interrupted, and long contexts make you less accurate.
- When a red team is called for, do it as a separate pass of about 5–10 searches for the strongest counter-evidence, before verification.
- Do verification as a deliberate, separate final pass. Work from the claims checklist, not the draft, open each cited source once, and check its claims as if someone else had written them.

## Ground rules for every tier

1. **Use today's date.** Write it in the plan and in every brief. For anything that can change (prices, versions, laws, office-holders, rankings, model releases, statistics), search instead of trusting memory, record each source's date, and say "as of <date>".
2. **Only cite what was opened.** A URL goes into the answer only if you or a subagent fetched that page in this session and it says what you claim. Search snippets are leads, not evidence.
3. **Go to the origin.** Trace claims to whoever produced them: official docs, filings, datasets, the law's text, the paper, the person's own words. Count independent origins, not URLs; five articles repeating one press release are one source, and a second page from the same organization isn't independent confirmation.
4. **Search where the evidence lives.** Search in the language of the primary sources (Arabic for Jordanian law, Japanese for Japanese filings), on the jurisdiction's official sites, and in specialist databases. Write the final answer in the user's language.
5. **Look for the case against.** Before concluding, search for criticism, failures, replications and competing explanations. A one-sided pile of confirmations is a warning sign, not a result.
6. **Say what you don't know.** Gaps, unresolved conflicts and unverifiable claims go into the answer explicitly. Never smooth them over or fill them in.
7. **Serve the user's purpose.** Answer the question as asked, then add the practical implications for what the user said they're doing: the gotcha that will bite them, the local cost, the next step. If they're about to act (pin a version, upgrade, buy, sign, migrate), spend a search on what commonly breaks or surprises people at that step, such as release notes or known issues. The best answers connect the evidence to the decision.
8. **The user's own material.** If the question is about the user's own work, company or data, search their connected apps (Drive, email, Slack, GitHub and similar) and treat those records as primary sources. For public-world questions stay on the web, and never put private details into web search queries.

## Quick tier

1. Run 2–4 short searches. Open the most authoritative result. Also open one independent confirmation, unless that result is itself the authority (for example, the project's own release page for a version number); then one primary source is enough.
2. Re-read the exact sentence that supports the answer. Check that the number, unit, date and scope match what you are about to say.
3. Answer in about 150–200 words of prose (links and code don't count):
   - the answer first, with its citation and "as of <date>";
   - the one or two practical implications that matter for what the user said they're doing, such as a breaking change, a deadline or a better option;
   - a one-line confidence statement.
4. Escalate to Standard if sources disagree, the answer depends on definitions, or the trail leads through re-reporting.

## Standard and Deep workflow

### 1. Frame

Restate the question in one sentence, then pin down:
- the decision or use it serves;
- the exact entities;
- the time window (as of today unless told otherwise);
- the geography or jurisdiction;
- the languages of the primary sources;
- what a complete answer must contain.

Read `references/question-types.md` for the matching playbook (comparison, technical, literature review, medical, market, legal, fact-check, forecast and more).

Ask the user only what would change the plan, such as an ambiguous entity, jurisdiction, time frame or purpose. Ask at most 1–3 questions, ideally with options. For a broad Deep-tier topic the user hasn't narrowed, confirm the scope before spending heavily. If nobody is there to answer, state your assumptions and proceed.

### 2. Plan on disk

Create `research/<YYYY-MM-DD>-<short-slug>/` in the working directory and write `plan.md` with:
- the framed question and today's date;
- 2–6 sub-questions (S1, S2…) that together cover the question without overlapping;
- the perspectives to cover (for contested topics: proponents, critics, independent evaluators, affected users, regulators);
- the source strategy for each sub-question;
- budgets and the stop rule.

The plan on disk is your memory if the context grows long or the run is interrupted. Re-read it before you synthesize, and first thing when resuming.

### 3. Research in parallel

Spawn one researcher per sub-question. Launch them all in a single turn so they run in parallel, and wait for all of them to finish; don't run them in the background.

Write each brief from the template in `references/briefs.md`. A brief contains the objective, the boundaries (what the other researchers cover), time, place and language constraints, sources to prefer and avoid, a budget, and the absolute output path `notes/<id>-<slug>.md`. Each researcher's first step is to read `references/researching.md`; give them its absolute path. Vague briefs are the main cause of duplicated work and gaps, so spend the effort here.

Researchers reply with short summaries. Their evidence lives in their notes files as **evidence cards** (claim, verbatim quote, source, date, tier).

### 4. Check coverage

Run `python SKILL_DIR/scripts/evidence.py summary <research-dir>`. Here SKILL_DIR is this skill's base directory; use `python3` if `python` isn't found. For fast-changing facts (prices, versions, statistics) add `--since <date>` to flag stale sources; leave it off for laws, papers and history, where an old date isn't a problem. The summary validates the cards and shows, for each sub-question, how many independent origins and which source tiers back it. It also lists format problems and the researchers' reported conflicts and gaps.

- **Coverage is adequate:** go to synthesis.
- **A critical gap or unresolved conflict remains:** run **one** targeted gap-filling round (1–3 researchers, or about 8 calls alone), then move on regardless. Past this point, more exploration tends to add noise and errors faster than accuracy.

### 5. Synthesize the draft

Read the notes and write `draft.md` using the template in `references/report-templates.md` that fits the question type. Put the bottom line first, then the findings, the practical implications, disagreements, what would change the conclusion, gaps, and sources. While drafting:
- **Cite every specific claim.** Each number, date, name, quote, ranking, superlative and causal claim gets an inline citation to the source of an evidence card. Label your own arithmetic and inferences as such ("my arithmetic", "my inference").
- **Report the evidence as it is.** Keep ranges and disagreements rather than averaging them away, and explain why sources differ (definitions, dates, methods, incentives).
- **Calibrate.** Use likelihood words with fixed meanings, plus a separate High, Moderate or Low label for confidence in the evidence (see the templates).
- **Respect the length.** Prose counts toward the tier's limit; tables don't. If you're over, cut repetition, merge sections, and move detail into tables. Length costs the reader.

### 6. Challenge (Deep, and any contested or high-stakes Standard question)

Spawn a red-team subagent with the bottom line and the key findings (template in `references/briefs.md`). It hunts for the strongest disconfirming evidence and alternative explanations, checks the key assumptions, and runs a premortem; the techniques are in `references/analysis.md`. Where it lands a blow, revise the conclusion or the confidence. Either way, record the strongest counter-argument in the draft. The challenge comes before verification so that one verification pass covers everything, including what the red team added.

### 7. Verify (never skip)

1. **Audit the draft.** Run `python SKILL_DIR/scripts/audit_report.py <research-dir>/draft.md --evidence <research-dir>`. It writes a numbered claims checklist to `checks/claims.md`, marking high-priority claims and listing them by source. It also flags specific claims with no citation, and any cited URL that no researcher gathered (a classic sign of an invented source). Fix what it flags.
2. **Check links, if the shell has internet access.** Claude Code on a personal machine usually has it; sandboxes often don't. Run `python SKILL_DIR/scripts/check_links.py <research-dir>/draft.md --evidence <research-dir>` to catch dead links and quotes that don't appear on their page. Some sites refuse scripts, so re-open a page flagged NOT FOUND or BLOCKED with your fetch tool before dropping it. If it reports that the network is blocked, skip it; the verifier covers this.
3. **Spawn a verifier subagent.** Use the verifier template in `references/briefs.md` and give it the claims checklist, not the draft's argument. It re-opens each source and labels every claim SUPPORTED, PARTIAL, NOT SUPPORTED, CONTRADICTED or UNREACHABLE, quoting the exact sentence. Fresh eyes matter: a writer checking its own draft tends to see what it meant, not what the source says.
   - **Scope:** check every high-priority claim (the bottom line, key findings, numbers, quotes, anything the decision rests on), and spot-check the rest. For a Standard report that's usually 15–30 claims.
   - **Work by source:** open each cited source once and check every claim that cites it, using the "By source" list at the end of the checklist. That's usually far fewer fetches than claims.
   - Split more than about 25 claims across parallel verifiers, dividing by source, and have each label only its part of a claim that cites sources from both sets.
4. **Apply the results.** Fix or cut anything not supported. Reword partial matches to exactly what the source says. Replace unreachable sources, or mark the claim as unverified. Note in the method line what verification changed. If you add a new factual claim after this point, check it against its source before delivering.

### 8. Deliver

Save the final version as `report.md` in the research folder. (If your environment won't let you write a file with that name, keep the final as `draft.md` and say so.) In chat, give the user the bottom line in 3–6 sentences: the answer, the confidence, and the biggest caveat. Then deliver the report however your environment delivers files or documents. Don't paste a long report into chat.

**If tools start failing mid-run** (rate limits, outages): make sure the plan and notes are saved, then tell the user what's done and what's left, rather than pushing on with degraded tools. If a subagent stops early, read its output file before re-running it, because it may have finished the work; near a usage limit, run the red team and verifiers one at a time.

## Failure modes and their guards

| Failure | Guard |
|---|---|
| The citation exists but doesn't say what the claim says (the most common error) | Evidence cards carry verbatim quotes; an independent verifier re-opens the sources |
| Invented or dead URLs | Cite only fetched pages; the audit flags URLs no researcher gathered; `check_links.py` |
| A fetch tool's paraphrase gets recorded as a quote | Ask for verbatim text; confirm exact wording that matters with a second fetch or the raw source |
| SEO farms and vendor marketing outrank real sources | Source tiers in `researching.md`; go straight to primary hosts |
| Stale facts presented as current | Today's date in every brief; record source dates; `--since` in the coverage check |
| Circular reporting inflates confidence | Count independent origins (the card's `Origin` field), not URLs |
| Confirmation bias or settling too early | Disconfirming searches in every brief; a red team for contested questions |
| Over-research (cost, noise, more errors) | Tier budgets; one gap-filling round; verify high-priority claims rather than searching more |
| Under-research | The coverage check: key claims need two independent origins or one authoritative primary source |
| Lost work after an interruption | Notes written every few tool calls; the plan on disk; resume from them |
| Answers that are correct but not useful | Ground rule 7: connect the evidence to the user's decision and situation |

## Files in this skill

- `references/researching.md`: the researcher manual (search craft, source tiers, evidence-card format, stop rules). Give its absolute path to every researcher. Read it yourself in the Quick tier or when working without subagents.
- `references/briefs.md`: fill-in templates for researcher, verifier and red-team briefs.
- `references/question-types.md`: playbooks by question type, covering where the evidence lives and what a complete answer contains.
- `references/verification.md`: how to check claims against sources. It is given to verifiers.
- `references/analysis.md`: the key assumptions check, competing hypotheses, premortem, base rates and red teaming.
- `references/report-templates.md`: output structures by question type, the confidence vocabulary and citation rules.
- `scripts/evidence.py`: validates evidence cards and summarizes coverage (`summary`, `check`, `urls`).
- `scripts/audit_report.py`: writes the claims checklist and flags uncited specific claims and URLs no researcher gathered.
- `scripts/check_links.py`: a live link and quote check (needs internet access from the shell).

The scripts use only the Python 3 standard library and work on Windows, macOS and Linux.
