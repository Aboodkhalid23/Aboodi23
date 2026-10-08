#!/usr/bin/env python3
"""بحث عميق سريع: يدوّر على موضوع وحد بعدة مصادر مجانية بنفس الوقت (بدون مفاتيح).

المصادر:
  exa      محرك بحث ذكي (خادم Exa العام، مجاني بحدود)
  gdelt    أخبار العالم بأكثر من 65 لغة (GDELT)، نطلب الإنگليزي والعربي افتراضياً
  gnews    Google News (قوائم RSS) بالإنگليزي والعربي
  wiki     ويكيبيديا العربية والإنگليزية
  hn       Hacker News (نقاشات التقنية)
  reddit   Reddit (غالباً محجوب من الحاوية، يتجاوزه السكربت بهدوء)
  edgar    البحث بنص ملفات الشركات الأمريكية الرسمية (SEC EDGAR)
  court    أحكام وقضايا المحاكم الأمريكية (CourtListener)
  arxiv    أبحاث علمية (arXiv)
  + فحص الأرشيف: لأول N روابط، يشوف إذا عدها نسخة محفوظة بـ Wayback Machine

أمثلة:
  python3 scripts/deep-search.py "Hugging Face breach AI agents"
  python3 scripts/deep-search.py "Theranos" --sources gdelt,wiki,edgar,court --limit 8
  python3 scripts/deep-search.py "Nokia collapse" --langs english,arabic,french --json > out.json

ملاحظات:
  - يستخدم مكتبة requests إذا موجودة، وإلا مكتبات بايثون الأساسية بس.
  - يحترم البروكسي وشهادة الحاوية تلقائياً (HTTPS_PROXY و REQUESTS_CA_BUNDLE / SSL_CERT_FILE).
  - كل مصدر يفشل ينطبع سببه بسطر قصير، والباقي يكمل عادي.
"""
from __future__ import annotations

import argparse
import concurrent.futures as cf
import html
import json
import os
import re
import sys
import time
import urllib.parse as up
import xml.etree.ElementTree as ET
from email.utils import parsedate_to_datetime

try:
    import requests  # type: ignore
except ImportError:  # pragma: no cover
    requests = None
    import ssl
    import urllib.request

UA = os.environ.get(
    "DEEP_SEARCH_UA",
    "Aboodi23-deep-search/1.0 (research script; +https://github.com/) python",
)
TIMEOUT = 30


class Fail(Exception):
    pass


def http_get(url, params=None, headers=None, retries=3, backoff=4.0, as_json=True):
    """GET مع إعادة محاولة عند 429/5xx. يرجّع JSON أو نص."""
    if params:
        url = url + ("&" if "?" in url else "?") + up.urlencode(params)
    h = {"User-Agent": UA, "Accept": "*/*"}
    h.update(headers or {})
    last = ""
    for attempt in range(retries):
        try:
            if requests:
                r = requests.get(url, headers=h, timeout=TIMEOUT)
                code, text = r.status_code, r.content.decode("utf-8", "replace")
            else:
                ctx = ssl.create_default_context(
                    cafile=os.environ.get("SSL_CERT_FILE") or os.environ.get("REQUESTS_CA_BUNDLE"))
                req = urllib.request.Request(url, headers=h)
                try:
                    with urllib.request.urlopen(req, timeout=TIMEOUT, context=ctx) as resp:
                        code, text = resp.status, resp.read().decode("utf-8", "replace")
                except urllib.error.HTTPError as e:  # type: ignore[attr-defined]
                    code, text = e.code, e.read().decode("utf-8", "replace")
        except Exception as e:  # شبكة
            last = f"network: {str(e)[:80]}"
            time.sleep(backoff * (attempt + 1))
            continue
        if code == 429 or code >= 500:
            last = f"HTTP {code}"
            time.sleep(backoff * (attempt + 1))
            continue
        if code >= 400:
            raise Fail(f"HTTP {code}")
        if not as_json:
            return text
        try:
            return json.loads(text)
        except ValueError:
            raise Fail("not JSON (probably blocked page)")
    raise Fail(last or "failed")


def item(source, date, title, url, extra=""):
    return {
        "source": source,
        "date": (date or "")[:10],
        "title": re.sub(r"\s+", " ", html.unescape(re.sub(r"<[^>]+>", "", title or ""))).strip(),
        "url": url or "",
        "extra": extra,
    }


def parse_xml(text):
    """قارئ XML آمن: نرفض أي ملف بيه تعريفات كيانات (حماية من هجمات XML)."""
    if "<!ENTITY" in text or "<!DOCTYPE" in text:
        raise Fail("XML with DOCTYPE/ENTITY refused")
    return ET.fromstring(text)


def shrink(query, quote=False):
    """إذا ماكو نتائج، نشيل آخر كلمة ونعيد (لحد كلمتين).
    quote=True: كل محاولة تنحط بين علامات تنصيص (عبارة حرفية) حتى ما تطلع نتائج غلط."""
    words = query.split()
    out = [query]
    while len(words) > 2:
        words = words[:-1]
        out.append(" ".join(words))
    return [f'"{x}"' for x in out] if quote else out


# ---------------------------------------------------------------- المصادر
def src_exa(q, limit, **_):
    body = {"jsonrpc": "2.0", "id": 1, "method": "tools/call",
            "params": {"name": "web_search_exa", "arguments": {"query": q, "numResults": limit}}}
    hdr = {"Content-Type": "application/json", "Accept": "application/json, text/event-stream",
           "User-Agent": UA}
    url = "https://mcp.exa.ai/mcp"
    if requests:
        r = requests.post(url, json=body, headers=hdr, timeout=60)
        if r.status_code >= 400:
            raise Fail(f"HTTP {r.status_code}")
        raw = r.content.decode("utf-8", "replace")
    else:
        req = urllib.request.Request(url, data=json.dumps(body).encode(), headers=hdr)
        ctx = ssl.create_default_context(cafile=os.environ.get("SSL_CERT_FILE"))
        raw = urllib.request.urlopen(req, timeout=60, context=ctx).read().decode()
    m = re.search(r"^data: (.*)$", raw, re.M)
    data = json.loads(m.group(1) if m else raw)
    if "error" in data:
        raise Fail(str(data["error"].get("message", "error"))[:80])
    text = data["result"]["content"][0]["text"]
    out = []
    for block in re.split(r"\n(?=Title: )", text):
        t = re.search(r"Title: (.*)", block)
        u = re.search(r"URL: (\S+)", block)
        d = re.search(r"Published: (\S+)", block)
        if u:
            out.append(item("exa", d.group(1) if d else "", t.group(1) if t else u.group(1), u.group(1)))
    return out[:limit]


def src_gdelt(q, limit, langs=("english", "arabic"), timespan="6m", **_):
    # GDELT يرفض الكلمات الأقصر من 3 حروف، ويسمح بطلب واحد كل 5 ثواني
    words = [w for w in q.split() if len(w) >= 3]
    core = " ".join(words) if words else q
    out, notes = [], []
    for i, lang in enumerate(langs):
        if i:
            time.sleep(6)
        got = []
        for qq in shrink(core)[:2]:
            data = http_get("https://api.gdeltproject.org/api/v2/doc/doc", {
                "query": f"{qq} sourcelang:{lang}", "mode": "artlist", "format": "json",
                "maxrecords": limit, "timespan": timespan, "sort": "hybridrel"},
                retries=4, backoff=8)
            got = data.get("articles", []) if isinstance(data, dict) else []
            if got:
                break
            time.sleep(6)
        if not got:
            notes.append(lang)
        for a in got[:limit]:
            sd = a.get("seendate", "")
            date = f"{sd[:4]}-{sd[4:6]}-{sd[6:8]}" if len(sd) >= 8 else ""
            out.append(item(f"gdelt:{lang[:2]}", date, a.get("title"), a.get("url"),
                            a.get("domain", "")))
    return out


def src_gnews(q, limit, **_):
    out = []
    for hl, gl, ceid in (("en-US", "US", "US:en"), ("ar", "IQ", "IQ:ar")):
        text = http_get("https://news.google.com/rss/search",
                        {"q": q, "hl": hl, "gl": gl, "ceid": ceid}, as_json=False)
        root = parse_xml(text)
        for it in root.iter("item"):
            try:
                d = parsedate_to_datetime(it.findtext("pubDate", "")).strftime("%Y-%m-%d")
            except Exception:
                d = ""
            src = it.find("source")
            out.append(item(f"gnews:{hl[:2]}", d, it.findtext("title"), it.findtext("link"),
                            src.text if src is not None else ""))
            if sum(1 for x in out if x["source"] == f"gnews:{hl[:2]}") >= limit:
                break
    return out


def src_wiki(q, limit, **_):
    out = []
    for lang in ("ar", "en"):
        for qq in shrink(q):
            data = http_get(f"https://{lang}.wikipedia.org/w/rest.php/v1/search/page",
                            {"q": qq, "limit": limit})
            pages = data.get("pages", [])
            if pages:
                break
        for p in pages:
            out.append(item(f"wiki:{lang}", "", p.get("title"),
                            f"https://{lang}.wikipedia.org/wiki/{up.quote(p.get('key', ''))}",
                            (p.get("description") or "")[:60]))
    return out


def src_hn(q, limit, **_):
    for qq in shrink(q):
        data = http_get("https://hn.algolia.com/api/v1/search",
                        {"query": qq, "tags": "story", "hitsPerPage": limit})
        hits = data.get("hits", [])
        if hits:
            break
    return [item("hn", h.get("created_at"), h.get("title"),
                 h.get("url") or f"https://news.ycombinator.com/item?id={h.get('objectID')}",
                 f"{h.get('points', 0)} pts / {h.get('num_comments', 0)} comments") for h in hits]


def src_reddit(q, limit, **_):
    data = http_get("https://www.reddit.com/search.json",
                    {"q": q, "limit": limit, "sort": "relevance", "t": "year"}, retries=1)
    out = []
    for c in data.get("data", {}).get("children", []):
        d = c.get("data", {})
        out.append(item("reddit", time.strftime("%Y-%m-%d", time.gmtime(d.get("created_utc", 0))),
                        d.get("title"), "https://www.reddit.com" + d.get("permalink", ""),
                        f"r/{d.get('subreddit', '')}"))
    return out


def src_edgar(q, limit, **_):
    hits = []
    # SEC تطلب هوية فيها وسيلة تواصل؛ غيّرها بمتغير SEC_UA إذا تحب
    sec_ua = os.environ.get("SEC_UA", "Aboodi23 research-script research@example.org")
    for qq in shrink(q, quote=True):
        data = http_get("https://efts.sec.gov/LATEST/search-index", {"q": qq},
                        headers={"User-Agent": sec_ua})
        hits = data.get("hits", {}).get("hits", [])
        if hits:
            break
    out = []
    for h in hits[:limit]:
        s = h.get("_source", {})
        adsh, _, fname = h.get("_id", "").partition(":")
        cik = (s.get("ciks") or [""])[0].lstrip("0")
        url = (f"https://www.sec.gov/Archives/edgar/data/{cik}/{adsh.replace('-', '')}/{fname}"
               if cik and adsh else "")
        name = (s.get("display_names") or ["?"])[0]
        out.append(item("edgar", s.get("file_date"), f"{s.get('form', '')} — {name}", url))
    return out


def src_court(q, limit, **_):
    res = []
    for qq in shrink(q, quote=True):
        data = http_get("https://www.courtlistener.com/api/rest/v4/search/",
                        {"q": qq, "type": "o", "order_by": "score desc"})
        res = data.get("results", [])
        if res:
            break
    return [item("court", r.get("dateFiled"), r.get("caseName"),
                 "https://www.courtlistener.com" + r.get("absolute_url", ""),
                 r.get("court", "")) for r in res[:limit]]


def src_arxiv(q, limit, **_):
    ns = {"a": "http://www.w3.org/2005/Atom"}
    for qq in shrink(q):
        terms = " AND ".join(f"all:{w}" for w in qq.split())
        text = http_get("https://export.arxiv.org/api/query",
                        {"search_query": terms, "max_results": limit,
                         "sortBy": "relevance"}, as_json=False)
        entries = parse_xml(text).findall("a:entry", ns)
        if entries:
            break
    return [item("arxiv", e.findtext("a:published", "", ns), e.findtext("a:title", "", ns),
                 e.findtext("a:id", "", ns)) for e in entries]


SOURCES = {"exa": src_exa, "gdelt": src_gdelt, "gnews": src_gnews, "wiki": src_wiki,
           "hn": src_hn, "reddit": src_reddit, "edgar": src_edgar, "court": src_court,
           "arxiv": src_arxiv}


def wayback_check(url):
    try:
        data = http_get("https://archive.org/wayback/available", {"url": url}, retries=2)
        snap = data.get("archived_snapshots", {}).get("closest", {})
        return snap.get("url", "")
    except Fail:
        return ""


def main():
    ap = argparse.ArgumentParser(description="Deep search across free, keyless sources.")
    ap.add_argument("query")
    ap.add_argument("--sources", default=",".join(SOURCES), help="comma list: " + ",".join(SOURCES))
    ap.add_argument("--limit", type=int, default=5, help="results per source (per language)")
    ap.add_argument("--langs", default="english,arabic", help="GDELT source languages")
    ap.add_argument("--timespan", default="6m", help="GDELT window, e.g. 1w, 3m, 12m")
    ap.add_argument("--archive-check", type=int, default=5,
                    help="check Wayback snapshots for the first N news/web URLs (0 = off)")
    ap.add_argument("--json", action="store_true", help="print JSON instead of a table")
    a = ap.parse_args()

    chosen = [s.strip() for s in a.sources.split(",") if s.strip() in SOURCES]
    kw = {"langs": [x.strip() for x in a.langs.split(",") if x.strip()], "timespan": a.timespan}
    results, status = [], {}
    t0 = time.time()
    with cf.ThreadPoolExecutor(max_workers=len(chosen) or 1) as ex:
        futs = {ex.submit(SOURCES[s], a.query, a.limit, **kw): s for s in chosen}
        for f in cf.as_completed(futs):
            s = futs[f]
            try:
                got = f.result()
                results += got
                status[s] = f"{len(got)} results"
            except Exception as e:
                status[s] = f"FAILED ({str(e)[:70]})"

    # إزالة التكرار حسب الرابط
    seen, merged = set(), []
    for r in results:
        key = r["url"].split("#")[0].rstrip("/")
        if key and key not in seen:
            seen.add(key)
            merged.append(r)
    merged.sort(key=lambda r: r["date"] or "0000", reverse=True)

    if a.archive_check:
        web = [r for r in merged if r["source"].split(":")[0] in ("exa", "gdelt", "hn")][: a.archive_check]
        for r in web:
            r["archived"] = wayback_check(r["url"])
            time.sleep(1)

    if a.json:
        print(json.dumps({"query": a.query, "status": status, "results": merged},
                         ensure_ascii=False, indent=2))
        return
    print(f"# {a.query}  ({len(merged)} unique results, {time.time() - t0:.0f}s)\n")
    for s in chosen:
        print(f"  {s:7} {status.get(s, '-')}")
    print()
    for r in merged:
        print(f"[{r['source']:9}] {r['date'] or '----------'}  {r['title'][:110]}")
        print(f"             {r['url']}")
        if r.get("extra"):
            print(f"             ({r['extra']})")
        if r.get("archived"):
            print(f"             archived: {r['archived']}")


if __name__ == "__main__":
    sys.exit(main())
