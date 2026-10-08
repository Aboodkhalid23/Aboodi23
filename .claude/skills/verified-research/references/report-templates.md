# Report templates

Write for a busy reader: the answer first, then the support, then the honest part (disagreements, limits and gaps). Write in the user's language.

The length follows the tier: about 150–200 words for a Quick answer, 600–1,200 words of prose for a Standard report, and 1,200–2,500 for a Deep one. Tables don't count toward the limit, so put detail there. Don't pad; a short, well-sourced report beats a long one. If you're over, cut repetition between sections first.

## The skeleton for Standard and Deep reports

```
# <A title that states the answer, not just the topic>

**Bottom line:** 2–4 sentences that answer the question directly: the key number or recommendation, the overall confidence, and the single biggest caveat.

## Key findings
- 3–7 findings, each a specific, cited sentence, with a confidence label wherever the confidence isn't obvious.

## <Body sections for the question type, listed below>

## What this means for you
The practical implications for the user's stated situation: the gotcha that will bite them, local costs or rules, setup steps, and the next action. Keep it concrete and short.

## Where the evidence disagrees
What conflicts and why (definitions, dates, methods, incentives), and which side fits the user's situation.

## What would change this conclusion
The assumptions the conclusion rests on, and the evidence that would overturn it. For fast-moving topics, list signposts to watch.

## Gaps and unverified points
What couldn't be established, and which claims remain unverified and why.

## Sources
Grouped as Primary, Secondary and Other. Give each one's title, publisher and date, with its link.

---
Method: <how it was researched, in plain words, e.g. "4 researchers in parallel" or "researched alone">; <n> sources consulted (<n> primary); <n> claims checked against their sources, <n> corrected or removed; researched <YYYY-MM-DD>.
```

Drop a section only if it would be empty. Write "No significant disagreements found" rather than inventing some.

## Body sections by question type

- **Comparison or evaluation:**
  - A criteria table. Its rows are the criteria that matter for the user's use case, and every cell is sourced or marked "not published".
  - "Choose A if… / Choose B if…".
  - A recommendation for the user's stated situation.
- **Technical deep dive:**
  - How it works.
  - The evidence, including benchmarks with their settings and versions.
  - Trade-offs and failure modes.
  - Implementation guidance.
  - The versions and dates the answer applies to.
- **Literature or evidence review:**
  - The question. For clinical questions, use PICO: population, intervention, comparison, outcome.
  - What was searched, and when.
  - An evidence table: study, design, sample size, population, finding with effect size, and quality.
  - The overall certainty (High, Moderate, Low or Very low, in the style of GRADE), with the reasons for it.
- **Market or landscape:**
  - A dated landscape table: players, offering, scale, pricing and positioning.
  - Trends, with dated evidence.
  - Drivers and risks.
  - Signposts to watch.
- **Legal or regulatory:**
  - The governing instruments, each with its number, date and status (in force, amended or draft).
  - The obligations, as a checklist.
  - Penalties.
  - What is still pending, such as executive regulations.
  - A note that this is research, not legal advice, and when to consult a local lawyer.
- **Fact-check:**
  - A verdict: True, Mostly true, Mixed, Mostly false, False or Unproven.
  - The origin trace: who first said it, when, and based on what.
  - What the best evidence shows.
  - Why the claim spread, or what it gets wrong.
- **Forecast or estimate:**
  - The base rate.
  - The decomposition, with its arithmetic.
  - The current indicators.
  - The estimate, as a range or a probability.
  - Signposts to watch.

## The Quick tier (a chat answer)

```
<The answer in one or two sentences, with the key value.> (<cited source>, as of <date>)
<One or two practical implications for what the user said they're doing: a breaking change, a deadline, a better option.>
Confidence: High / Moderate / Low, because <a few words>.
```

Keep it to about 150–200 words of prose; links and code don't count.

## Confidence vocabulary

Keep two things separate.

**How likely something is.** Use these words with these meanings, which come from the US intelligence community's analytic standard, ICD 203:

| Term | Probability |
|---|---|
| almost no chance | 1–5% |
| very unlikely | 5–20% |
| unlikely | 20–45% |
| roughly even chance | 45–55% |
| likely | 55–80% |
| very likely | 80–95% |
| almost certain | 95–99% |

**How solid the evidence is.** Use High, Moderate or Low confidence:
- **High:** several independent, high-quality sources agree, and there is little reasonable doubt.
- **Moderate:** the evidence is credible but limited, such as a single good source, minor conflicts or indirect evidence.
- **Low:** the evidence is sparse, conflicting, dated or of low quality.

Don't stack hedges, as in "may possibly suggest". State the claim and attach the right label once.

## Citations

- Put each citation inline, right after the claim it supports, for example: `... grew 38% in 2025 ([Statistics Agency](https://...))`.
- Link the exact page (a deep link or a DOI), not a homepage.
- In tables, put the citation in each row or cell that carries a fact. A single source line under a table doesn't tie each fact to its source.
- Cite every number, date, quote, ranking, superlative and causal claim. General framing doesn't need a citation.
- Mark weak or interested sources in the text, for example "(vendor benchmark)", "(preprint, not peer-reviewed)" or "(company announcement)".
- Label your own arithmetic and inferences as such, for example "(my arithmetic)" or "(my inference)", instead of attaching a citation to them.
- Never cite a page that wasn't opened in this session.

## Style

- Lead with the answer. Use headers that say something ("Prices diverge above 100k users") rather than bare labels ("Pricing").
- Use tables for comparisons, short paragraphs, and bullets for parallel findings. Bold key numbers sparingly.
- Interpret the data: say what a number means for the user's question.
- Take a position when the evidence supports one, and say plainly when it doesn't.
