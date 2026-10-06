#!/usr/bin/env python3
"""Audit a research draft before verification.

1. Writes a numbered checklist of every cited claim (C1, C2, ...) to checks/claims.md,
   with the researcher's quote for that source as a hint for the verifier.
2. Flags specific claims (numbers, dates, quotes, superlatives) that carry no citation.
3. Flags cited URLs that no evidence card contains (a possible invented or unvetted source).

Usage:
  python audit_report.py DRAFT.md [--evidence RESEARCH_DIR] [--out CLAIMS.md]

Citations are recognized as inline markdown links, bare URLs, footnotes ([^1]) and
numbered references ([3]) that resolve through a Sources/References list.
Standard library only; works on Windows, macOS and Linux.
"""

import argparse
import re
import sys
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from evidence import (_utf8_stdout, clean_url, evidence_url_index, load_evidence,  # noqa: E402
                      normalize_url)

HEADING_RE = re.compile(r"^(#{1,6})\s+(.*?)\s*#*\s*$")
SOURCES_HEADING_RE = re.compile(
    r"^(sources|references|bibliography|works cited|citations|links|"
    r"المصادر|المراجع)\b",
    re.IGNORECASE)
PRIORITY_HEADING_RE = re.compile(
    r"(key findings|bottom line|summary|tl;?dr|verdict|recommendation|answer|conclusion|"
    r"الخلاصة|النتائج|"
    r"التوصية)", re.IGNORECASE)
MD_LINK_RE = re.compile(r"\[((?:[^\[\]]|\[[^\]]*\])*)\]\(\s*<?(https?://(?:[^()\s<>]|\([^()\s<>]*\))+)>?(?:\s+\"[^\"]*\")?\s*\)")
BARE_URL_RE = re.compile(r"https?://[^\s<>\"'\]\[`]+")
FOOTNOTE_REF_RE = re.compile(r"\[\^([^\]\s]+)\](?!:)")
NUM_REF_RE = re.compile(r"(?<![\]\w])\[(\d{1,3}(?:\s*[,–-]\s*\d{1,3})*)\](?![(:])")
FOOTNOTE_DEF_RE = re.compile(r"^\s*\[\^([^\]\s]+)\]:\s*(.*)$")
NUMBERED_SOURCE_RE = re.compile(r"^\s*(?:[-*+]\s*)?(?:\[(\d{1,3})\]|(\d{1,3})[.)])\s+(.*)$")
BULLET_RE = re.compile(r"^(\s*)(?:[-*+]|\d{1,3}[.)])\s+(.*)$")
METHOD_RE = re.compile(r"^\s*[*_]{0,2}\s*(method|methodology|\u0627\u0644\u0645\u0646\u0647\u062c\u064a\u0629|\u0645\u0646\u0647\u062c\u064a\u0629)", re.IGNORECASE)
# Sections whose sentences are forward-looking, admissions or actions, not claims that need a citation.
NO_FLAG_HEADING_RE = re.compile(
    r"(what would change|would change this|gaps|unverified|open questions|assumptions|limitations of this|"
    r"recommendation|next steps|what to do|action plan|pilot plan|how to raise|"
    r"\u062b\u063a\u0631\u0627\u062a|\u063a\u064a\u0631 \u0645\u062d\u0633\u0648\u0645\u0629|\u0645\u0627 \u0627\u0644\u0630\u064a \u0642\u062f \u064a\u063a\u064a|"
    r"\u0627\u0644\u062a\u0648\u0635\u064a|\u0627\u0644\u062e\u0637\u0648\u0627\u062a|\u0627\u0628\u062f\u0623\u0648\u0627|\u0627\u0644\u0627\u0641\u062a\u0631\u0627\u0636)", re.IGNORECASE)
# Sentences the author has labeled as their own arithmetic, inference or assumption.
SELF_LABEL_RE = re.compile(
    r"(my arithmetic|arithmetic:|my calculation|my inference|my estimate|my read|my assessment|my judgment|my judgement|my verdict|I assume|assuming|assumption|"
    r"\u062d\u0633\u0627\u0628\u064a|\u0627\u0633\u062a\u0646\u062a\u0627\u062c\u064a|\u0627\u0641\u062a\u0631\u0636|\u0627\u0641\u062a\u0631\u0627\u0636)", re.IGNORECASE)

# A sentence that opens with a bold or plain label, e.g. "**Recommendation:** start on ...".
LEAD_LABEL_RE = re.compile(r"^\s*(?:[-*+]\s+)?(?:\*\*|__)?([^*_:\n]{2,40}?)(?:\*\*|__)?\s*:")
HINT_WORD_RE = re.compile(r"[^\W_]{4,}|\d[\d.,]*", re.UNICODE)

DIGIT_RE = re.compile(r"[0-9٠-٩۰-۹]")
QUOTE_RE = re.compile(r"[“\"«]([^”\"»]{12,})[”\"»]")
ABSOLUTE_RE = re.compile(
    r"\b(first|only|largest|biggest|smallest|most|least|best|worst|fastest|slowest|highest|"
    r"lowest|leading|record|never|always|every|all|none|unique|unprecedented|majority|minority|"
    r"doubled|tripled|halved)\b", re.IGNORECASE)
ARABIC_ABSOLUTE_RE = re.compile(
    "(أكبر|أول|أفضل|الأكثر|"
    "الوحيد|أعلى|أدنى|أقل)")
ATTRIBUTION_RE = re.compile(
    r"\b(according to|found that|reported|reports that|estimated|estimates|survey|study|studies|"
    r"research shows|data show|announced|requires|prohibits|mandates|fined|penalt)", re.IGNORECASE)
ARABIC_ATTRIBUTION_RE = re.compile(
    "(وفقا|وفقًا|بحسب|"
    "أظهرت|دراسة|تقرير|"
    "يلزم|غرامة)")

ABBREVIATIONS = ["e.g.", "i.e.", "et al.", "vs.", "etc.", "approx.", "U.S.", "U.K.", "E.U.",
                 "Dr.", "Mr.", "Ms.", "Mrs.", "Prof.", "No.", "Fig.", "Inc.", "Ltd.", "Co.",
                 "Corp.", "Jan.", "Feb.", "Mar.", "Apr.", "Jun.", "Jul.", "Aug.", "Sep.",
                 "Sept.", "Oct.", "Nov.", "Dec.", "St.", "p.", "pp.", "vol.", "ed.", "cf."]


def split_sentences(text):
    protected = text
    for i, abbr in enumerate(ABBREVIATIONS):
        protected = protected.replace(abbr, abbr.replace(".", "․"))
    protected = re.sub(r"(?<=\b[A-Z])\.(?=[A-Z]\.)", "․", protected)
    parts, start = [], 0
    boundary = (r"[.!?؟](?:[\"”’')\]]*)"
                r"(?:\[\^[^\]\s]+\]|\[\d{1,3}(?:\s*[,–-]\s*\d{1,3})*\])*\s+")
    for m in re.finditer(boundary, protected):
        nxt = protected[m.end():m.end() + 1]
        if nxt and ("a" <= nxt <= "z"):
            continue
        parts.append(protected[start:m.end()].strip())
        start = m.end()
    tail = protected[start:].strip()
    if tail:
        parts.append(tail)
    return [p.replace("․", ".") for p in parts if p]


def strip_citations(text):
    out = MD_LINK_RE.sub(lambda m: m.group(1), text)
    out = BARE_URL_RE.sub("", out)
    out = FOOTNOTE_REF_RE.sub("", out)
    out = NUM_REF_RE.sub("", out)
    out = re.sub(r"\(\s*\)", "", out)
    out = re.sub(r"(\*\*|__)", "", out)
    out = re.sub(r"\s+([.,;:!?؟،])", r"\1", out)
    return re.sub(r"\s+", " ", out).strip()


def is_specific(text):
    plain = strip_citations(text)
    plain_wo_md = re.sub(r"[*_`#>]", "", plain)
    if len(plain_wo_md.split()) < 4:
        return False, ""
    reasons = []
    if DIGIT_RE.search(plain_wo_md):
        reasons.append("number/date")
    if QUOTE_RE.search(plain_wo_md):
        reasons.append("quote")
    if ABSOLUTE_RE.search(plain_wo_md) or ARABIC_ABSOLUTE_RE.search(plain_wo_md):
        reasons.append("superlative/absolute")
    if ATTRIBUTION_RE.search(plain_wo_md) or ARABIC_ATTRIBUTION_RE.search(plain_wo_md):
        reasons.append("attribution/finding")
    return bool(reasons), ", ".join(reasons)


def parse_reference_lists(lines):
    """Map footnote ids and numbered references to URLs."""
    footnotes, numbered = {}, {}
    in_sources = False
    for line in lines:
        hm = HEADING_RE.match(line)
        if hm:
            in_sources = bool(SOURCES_HEADING_RE.match(hm.group(2).strip()))
            continue
        fm = FOOTNOTE_DEF_RE.match(line)
        if fm:
            urls = BARE_URL_RE.findall(fm.group(2)) + [m.group(2) for m in MD_LINK_RE.finditer(fm.group(2))]
            if urls:
                footnotes[fm.group(1)] = clean_url(urls[-1] if "](" in fm.group(2) else urls[0])
            continue
        if in_sources:
            nm = NUMBERED_SOURCE_RE.match(line)
            if nm:
                num = nm.group(1) or nm.group(2)
                rest = nm.group(3)
                links = [m.group(2) for m in MD_LINK_RE.finditer(rest)]
                urls = links or BARE_URL_RE.findall(rest)
                if urls:
                    numbered[num] = clean_url(urls[0])
    return footnotes, numbered


def citations_in(text, footnotes, numbered):
    urls = [clean_url(m.group(2)) for m in MD_LINK_RE.finditer(text)]
    rest = MD_LINK_RE.sub(" ", text)
    urls += [clean_url(u) for u in BARE_URL_RE.findall(rest)]
    unresolved = []
    for ref in FOOTNOTE_REF_RE.findall(rest):
        if ref in footnotes:
            urls.append(footnotes[ref])
        else:
            unresolved.append("[^%s]" % ref)
    for group in NUM_REF_RE.findall(rest):
        nums = []
        for piece in re.split(r"\s*,\s*", group):
            rng = re.split(r"\s*[–-]\s*", piece)
            if len(rng) == 2 and rng[0].isdigit() and rng[1].isdigit() and int(rng[1]) - int(rng[0]) < 30:
                nums.extend(str(n) for n in range(int(rng[0]), int(rng[1]) + 1))
            else:
                nums.append(piece.strip())
        for n in nums:
            if n in numbered:
                urls.append(numbered[n])
            else:
                unresolved.append("[%s]" % n)
    seen, out = set(), []
    for u in urls:
        if u and u not in seen:
            seen.add(u)
            out.append(u)
    return out, unresolved


def extract_units(text):
    """Split markdown into checkable units with line numbers and section context."""
    lines = text.splitlines()
    footnotes, numbered = parse_reference_lists(lines)
    units = []
    section, h2_seen, in_sources, in_code = "", False, False, False
    para, para_line = [], 0
    table_rows_seen = 0

    def flush_para():
        nonlocal para
        if para:
            units.append({"kind": "para", "line": para_line, "text": " ".join(para),
                          "section": section, "top": not h2_seen})
            para = []

    i = 0
    while i < len(lines):
        line = lines[i]
        s = line.strip()
        if s.startswith("```") or s.startswith("~~~"):
            flush_para()
            in_code = not in_code
            i += 1
            continue
        if in_code or s.startswith("<!--"):
            i += 1
            continue
        hm = HEADING_RE.match(line)
        if hm:
            flush_para()
            level, title = len(hm.group(1)), hm.group(2).strip()
            if level <= 2 and level > 1:
                h2_seen = True
            in_sources = bool(SOURCES_HEADING_RE.match(title))
            section = title
            table_rows_seen = 0
            i += 1
            continue
        if in_sources or FOOTNOTE_DEF_RE.match(line):
            flush_para()
            i += 1
            continue
        if not s or s in ("---", "***", "___"):
            flush_para()
            table_rows_seen = 0
            i += 1
            continue
        if METHOD_RE.match(s):
            flush_para()
            i += 1
            continue
        if s.startswith("|"):
            flush_para()
            if re.match(r"^\|?\s*:?-{2,}", s.replace(" ", "")) or set(s) <= set("|-: "):
                i += 1
                continue
            table_rows_seen += 1
            nxt = lines[i + 1].strip() if i + 1 < len(lines) else ""
            is_header = table_rows_seen == 1 and nxt.startswith("|") and set(nxt) <= set("|-: ")
            if not is_header:
                cells = [c.strip() for c in s.strip("|").split("|")]
                units.append({"kind": "table", "line": i + 1, "text": " | ".join(cells),
                              "section": section, "top": not h2_seen})
            i += 1
            continue
        bm = BULLET_RE.match(line)
        if bm:
            flush_para()
            start, body = i + 1, [bm.group(2).strip()]
            j = i + 1
            while j < len(lines) and lines[j].strip() and not BULLET_RE.match(lines[j]) \
                    and not HEADING_RE.match(lines[j]) and lines[j].startswith((" ", "\t")):
                body.append(lines[j].strip())
                j += 1
            units.append({"kind": "bullet", "line": start, "text": " ".join(body),
                          "section": section, "top": not h2_seen})
            i = j
            continue
        if line.startswith(">"):
            line = line.lstrip("> ")
        if not para:
            para_line = i + 1
        para.append(line.strip())
        i += 1
    flush_para()
    return units, footnotes, numbered


def audit(draft_path, evidence_dir=None):
    text = Path(draft_path).read_text(encoding="utf-8", errors="replace")
    units, footnotes, numbered = extract_units(text)
    ev_index = {}
    if evidence_dir:
        cards, _ = load_evidence(evidence_dir)
        ev_index = evidence_url_index(cards)
    claims, uncited, soft_uncited, not_in_evidence, unresolved_refs = [], [], [], [], []
    skipped_labeled = 0
    cited_norm = set()
    for u in units:
        if u["kind"] == "para":
            para_urls, _ = citations_in(u["text"], footnotes, numbered)
            pieces = split_sentences(u["text"])
        else:
            para_urls, pieces = [], [u["text"]]
        for piece in pieces:
            urls, unresolved = citations_in(piece, footnotes, numbered)
            for ref in unresolved:
                unresolved_refs.append((u["line"], ref))
            specific, why = is_specific(piece)
            if urls:
                high = u["top"] or bool(PRIORITY_HEADING_RE.search(u["section"] or "")) or specific
                claims.append({"line": u["line"], "text": strip_citations(piece), "raw": piece,
                               "urls": urls, "priority": "high" if high else "normal",
                               "section": u["section"]})
                for url in urls:
                    n = normalize_url(url)
                    cited_norm.add(n)
                    if evidence_dir and n not in ev_index:
                        not_in_evidence.append((u["line"], url))
            elif specific:
                lead = LEAD_LABEL_RE.match(piece)
                if (NO_FLAG_HEADING_RE.search(u["section"] or "") or SELF_LABEL_RE.search(piece)
                        or (lead and NO_FLAG_HEADING_RE.search(lead.group(1)))):
                    skipped_labeled += 1
                    continue
                entry = (u["line"], strip_citations(piece), why)
                (soft_uncited if para_urls else uncited).append(entry)
    seen, dedup = set(), []
    for line, url in not_in_evidence:
        if url not in seen:
            seen.add(url)
            dedup.append((line, url))
    listed = set(normalize_url(v) for v in list(footnotes.values()) + list(numbered.values()))
    sources_section_urls = set()
    in_sources = False
    for line in text.splitlines():
        hm = HEADING_RE.match(line)
        if hm:
            in_sources = bool(SOURCES_HEADING_RE.match(hm.group(2).strip()))
            continue
        if in_sources:
            for m in MD_LINK_RE.finditer(line):
                sources_section_urls.add(normalize_url(m.group(2)))
            for url in BARE_URL_RE.findall(MD_LINK_RE.sub(" ", line)):
                sources_section_urls.add(normalize_url(url))
    uncited_listed = sorted((sources_section_urls | listed) - cited_norm)
    return {"claims": claims, "uncited": uncited, "soft_uncited": soft_uncited,
            "not_in_evidence": dedup, "unresolved_refs": unresolved_refs,
            "uncited_listed": uncited_listed, "ev_index": ev_index,
            "skipped_labeled": skipped_labeled}


def best_hints(cards, claim_words, n=2):
    """Pick the cards for a source whose claim and quote share the most words with the draft claim."""
    def score(card):
        words = set(w.lower() for w in HINT_WORD_RE.findall(
            "%s %s" % (card.get("claim", ""), card.get("quote", ""))))
        return len(words & claim_words)
    ranked = sorted(enumerate(cards), key=lambda ic: (-score(ic[1]), ic[0]))
    return [card for _, card in ranked[:n]]


def write_claims(result, draft_path, out_path):
    ev_index = result["ev_index"]
    claims = result["claims"]
    high = sum(1 for c in claims if c["priority"] == "high")
    lines = ["# Claims checklist", "",
             "Draft: %s | Generated: %s | Claims: %d (high priority: %d)"
             % (draft_path, date.today().isoformat(), len(claims), high), "",
             "For each claim, open the cited source(s) and judge whether they support the Text as written.",
             "Evidence hints are researchers' quotes: use them to find the passage, but confirm it on the page.",
             ""]
    for n, c in enumerate(claims, 1):
        c["id"] = "C%d" % n
        lines.append("## C%d [%s] (draft line %d)" % (n, c["priority"], c["line"]))
        lines.append("Text: %s" % c["text"])
        claim_words = set(w.lower() for w in HINT_WORD_RE.findall(c["text"]))
        for url in c["urls"]:
            lines.append("Cited: %s" % url)
            for card in best_hints(ev_index.get(normalize_url(url), []), claim_words):
                quote = re.sub(r"\s+", " ", card.get("quote", ""))
                if len(quote) > 300:
                    quote = quote[:299] + "…"
                lines.append("Evidence hint: %s \"%s\"" % (card["id"], quote))
        lines.append("")
    # Index by source, so a verifier can open each source once and check all its claims together.
    by_source, shown = {}, {}
    for c in claims:
        for url in c["urls"]:
            key = normalize_url(url)
            shown.setdefault(key, url)
            if c["id"] not in by_source.setdefault(key, []):
                by_source[key].append(c["id"])
    lines += ["## By source (open each once, check all its claims)", ""]
    for key, ids in sorted(by_source.items(), key=lambda kv: -len(kv[1])):
        lines.append("- %s: %s" % (shown[key], ", ".join(ids)))
    lines.append("")
    Path(out_path).parent.mkdir(parents=True, exist_ok=True)
    Path(out_path).write_text("\n".join(lines), encoding="utf-8")


def _short(s, n=150):
    s = re.sub(r"\s+", " ", s).strip()
    return s if len(s) <= n else s[: n - 1] + "…"


def main(argv=None):
    _utf8_stdout()
    ap = argparse.ArgumentParser(description="Audit a research draft's citations.")
    ap.add_argument("draft")
    ap.add_argument("--evidence", help="research folder (or notes folder) with evidence cards")
    ap.add_argument("--out", help="where to write the claims checklist")
    args = ap.parse_args(argv)
    draft = Path(args.draft)
    if not draft.is_file():
        print("Not found: %s" % draft)
        return 2
    evidence_dir = Path(args.evidence) if args.evidence else None
    if evidence_dir and not evidence_dir.exists():
        print("Evidence folder not found: %s (continuing without it)" % evidence_dir)
        evidence_dir = None
    if args.out:
        out = Path(args.out)
    elif evidence_dir and evidence_dir.is_dir():
        out = evidence_dir / "checks" / "claims.md"
    else:
        out = draft.parent / "checks" / "claims.md"
    result = audit(draft, evidence_dir)
    write_claims(result, draft, out)

    claims = result["claims"]
    high = sum(1 for c in claims if c["priority"] == "high")
    print("Audit of %s" % draft)
    print("  Cited claims: %d (%d high priority), written to %s" % (len(claims), high, out))
    if not claims:
        print("  ! No citations found. Every specific claim needs an inline link to its source.")
    print("  Uncited specific claims: %d" % len(result["uncited"]))
    for line, text, why in result["uncited"][:30]:
        print("    L%d [%s] %s" % (line, why, _short(text)))
    if len(result["uncited"]) > 30:
        print("    ... and %d more" % (len(result["uncited"]) - 30))
    if result["skipped_labeled"]:
        print("  (Not flagged: %d specific sentence(s) labeled as your own arithmetic/inference/assumption,"
              " or in recommendation, gaps or what-would-change sections.)" % result["skipped_labeled"])
    if result["soft_uncited"]:
        print("  Specific sentences without their own citation in a cited paragraph: %d"
              " (make sure the paragraph's citations cover them)" % len(result["soft_uncited"]))
        for line, text, why in result["soft_uncited"][:15]:
            print("    L%d [%s] %s" % (line, why, _short(text)))
    if evidence_dir:
        print("  Cited URLs not found in any evidence card: %d" % len(result["not_in_evidence"]))
        for line, url in result["not_in_evidence"][:30]:
            print("    L%d %s" % (line, url))
        if result["not_in_evidence"]:
            print("    Confirm each was actually opened and says what's claimed, or add an evidence card.")
    else:
        print("  (No --evidence folder given: skipped the cross-check against gathered sources.)")
    if result["unresolved_refs"]:
        refs = sorted(set(r for _, r in result["unresolved_refs"]))
        print("  Reference markers with no matching source entry: %s" % ", ".join(refs[:20]))
    if result["uncited_listed"]:
        print("  Sources listed but never cited inline: %d (fine if intentional)"
              % len(result["uncited_listed"]))
    return 0


if __name__ == "__main__":
    sys.exit(main())
