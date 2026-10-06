#!/usr/bin/env python3
"""Validate and summarize the evidence cards in a research folder.

Researchers write evidence cards into notes/*.md (format: references/researching.md).
This script parses them so the lead can judge coverage without reading every card.

Usage:
  python evidence.py summary RESEARCH_DIR [--since YYYY-MM-DD] [--json]
  python evidence.py check   RESEARCH_DIR
  python evidence.py urls    RESEARCH_DIR

RESEARCH_DIR can also be a single notes file.
Standard library only; works on Windows, macOS and Linux.
"""

import argparse
import json
import re
import sys
import unicodedata
from collections import Counter, OrderedDict
from pathlib import Path
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

# ---------------------------------------------------------------- utilities

def _utf8_stdout():
    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(encoding="utf-8", errors="replace")
        except Exception:
            pass


FIELD_NAMES = ["claim", "quote", "source", "publisher", "date", "tier",
               "origin", "stance", "note", "url"]
_FIELD_ALT = "|".join(FIELD_NAMES)
FIELD_RE = re.compile(
    r"^\s*(?:[-*+]\s+)?(?:\*\*|__)?(" + _FIELD_ALT + r")(?:\*\*|__)?\s*:\s*(?:\*\*|__)?\s*(.*)$",
    re.IGNORECASE)
INLINE_FIELD_RE = re.compile(r"^\s*(?:\*\*|__)?(" + _FIELD_ALT + r")(?:\*\*|__)?\s*:\s*(.*)$",
                             re.IGNORECASE)
HEADING_RE = re.compile(r"^(#{1,6})\s+(.*?)\s*#*\s*$")
CARD_ID_RE = re.compile(r"^([A-Za-z0-9][A-Za-z0-9_.]*(?:-[A-Za-z0-9_.]+)*)\b\s*(?:[—–:|\-]+\s*(.*))?$")
MD_LINK_URL_RE = re.compile(r"\]\(\s*<?(https?://(?:[^()\s<>]|\([^()\s<>]*\))+)>?")
BARE_URL_RE = re.compile(r"https?://[^\s<>\"'\]\[`]+")
TRAILING = ".,;:!?»”’'\")>*_"
TRACKING_PARAMS = {"fbclid", "gclid", "mc_cid", "mc_eid", "ref", "ref_src", "igshid", "si"}
EXCLUDED_NAMES = {"plan.md", "draft.md", "report.md"}

MONTHS = {m: i for i, m in enumerate(
    ["jan", "feb", "mar", "apr", "may", "jun", "jul", "aug", "sep", "oct", "nov", "dec"], 1)}


def clean_url(url):
    url = url.strip()
    while url and url[-1] in TRAILING:
        if url[-1] == ")" and url.count("(") >= url.count(")"):
            break
        url = url[:-1]
    return url


def find_urls(text):
    """URLs in a text: markdown link targets first, then bare URLs, de-duplicated in order."""
    found = []
    for m in MD_LINK_URL_RE.finditer(text):
        found.append(clean_url(m.group(1)))
    stripped = MD_LINK_URL_RE.sub("](", text)
    for m in BARE_URL_RE.finditer(stripped):
        found.append(clean_url(m.group(0)))
    seen, out = set(), []
    for u in found:
        if u and u not in seen:
            seen.add(u)
            out.append(u)
    return out


def normalize_url(url):
    """Canonical form for matching the same page across notes and reports."""
    try:
        parts = urlsplit(clean_url(url))
    except ValueError:
        return url.strip().lower()
    host = (parts.hostname or "").lower()
    if host.startswith("www."):
        host = host[4:]
    if host in ("dx.doi.org",):
        host = "doi.org"
    if host == "doi.org":
        path = parts.path.lower()
    else:
        path = parts.path
    if len(path) > 1 and path.endswith("/"):
        path = path.rstrip("/")
    query = [(k, v) for k, v in parse_qsl(parts.query, keep_blank_values=True)
             if not k.lower().startswith("utm_") and k.lower() not in TRACKING_PARAMS]
    query.sort()
    return urlunsplit(("", host, path, urlencode(query), "")).lstrip("/")


def domain_of(url):
    try:
        host = (urlsplit(url).hostname or "").lower()
    except ValueError:
        return ""
    return host[4:] if host.startswith("www.") else host


def norm_text(s):
    s = unicodedata.normalize("NFKC", s or "").lower()
    s = re.sub(r"[^\w\s]", " ", s)
    return re.sub(r"\s+", " ", s).strip()


def parse_date(value):
    """Return (sortable (y, m, d) using the latest possible day, display string) or (None, reason)."""
    v = (value or "").strip()
    if not v or re.search(r"\b(undated|n\.?d\.?|unknown|none|no date)\b", v, re.I):
        return None, "undated"
    m = re.search(r"\b((?:19|20)\d{2})[-/.](\d{1,2})[-/.](\d{1,2})\b", v)
    if m:
        return (int(m.group(1)), int(m.group(2)), int(m.group(3))), m.group(0)
    m = re.search(r"\b((?:19|20)\d{2})[-/.](\d{1,2})\b", v)
    if m:
        return (int(m.group(1)), int(m.group(2)), 31), m.group(0)
    m = re.search(r"\b(\d{1,2})\s+([A-Za-z]{3,9})\.?,?\s+((?:19|20)\d{2})\b", v)
    if m and m.group(2)[:3].lower() in MONTHS:
        return (int(m.group(3)), MONTHS[m.group(2)[:3].lower()], int(m.group(1))), m.group(0)
    m = re.search(r"\b([A-Za-z]{3,9})\.?\s+(\d{1,2}),?\s+((?:19|20)\d{2})\b", v)
    if m and m.group(1)[:3].lower() in MONTHS:
        return (int(m.group(3)), MONTHS[m.group(1)[:3].lower()], int(m.group(2))), m.group(0)
    m = re.search(r"\b([A-Za-z]{3,9})\.?,?\s+((?:19|20)\d{2})\b", v)
    if m and m.group(1)[:3].lower() in MONTHS:
        return (int(m.group(2)), MONTHS[m.group(1)[:3].lower()], 31), m.group(0)
    m = re.search(r"\b((?:19|20)\d{2})\b", v)
    if m:
        return (int(m.group(1)), 12, 31), m.group(0)
    return None, "unparsed"


def parse_since(value):
    key, _ = parse_date(value)
    if key is None:
        raise SystemExit("--since must look like YYYY-MM-DD, got %r" % value)
    return key


# ------------------------------------------------------------------ parsing

def _new_card(card_id, label, path, line_no):
    return {"id": card_id, "label": label, "file": str(path), "line": line_no, "fields": OrderedDict()}


def _split_inline_fields(field, value):
    """'Publisher: X | Date: Y | Tier: 1' -> several fields."""
    out = [(field, value)]
    if "|" not in value:
        return out
    pieces = value.split("|")
    head, rest = [pieces[0]], []
    for piece in pieces[1:]:
        m = INLINE_FIELD_RE.match(piece)
        if m:
            rest.append((m.group(1).lower(), m.group(2).strip()))
        elif rest:
            k, v = rest[-1]
            rest[-1] = (k, v + " |" + piece)
        else:
            head.append(piece)
    return [(field, "|".join(head).strip())] + rest


def parse_notes_file(path):
    """Return (cards, sections) for one markdown notes file."""
    try:
        text = Path(path).read_text(encoding="utf-8", errors="replace")
    except OSError as exc:
        return [], {"error": str(exc)}
    cards = []
    sections = {"conflicts": [], "gaps": []}
    current = None
    pending_heading = None
    last_field = None
    section = None
    in_code = False
    auto_n = 0

    def finish():
        if current is None:
            return
        f = current["fields"]
        if f.get("claim") or (f.get("source") and f.get("quote")):
            cards.append(current)

    for line_no, raw in enumerate(text.splitlines(), 1):
        line = raw.rstrip("\n")
        if line.strip().startswith("```") or line.strip().startswith("~~~"):
            in_code = not in_code
            continue
        if in_code:
            continue
        hm = HEADING_RE.match(line)
        if hm:
            finish()
            current, last_field = None, None
            title = hm.group(2).strip()
            low = title.lower()
            if low.startswith("conflict"):
                section = "conflicts"
            elif low.startswith("gap"):
                section = "gaps"
            else:
                section = None
            idm = CARD_ID_RE.match(title)
            pending_heading = (idm.group(1), (idm.group(2) or "").strip(), line_no) if idm else (title, "", line_no)
            continue
        fm = FIELD_RE.match(line)
        if fm:
            field, value = fm.group(1).lower(), fm.group(2).strip()
            start_new = current is None or (field == "claim" and current["fields"].get("claim"))
            if start_new:
                finish()
                use_heading = (current is None and pending_heading is not None
                               and re.search(r"\d", pending_heading[0]))
                if use_heading:
                    cid, label, hl = pending_heading
                else:
                    auto_n += 1
                    cid, label, hl = "%s#%d" % (Path(path).stem, auto_n), "", line_no
                current = _new_card(cid, label, path, hl)
                pending_heading = None
            for f, v in _split_inline_fields(field, value):
                if f in current["fields"] and current["fields"][f]:
                    current["fields"][f] += " " + v
                else:
                    current["fields"][f] = v
                last_field = f
            continue
        stripped = line.strip()
        if current is not None and stripped and last_field in ("claim", "quote", "note", "source"):
            current["fields"][last_field] += " " + stripped
            continue
        if section and re.match(r"^\s*[-*+]\s+", line) and current is None:
            sections[section].append(re.sub(r"^\s*[-*+]\s+", "", line).strip())
    finish()
    return [_enrich(c) for c in cards], sections


def _enrich(card):
    f = card["fields"]
    src = f.get("source", "") + " " + f.get("url", "")
    urls = find_urls(src)
    card["url"] = urls[0] if urls else ""
    card["norm_url"] = normalize_url(card["url"]) if card["url"] else ""
    card["domain"] = domain_of(card["url"]) if card["url"] else ""
    quote = f.get("quote", "").strip()
    quote = quote.strip(" \t\"'“”«»‘’")
    card["quote"] = quote
    card["claim"] = f.get("claim", "").strip()
    tm = re.search(r"[1-4]", f.get("tier", ""))
    card["tier"] = int(tm.group(0)) if tm else None
    card["date_key"], card["date_str"] = parse_date(f.get("date", ""))
    stance = f.get("stance", "").strip().lower()
    if stance.startswith(("support", "for", "confirm")):
        stance = "supports"
    elif stance.startswith(("contradict", "against", "refut", "disput")):
        stance = "contradicts"
    elif stance.startswith(("context", "background", "neutral", "mixed")):
        stance = "context"
    card["stance"] = stance
    origin = f.get("origin", "").strip()
    if norm_text(origin) in ("", "self", "original", "same", "n a", "na", "none", "itself", "primary"):
        base = f.get("publisher", "") or card["domain"] or card["url"] or card["id"]
        card["origin_key"] = norm_text(base)
        card["origin_self"] = True
    else:
        card["origin_key"] = norm_text(origin)
        card["origin_self"] = False
    m = re.match(r"^(.+?)-E\d+[A-Za-z]?$", card["id"], re.I)
    if m and "#" not in card["id"]:
        card["subq"] = m.group(1).upper()
    else:
        stem = Path(card["file"]).stem
        sm = re.match(r"^([A-Za-z]+\d+)", stem)
        card["subq"] = sm.group(1).upper() if sm else stem
    return card


def card_problems(card):
    """(errors, warnings) for one card."""
    errors, warnings = [], []
    if not card["claim"]:
        errors.append("missing Claim")
    if not card["quote"]:
        errors.append("missing Quote")
    elif len(card["quote"]) < 15:
        warnings.append("very short Quote")
    if not card["url"]:
        if card["fields"].get("source", "").strip():
            warnings.append("Source has no URL (offline or internal source?)")
        else:
            errors.append("missing Source")
    if card["tier"] is None:
        warnings.append("missing or invalid Tier (use 1-4)")
    if card["date_key"] is None:
        warnings.append("undated" if card["date_str"] == "undated" else "unparsed Date")
    if card["stance"] not in ("supports", "contradicts", "context"):
        warnings.append("Stance should be supports/contradicts/context")
    return errors, warnings


def collect_files(target):
    target = Path(target)
    if target.is_file():
        return [target]
    files = []
    for p in sorted(target.rglob("*.md")):
        rel = p.relative_to(target).parts
        if p.name.lower() in EXCLUDED_NAMES or p.name.lower().startswith(("draft", "report")):
            continue
        if "checks" in rel[:-1] and not p.name.lower().startswith("red-team"):
            continue
        files.append(p)
    return files


def unify_origins(cards):
    """Map 'Origin: Cambridge Judge Business School 2013 report' onto the publisher key of the
    card that *is* that origin, so re-reports don't count as independent sources."""
    publishers = sorted({c["origin_key"] for c in cards if c["origin_self"] and len(c["origin_key"]) >= 4},
                        key=len, reverse=True)
    for c in cards:
        if c["origin_self"]:
            continue
        for p in publishers:
            if p in c["origin_key"] or c["origin_key"] in p:
                c["origin_key"] = p
                break


def load_evidence(target):
    """Parse every notes file under target. Returns (cards, per_file)."""
    cards, per_file = [], OrderedDict()
    for path in collect_files(target):
        file_cards, sections = parse_notes_file(path)
        per_file[str(path)] = {"cards": len(file_cards), "sections": sections}
        cards.extend(file_cards)
    unify_origins(cards)
    return cards, per_file


def evidence_url_index(cards):
    index = {}
    for c in cards:
        if c["norm_url"]:
            index.setdefault(c["norm_url"], []).append(c)
    return index


# ------------------------------------------------------------------ reports

def build_summary(cards, per_file, since=None):
    groups = OrderedDict()
    for c in cards:
        groups.setdefault(c["subq"], []).append(c)
    rows, warnings = [], []
    for sq, all_cs in groups.items():
        cs = [c for c in all_cs if not card_problems(c)[0]]   # cards with format errors don't count
        tiers = Counter(c["tier"] for c in cs)
        origins = {c["origin_key"] for c in cs}
        dated = sorted((c["date_key"], c["date_str"]) for c in cs if c["date_key"])
        stale = [c for c in cs if since and c["date_key"] and c["date_key"] < since]
        domains = Counter(c["domain"] for c in cs if c["domain"])
        row = OrderedDict([
            ("subq", sq),
            ("cards", len(cs)),
            ("bad", len(all_cs) - len(cs)),
            ("origins", len(origins)),
            ("t12", tiers.get(1, 0) + tiers.get(2, 0)),
            ("t34", tiers.get(3, 0) + tiers.get(4, 0)),
            ("unrated", tiers.get(None, 0)),
            ("contradicts", sum(1 for c in cs if c["stance"] == "contradicts")),
            ("undated", sum(1 for c in cs if c["date_key"] is None)),
            ("stale", len(stale)),
            ("oldest", dated[0][1] if dated else ""),
            ("newest", dated[-1][1] if dated else ""),
        ])
        rows.append(row)
        if row["t12"] == 0:
            warnings.append("%s: no tier-1 or tier-2 evidence; conclusions here rest on weak sources" % sq)
        if row["origins"] <= 1 and tiers.get(1, 0) == 0 and sq not in ("R",):
            warnings.append("%s: only %d independent origin(s) and no tier-1 source; corroborate before relying on it"
                            % (sq, row["origins"]))
        if len(cs) >= 5 and domains:
            dom, n = domains.most_common(1)[0]
            dom_tier1 = all(c["tier"] == 1 for c in cs if c["domain"] == dom)
            if n / float(len(cs)) > 0.5 and not dom_tier1:
                warnings.append("%s: %d of %d cards come from one domain (%s)" % (sq, n, len(cs), dom))
        if stale:
            warnings.append("%s: %d card(s) older than --since (%s)"
                            % (sq, len(stale), ", ".join(c["id"] for c in stale[:8])))
    for f, info in per_file.items():
        if info["cards"] == 0:
            warnings.append("%s: no evidence cards parsed; check the card format" % f)
    problems = []
    for c in cards:
        errs, warns = card_problems(c)
        if errs or warns:
            problems.append({"id": c["id"], "file": c["file"], "line": c["line"],
                             "errors": errs, "warnings": warns})
    usable = [c for c in cards if not card_problems(c)[0]]
    totals = OrderedDict([
        ("cards", len(cards)),
        ("files", len(per_file)),
        ("unique_sources", len({c["norm_url"] for c in usable if c["norm_url"]})),
        ("independent_origins", len({c["origin_key"] for c in usable})),
        ("stances", dict(Counter(c["stance"] or "missing" for c in cards))),
        ("tiers", {("T%s" % k if k else "unrated"): v for k, v in sorted(
            Counter(c["tier"] for c in cards).items(), key=lambda kv: (kv[0] is None, kv[0] or 0))}),
    ])
    notes = OrderedDict()
    for f, info in per_file.items():
        sec = info["sections"]
        if sec.get("conflicts") or sec.get("gaps"):
            notes[f] = {"conflicts": sec.get("conflicts", []), "gaps": sec.get("gaps", [])}
    return {"totals": totals, "subquestions": rows, "warnings": warnings,
            "problems": problems, "notes": notes}


def _short(s, n=160):
    s = re.sub(r"\s+", " ", s or "").strip()
    return s if len(s) <= n else s[: n - 1] + "…"


def print_summary(summary, target):
    t = summary["totals"]
    print("Evidence summary: %s" % target)
    print("Cards: %d in %d file(s) | unique sources: %d | independent origins: %d"
          % (t["cards"], t["files"], t["unique_sources"], t["independent_origins"]))
    print("Stances: %s" % ", ".join("%s %d" % kv for kv in t["stances"].items()))
    print("Tiers: %s" % ", ".join("%s %d" % kv for kv in t["tiers"].items()))
    print()
    header = ("Sub-q", "Cards", "Bad", "Origins", "T1/T2", "T3/T4", "Contra", "Undated", "Stale", "Dates")
    print("%-8s %5s %4s %7s %5s %5s %6s %7s %5s  %s" % header)
    for r in summary["subquestions"]:
        dates = (r["oldest"] + " .. " + r["newest"]) if r["oldest"] else "-"
        print("%-8s %5d %4d %7d %5d %5d %6d %7d %5d  %s" % (
            r["subq"][:8], r["cards"], r["bad"], r["origins"], r["t12"], r["t34"], r["contradicts"],
            r["undated"], r["stale"], dates))
    print("(Cards = usable cards; Bad = cards with format errors, not counted. Origins = independent origins.)")
    if summary["warnings"]:
        print("\nWarnings:")
        for w in summary["warnings"]:
            print("  - " + w)
    errs = [p for p in summary["problems"] if p["errors"]]
    if errs:
        print("\nCards with format errors (fix them or don't rely on them):")
        for p in errs[:40]:
            print("  - %s (%s:%d): %s" % (p["id"], Path(p["file"]).name, p["line"], "; ".join(p["errors"])))
        if len(errs) > 40:
            print("  ... and %d more" % (len(errs) - 40))
    warn_cards = [p for p in summary["problems"] if not p["errors"] and p["warnings"]]
    if warn_cards:
        print("\nCards with minor issues: %d (run 'check' for the list)" % len(warn_cards))
    if summary["notes"]:
        print("\nConflicts and gaps reported by researchers:")
        for f, sec in summary["notes"].items():
            name = Path(f).name
            for c in sec["conflicts"][:5]:
                print("  - [%s] conflict: %s" % (name, _short(c)))
            for g in sec["gaps"][:5]:
                print("  - [%s] gap: %s" % (name, _short(g)))


# --------------------------------------------------------------------- main

def main(argv=None):
    _utf8_stdout()
    ap = argparse.ArgumentParser(description="Validate and summarize evidence cards.")
    sub = ap.add_subparsers(dest="cmd")
    s = sub.add_parser("summary", help="coverage summary per sub-question")
    s.add_argument("target")
    s.add_argument("--since", help="flag cards dated before this (YYYY-MM-DD)")
    s.add_argument("--json", action="store_true", help="machine-readable output")
    c = sub.add_parser("check", help="list every card with format problems")
    c.add_argument("target")
    u = sub.add_parser("urls", help="list gathered source URLs with their card IDs")
    u.add_argument("target")
    args = ap.parse_args(argv)
    if not args.cmd:
        ap.print_help()
        return 2
    target = Path(args.target)
    if not target.exists():
        print("Not found: %s" % target)
        return 2
    cards, per_file = load_evidence(target)

    if args.cmd == "summary":
        since = parse_since(args.since) if args.since else None
        summary = build_summary(cards, per_file, since)
        if args.json:
            print(json.dumps(summary, indent=2, ensure_ascii=False, default=str))
        else:
            print_summary(summary, target)
        return 0

    if args.cmd == "check":
        bad = 0
        for card in cards:
            errs, warns = card_problems(card)
            if errs or warns:
                bad += 1 if errs else 0
                print("%s (%s:%d)" % (card["id"], Path(card["file"]).name, card["line"]))
                for e in errs:
                    print("   ERROR   " + e)
                for w in warns:
                    print("   warning " + w)
        empty = [f for f, i in per_file.items() if i["cards"] == 0]
        for f in empty:
            print("%s: no evidence cards parsed" % f)
        print("\n%d card(s) checked, %d with errors, %d file(s) without cards."
              % (len(cards), bad, len(empty)))
        return 1 if bad else 0

    if args.cmd == "urls":
        index = OrderedDict()
        for card in cards:
            if card["url"]:
                index.setdefault(card["url"], []).append(card["id"])
        for url, ids in index.items():
            print("%s\t%s" % (url, ", ".join(ids)))
        print("\n%d unique URL(s)." % len(index), file=sys.stderr)
        return 0
    return 2


if __name__ == "__main__":
    sys.exit(main())
