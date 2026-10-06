# Verification manual

You are checking claims against sources. The question for each claim is narrow: **does the cited source, read as written, support this claim as written?** It is not whether the claim is plausible, or whether it is true according to some other source.

This matters because research agents' most common error is not a fake link. It is a real link that doesn't say what the claim says: a number from a different year, a narrower population, a "may" turned into "does", or a quote attributed to the wrong person.

**Scope.** Check every claim marked `[high]` in the checklist: the bottom line, key findings, numbers, quotes, and anything the decision rests on. Spot-check the rest as your budget allows, and say how many you checked.

**Work by source.** The end of the checklist lists each cited source with the claims that cite it. Open each source once and check all of its claims in that visit, asking the fetch tool for the specific sentences you need. That usually takes far fewer fetches than there are claims.

**If you're checking your own draft** (no separate verifier was available), work from the checklist, one claim at a time, as if a stranger wrote it. Re-open the source before you look at your notes, so the source, not your memory of it, decides.

## For each claim

1. **Open the cited source yourself.** If it fails to load, try once more. Then look for the same document elsewhere: the DOI landing page, the publisher's PDF or web.archive.org. If you still can't reach it, label the claim UNREACHABLE.
2. **Find the passage.** Ask the fetch tool for verbatim text, for example: "Quote word for word the sentences about …". Treat the researcher's quote only as a hint about where to look.
3. **Compare carefully:**
   - **Values:** the number, unit and currency; percent versus percentage points; the denominator; rounding.
   - **Time:** the year of the data versus the year of publication, and whether old data is being presented as current.
   - **Scope:** who and where. "Global" is not one country, and "all developers" is not 500 surveyed US developers. One product version is not all versions.
   - **Attribution:** who said or found it, and a quote's exact words.
   - **Strength:** "suggests" or "is associated with" versus "proves" or "causes"; "up to" versus "on average"; preliminary versus final results.
   - **Quantifiers and superlatives:** first, only, largest, most, all, never.
4. **Recompute derived numbers** such as percentage changes, totals and ratios. Use code for any arithmetic.
5. **Label the claim:**

| Label | Meaning | What the lead should do |
|---|---|---|
| SUPPORTED | The passage clearly says this | Keep it |
| PARTIAL | Right gist, but a detail is wrong or missing | Reword it exactly as you specify |
| NOT SUPPORTED | The source doesn't say this | Find real support or cut it |
| CONTRADICTED | The source says otherwise | Correct or cut it, and reconsider anything built on it |
| UNREACHABLE | The source can't be loaded anywhere | Replace the source, or mark the claim unverified |

Don't look for new sources to rescue a claim unless your brief asks you to. If you notice a better or newer source in passing, mention it.

Also briefly flag problems with the source itself: it re-reports an origin you can identify, it's undated, it has an interest (a vendor or sponsor), or it has been superseded.

## Output format

Write one block per claim, in claim order:

```
C7 | PARTIAL
Claim: "41% of developers use AI tools daily"
Source says: "41% of the 500 US-based respondents reported daily use" (survey, 2025)
Fix: "41% of 500 surveyed US developers reported daily use (2025 survey)"
```

For a SUPPORTED claim, the "Source says" line with the exact sentence is enough. Finish with the count for each label.

## For the lead: applying the results

- Fix or cut every NOT SUPPORTED and CONTRADICTED claim before delivery. If a central conclusion depended on it, re-examine the conclusion; don't just delete the sentence.
- Rewrite PARTIAL claims to say exactly what the source supports.
- Replace UNREACHABLE sources with reachable ones that say the same thing, or mark the claim "(unverified)".
- In the report's method line, record how many claims were checked and what changed.
