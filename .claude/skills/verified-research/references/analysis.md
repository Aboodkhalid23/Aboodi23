# Analytic techniques

Use these techniques when a question is contested, when the answer is a forecast or estimate, when the stakes are high, and in the red-team pass. They counter the predictable failure of careful researchers: settling early on an answer and then collecting confirmations.

## Key assumptions check

List the assumptions the conclusion silently depends on, for example "the 2024 pricing still applies", "the study's sample resembles the user's team" or "the regulation is in force". For each one, ask how solid it is and what changes if it's false. Verify the shaky ones, or state them in the report.

## Competing hypotheses (a lightweight version of Analysis of Competing Hypotheses)

1. Write down 2–4 plausible answers, including ones you don't favor.
2. List the most important pieces of evidence.
3. For each pairing of evidence and hypothesis, mark it Consistent, Inconsistent or Neutral.
4. Prefer the hypothesis with the **least inconsistent** evidence, not the one with the most consistent evidence. A lot of evidence fits several hypotheses and so tells you little.
5. Name the evidence that would best tell the surviving hypotheses apart, and look for it.

## Premortem

Imagine it's a year later and the conclusion turned out to be wrong. Write down the 3–5 most plausible reasons why. Check each one that can be checked now, and mention the rest as risks.

## Estimates and forecasts

- **Start with the outside view.** Find a reference class and its base rate (for example, how often projects like this ship on time), then adjust for the specifics.
- **Decompose the quantity** (Fermi estimation). Break it into factors you can source, show the arithmetic, and carry ranges through rather than single points.
- **Triangulate.** Compare independent estimates, such as top-down versus bottom-up, or different firms' market sizes, and explain why they differ.
- Give the answer as a range or a probability, along with the indicators that would move it.

## When sources disagree

Don't average incompatible numbers or quietly pick a side. Explain the disagreement. Common causes are different definitions, populations, time periods, methods (self-reported versus measured, lab versus field) and incentives. Then say which source fits the user's situation best.

## Red team

Your job is to make the conclusion fail if it deserves to:
- Search directly for the strongest counter-evidence and the best-argued opposing view, and present that view at its strongest.
- Look for newer data, replications or retractions that undercut the key sources.
- Attack the weakest links: a claim that rests on a single source, a source with an interest, an extrapolation from a different population.
- Run the key assumptions check and a premortem.

Rate each challenge as **changes the conclusion**, **lowers confidence** or **minor**. If the red team finds nothing, it should say what it tried.

## Signposts

For forecasts and fast-moving topics, list 2–4 observable indicators that would change the assessment, for example "if X ships Y by Q2" or "if the regulator publishes the executive regulations".
