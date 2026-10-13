# Question-type playbooks

Use the matching playbook when framing and planning. Each one says where the decisive evidence usually lives, what a complete answer contains, and the traps specific to that kind of question. Copy the relevant source suggestions into researcher briefs.

## Contents
- Comparing or evaluating tools, products and vendors
- Technical deep dives
- Scientific and literature reviews
- Medical and health questions
- Market, competitor and industry research
- Legal and regulatory questions
- Fact-checks and origin traces
- Forecasts and estimates
- Current events
- People and organizations
- The user's own work (internal sources)

## Comparing or evaluating tools, products and vendors
- **Start with the criteria.** Derive them from the user's use case (scale, budget, team skills, region, compliance). A generic feature list isn't an evaluation.
- **Evidence:**
  - official docs, pricing pages and limits pages (record the date, because they change);
  - changelogs and status or incident history;
  - independent benchmarks with published methods;
  - GitHub issues and discussions, for real-world pain points;
  - migration stories.
- **Traps:**
  - vendor benchmarks, and "X vs Y" pages written by X;
  - outdated pricing in third-party articles;
  - comparing different plan tiers;
  - features that are in beta or limited to some regions.
- **A complete answer has:** a sourced criteria table, "choose A if… / B if…", a recommendation for the user's situation, and what would change it.

## Technical deep dives
- **Evidence:** specs and RFCs, the official docs for the exact version, source code, release notes, maintainers' posts, design docs, conference talks by the authors, and reproducible benchmarks.
- **Traps:** answers that apply to an old major version, blog tutorials that repeat one another, and benchmarks published without their settings.
- **A complete answer has:** the mechanism, the evidence with versions, trade-offs, failure modes and concrete guidance.

## Scientific and literature reviews
- **Frame the question** with PICO (population, intervention or exposure, comparison, outcome), or the equivalent for non-clinical topics.
- **Evidence:**
  - Systematic reviews and meta-analyses come first (Cochrane, and PubMed with a "systematic review" filter), then the key primary studies.
  - Use Semantic Scholar and Google Scholar for coverage and citation trails.
  - Use arXiv, bioRxiv and medRxiv for preprints, and flag them as preprints.
- **Extract:** the design, the sample size and population, effect sizes with confidence intervals, the follow-up period and the funding.
- **Traps:**
  - single small studies reported as settled science;
  - press releases that overstate their paper;
  - retracted papers (check the important ones);
  - surrogate outcomes;
  - correlation reported as causation.
- **A complete answer has:** an evidence table, a certainty rating (High, Moderate, Low or Very low) with the reasons, where studies disagree and why, and the gaps.

## Medical and health questions
Treat these like a literature review, and add clinical guidelines (WHO, national health agencies, specialist societies) and regulatory labels (FDA, EMA). Present the findings as information, not personal medical advice. Recommend a clinician for individual decisions, and don't go beyond the official labeling on dosing.

## Market, competitor and industry research
- **Evidence:**
  - company filings and annual reports, earnings calls and investor presentations;
  - official statistics;
  - pricing pages and product docs;
  - job postings and other hiring signals;
  - credible industry analysts (cite their figures as analyst estimates);
  - funding databases.
- **Traps:**
  - market-size figures from the press releases of firms selling reports (they vary wildly, so triangulate and explain the spread);
  - stale figures;
  - numbers for private companies that are only estimates.
- **A complete answer has:** a dated landscape table, trends with evidence, drivers and risks, and signposts.

## Legal and regulatory questions
- **Evidence:**
  - The official text, in the jurisdiction's own language, from official sources: the official gazette, the government's legislation portal and the regulator's site.
  - Official guidance and executive regulations or instructions.
  - Reputable law-firm briefings. Treat these as tier 2, useful for orientation but never a substitute for the text.
- **Pin down:**
  - the jurisdiction;
  - the instrument's name, number and year;
  - its publication and effective dates;
  - amendments and transitional periods;
  - whether implementing regulations have been issued.
- **Traps:**
  - drafts or bills reported as law;
  - repealed versions;
  - English summaries that drop conditions;
  - a similar law from another country.
- **A complete answer has:** the instrument and its status, a checklist of obligations, penalties, open or pending items, and a note that this is research, not legal advice.

## Fact-checks and origin traces
- **Trace backward.** Find the earliest appearance of the claim, using date-restricted searches, the chain of citations in articles, and archives. Identify the original source, then read what it actually says, how it was produced (method and sample), and who funded it.
- **Look for mutation.** Note how the claim changed as it was retold, for example "up to 50%" becoming "50%", or one survey of 500 people becoming "studies show".
- **A complete answer has:** a verdict, the trace, what the best evidence says, and the context.

## Forecasts and estimates
Follow the "Estimates and forecasts" section of `analysis.md`: base rates, decomposition, triangulation and indicators. Prediction markets and forecasting platforms are one input, not the answer.

## Current events
Prefer wire services, outlets that do original reporting, official statements and primary documents. Timestamp everything. Flag developing situations and unconfirmed reports as such, and check again right before delivering.

## People and organizations
For public figures and organizations, use official bios, company registries, filings and the person's own published work. Don't compile personal information about private individuals, such as a home address, contact details or family details; decline that part.

## The user's own work (internal sources)
When the question is about the user's own company, projects, documents or conversations, search their connected apps first (Drive, email, Slack, GitHub, Notion, calendars and so on), and treat those records as primary sources. Cite each one by its title and link. Add web sources only for the public parts of the question, and keep private details out of web queries.
