#!/usr/bin/env python3
"""Check that a report's links resolve and that evidence quotes appear on the cited pages.

Needs internet access from the shell. That's usually available in Claude Code on a
personal machine and often blocked in sandboxes; the script detects a blocked network
and says so instead of reporting every link as broken.

Usage:
  python check_links.py REPORT.md [--evidence RESEARCH_DIR] [--out LINKS.md]
                        [--timeout 20] [--workers 6]

Statuses:
  OK            page loaded (and the quotes from evidence cards were found, if any)
  QUOTE?        page loaded but a researcher's quote was only partly or not found
  NOT FOUND     404/410; dead link, or a site that refuses scripts (confirm with a fetch tool)
  HOMEPAGE      redirected to the site's front page (moved or removed?)
  SOFT 404      loads, but the page says it doesn't exist
  BLOCKED       the site refused automated access (401/403/429...); check with a fetch tool or browser
  SERVER ERROR  5xx
  DNS FAIL      the domain doesn't resolve (often an invented or mistyped URL)
  NO CONNECTION timeout, TLS or connection error
Standard library only; works on Windows, macOS and Linux.
"""

import argparse
import concurrent.futures as cf
import gzip
import re
import socket
import ssl
import sys
import unicodedata
import zlib
from html.parser import HTMLParser
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import urlsplit
from urllib.request import Request, urlopen

sys.path.insert(0, str(Path(__file__).resolve().parent))
from evidence import _utf8_stdout, evidence_url_index, find_urls, load_evidence, normalize_url  # noqa: E402

UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) "
      "Chrome/126.0 Safari/537.36")
MAX_BYTES = 4 * 1024 * 1024
SOFT_404_RE = re.compile(r"(page not found|404 not found|page (?:does not|doesn't) exist|"
                         r"no longer available|could not be found|\b404\b.{0,40}\berror\b)", re.I)


class _TextExtractor(HTMLParser):
    SKIP = {"script", "style", "noscript", "svg", "template", "head"}

    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.parts, self.skip_depth, self.title, self._in_title = [], 0, "", False

    def handle_starttag(self, tag, attrs):
        if tag == "title":
            self._in_title = True
        if tag in self.SKIP:
            self.skip_depth += 1

    def handle_endtag(self, tag):
        if tag == "title":
            self._in_title = False
        if tag in self.SKIP and self.skip_depth:
            self.skip_depth -= 1

    def handle_data(self, data):
        if self._in_title:
            self.title += data
        elif not self.skip_depth:
            self.parts.append(data)


def html_to_text(raw):
    p = _TextExtractor()
    try:
        p.feed(raw)
        p.close()
    except Exception:
        pass
    return re.sub(r"\s+", " ", " ".join(p.parts)).strip(), re.sub(r"\s+", " ", p.title).strip()


def norm_words(s):
    s = unicodedata.normalize("NFKC", s).lower()
    s = (s.replace("’", "'").replace("‘", "'").replace("“", '"')
         .replace("”", '"').replace("–", "-").replace("—", "-"))
    s = re.sub(r"[^\w\s]", " ", s)
    return s.split()


def quote_match(quote, page_words, page_text_norm):
    """Return (status, score) for one quote: FOUND / PARTIAL / NOT FOUND / SHORT."""
    q = re.sub(r"\[[^\]]*\]", " ", quote)               # drop bracketed translations/insertions
    fragments = [f for f in re.split(r"\.\.\.|…", q) if len(norm_words(f)) >= 3]
    if not fragments:
        return "SHORT", 0.0
    scores = []
    for frag in fragments:
        words = norm_words(frag)
        if " ".join(words) in page_text_norm:
            scores.append(1.0)
            continue
        n = 4 if len(words) >= 8 else 2
        grams = [tuple(words[i:i + n]) for i in range(len(words) - n + 1)]
        if not grams:
            scores.append(0.0)
            continue
        hits = sum(1 for g in grams if g in page_words.get(n, set()))
        scores.append(hits / float(len(grams)))
    score = sum(scores) / len(scores)
    if score >= 0.85:
        return "FOUND", score
    if score >= 0.5:
        return "PARTIAL", score
    return "NOT FOUND", score


def ngram_sets(words):
    return {n: set(tuple(words[i:i + n]) for i in range(len(words) - n + 1)) for n in (2, 4)}


def fetch(url, timeout):
    req = Request(url, headers={
        "User-Agent": UA,
        "Accept": "text/html,application/xhtml+xml,application/pdf;q=0.9,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.9,ar;q=0.8",
        "Accept-Encoding": "gzip, deflate",
    })
    ctx = ssl.create_default_context()
    with urlopen(req, timeout=timeout, context=ctx) as resp:
        status = getattr(resp, "status", 200)
        final_url = resp.geturl()
        ctype = resp.headers.get("Content-Type", "")
        body = resp.read(MAX_BYTES)
        enc = (resp.headers.get("Content-Encoding") or "").lower()
    if enc == "gzip":
        try:
            body = gzip.decompress(body)
        except Exception:
            pass
    elif enc == "deflate":
        try:
            body = zlib.decompress(body)
        except Exception:
            try:
                body = zlib.decompress(body, -zlib.MAX_WBITS)
            except Exception:
                pass
    return status, final_url, ctype, body


def decode(body, ctype):
    m = re.search(r"charset=([\w-]+)", ctype or "", re.I)
    if not m:
        m = re.search(rb"<meta[^>]+charset=[\"']?([\w-]+)", body[:4096], re.I)
        charset = m.group(1).decode("ascii", "ignore") if m else "utf-8"
    else:
        charset = m.group(1)
    try:
        return body.decode(charset, errors="replace")
    except LookupError:
        return body.decode("utf-8", errors="replace")


def check_one(url, quotes, timeout):
    result = {"url": url, "status": "", "detail": "", "quotes": []}
    try:
        code, final_url, ctype, body = fetch(url, timeout)
    except HTTPError as e:
        code = e.code
        if code in (404, 410):
            result.update(status="NOT FOUND", detail="HTTP %d" % code)
        elif code in (401, 402, 403, 405, 406, 429, 451, 999):
            result.update(status="BLOCKED", detail="HTTP %d; check with a fetch tool or browser" % code)
        elif code >= 500:
            result.update(status="SERVER ERROR", detail="HTTP %d" % code)
        else:
            result.update(status="HTTP %d" % code, detail="")
        return result
    except (URLError, socket.timeout, ssl.SSLError, ConnectionError, OSError, ValueError) as e:
        reason = str(getattr(e, "reason", e))
        if re.search(r"getaddrinfo|name or service not known|nodename nor servname|"
                     r"no address associated|name resolution", reason, re.I):
            result.update(status="DNS FAIL",
                          detail="domain doesn't resolve; invented or mistyped URL? (%s)" % reason[:80])
        else:
            result.update(status="NO CONNECTION", detail=reason[:160])
        return result
    o, f = urlsplit(url), urlsplit(final_url)
    if (o.path not in ("", "/") and f.path in ("", "/") and not f.query):
        result.update(status="HOMEPAGE", detail="redirected to %s" % final_url)
        return result
    is_pdf = "pdf" in ctype.lower() or body[:5] == b"%PDF-"
    if is_pdf:
        result.update(status="OK", detail="PDF; quotes not checked (open it to confirm)")
        result["quotes"] = [("NOT CHECKED", 0.0, q) for q in quotes]
        return result
    text, title = html_to_text(decode(body, ctype)) if "html" in ctype.lower() or b"<html" in body[:2000].lower() \
        else (re.sub(r"\s+", " ", decode(body, ctype)), "")
    head = (title + " " + text[:600])
    if SOFT_404_RE.search(head) and len(text) < 3000:
        result.update(status="SOFT 404", detail="page says: %s" % (title or text[:80]))
        return result
    result["status"] = "OK"
    if final_url != url:
        result["detail"] = "redirected to %s" % final_url
    if quotes:
        if len(text) < 300:
            result["quotes"] = [("NOT CHECKED", 0.0, q) for q in quotes]
            result["detail"] = (result["detail"] + "; " if result["detail"] else "") + \
                "little text on page (JavaScript-rendered or blocked?)"
            return result
        words = norm_words(text)
        grams = ngram_sets(words)
        joined = " ".join(words)
        for q in quotes:
            st, score = quote_match(q, grams, joined)
            result["quotes"].append((st, score, q))
        if any(st in ("PARTIAL", "NOT FOUND") for st, _, _ in result["quotes"]):
            result["status"] = "QUOTE?"
    return result


def network_blocked(results):
    if not results:
        return False
    conn = [r for r in results if r["status"] in ("NO CONNECTION", "DNS FAIL")]
    proxyish = [r for r in results if r["status"] == "BLOCKED" and "403" in r["detail"]]
    if len(conn) == len(results):
        return True
    if len(results) >= 3 and (len(conn) + len(proxyish)) / float(len(results)) >= 0.9 and conn:
        return True
    tunnel = [r for r in conn if re.search(r"tunnel|proxy", r["detail"], re.I)]
    return bool(tunnel) and len(tunnel) >= max(1, len(results) // 2)


def main(argv=None):
    _utf8_stdout()
    ap = argparse.ArgumentParser(description="Check links and quotes in a research report.")
    ap.add_argument("report")
    ap.add_argument("--evidence", help="research folder with evidence cards (enables quote checks)")
    ap.add_argument("--out", help="markdown file for the results")
    ap.add_argument("--timeout", type=float, default=20.0)
    ap.add_argument("--workers", type=int, default=6)
    args = ap.parse_args(argv)
    report = Path(args.report)
    if not report.is_file():
        print("Not found: %s" % report)
        return 2
    text = report.read_text(encoding="utf-8", errors="replace")
    text = re.sub(r"```.*?```", " ", text, flags=re.S)
    urls = find_urls(text)
    if not urls:
        print("No links found in %s." % report)
        return 0
    quotes_by_url = {}
    if args.evidence and Path(args.evidence).exists():
        cards, _ = load_evidence(args.evidence)
        index = evidence_url_index(cards)
        for u in urls:
            qs = [c["quote"] for c in index.get(normalize_url(u), []) if c.get("quote")]
            quotes_by_url[u] = qs[:4]

    # Probe with the first link before checking everything (saves time when offline).
    first = check_one(urls[0], quotes_by_url.get(urls[0], []), min(args.timeout, 10))
    results = [first]
    offline = ("NO CONNECTION", "DNS FAIL")
    if first["status"] in offline and len(urls) > 1:
        second = check_one(urls[1], quotes_by_url.get(urls[1], []), min(args.timeout, 10))
        results.append(second)
        control = check_one("https://example.com/", [], 10) if second["status"] in offline else None
        if control is not None and control["status"] in offline:
            print("NETWORK BLOCKED: this shell can't reach the internet (%s)." % first["detail"])
            print("Skip this check here; the verifier's own fetches cover link and quote checking.")
            return 0
    rest = urls[len(results):]
    with cf.ThreadPoolExecutor(max_workers=max(1, args.workers)) as pool:
        futures = [pool.submit(check_one, u, quotes_by_url.get(u, []), args.timeout) for u in rest]
        results += [f.result() for f in futures]
    order = {u: i for i, u in enumerate(urls)}
    results.sort(key=lambda r: order.get(r["url"], 0))

    if network_blocked(results):
        print("NETWORK BLOCKED: every request failed at the connection level (e.g. %s)."
              % results[0]["detail"])
        print("Skip this check here; the verifier's own fetches cover link and quote checking.")
        return 0

    lines = ["# Link and quote check", "", "Report: %s" % report, "",
             "| # | Status | URL | Detail |", "|---|---|---|---|"]
    counts = {}
    for i, r in enumerate(results, 1):
        counts[r["status"]] = counts.get(r["status"], 0) + 1
        lines.append("| %d | %s | %s | %s |" % (i, r["status"], r["url"], r["detail"].replace("|", "/")))
    problem_quotes = []
    for r in results:
        for st, score, q in r["quotes"]:
            if st in ("PARTIAL", "NOT FOUND"):
                problem_quotes.append((r["url"], st, score, q))
    if problem_quotes:
        lines += ["", "## Quotes not found verbatim on the page", ""]
        for url, st, score, q in problem_quotes:
            qq = re.sub(r"\s+", " ", q)
            lines.append("- %s (match %.0f%%) %s\n  \"%s\"" % (st, score * 100, url, qq[:300]))
    out = Path(args.out) if args.out else (
        Path(args.evidence) / "checks" / "links.md" if args.evidence and Path(args.evidence).is_dir()
        else report.parent / "checks" / "links.md")
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text("\n".join(lines) + "\n", encoding="utf-8")

    print("Checked %d link(s): %s" % (len(results), ", ".join("%s %d" % kv for kv in sorted(counts.items()))))
    for i, r in enumerate(results, 1):
        if r["status"] != "OK":
            print("  %-13s %s  %s" % (r["status"], r["url"], r["detail"]))
    if problem_quotes:
        print("  Quotes not found verbatim: %d (a paraphrased 'quote', a page built by JavaScript, or the wrong page; have the verifier look)"
              % len(problem_quotes))
    if any(r["status"] in ("NOT FOUND", "BLOCKED") for r in results):
        print("  Some sites answer scripts with 403 or 404 but serve browsers and fetch tools;"
              " re-open a NOT FOUND or BLOCKED page with your fetch tool before dropping it.")
    print("Details written to %s" % out)
    return 0


if __name__ == "__main__":
    sys.exit(main())
