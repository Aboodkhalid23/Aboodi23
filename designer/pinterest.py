"""يجمع أفكار أغلفة من Pinterest: يبحث ويحفظ صور أحسن النتائج حتى المصمم يدرسها (مو حتى ينسخها).

    python3 designer/pinterest.py "youtube thumbnail" --limit 30

الصور تنحفظ بـ designer/references/pinterest/<البحث>/ (يتجاهلها git) ومعاها index.json.
يحتاج الشبكة مفتوحة لـ *.pinterest.com و*.pinimg.com.
"""
import argparse
import hashlib
import http.cookiejar
import json
import re
import sys
import urllib.parse
import urllib.request
from pathlib import Path

OUT_DIR = Path(__file__).resolve().parent / "references" / "pinterest"
SITE = "https://www.pinterest.com"
SEARCH_URL = SITE + "/resource/BaseSearchResource/get/"
UA = "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36"
MAX_DOWNLOAD_BYTES = 15 * 1024 * 1024


def slug(query: str) -> str:
    """اسم مجلد آمن للبحث. البحوث العربية ما إلها أحرف لاتينية، فنميّزها بهاش
    قصير حتى بحثين مختلفين ما يتشاركون نفس المجلد ويمسح وحدة صور الثانية."""
    s = re.sub(r"[^a-z0-9]+", "-", query.lower()).strip("-")
    if s:
        return s
    return "q-" + hashlib.sha1(query.encode("utf-8")).hexdigest()[:8]


def search_url(query: str, limit: int) -> str:
    data = {"options": {"query": query, "scope": "pins", "page_size": min(max(limit, 1), 50)}, "context": {}}
    params = {"source_url": "/search/pins/?q=" + urllib.parse.quote(query), "data": json.dumps(data)}
    return SEARCH_URL + "?" + urllib.parse.urlencode(params)


def parse_results(payload: dict, limit: int) -> list[dict]:
    """يطلع من رد Pinterest قائمة: رقم الـ pin، والعنوان، والوصف، ورابط أكبر صورة."""
    if not isinstance(payload, dict):
        return []
    resource_response = payload.get("resource_response")
    if not isinstance(resource_response, dict):
        return []
    data = resource_response.get("data")
    if isinstance(data, dict):
        results = data.get("results") or []
    elif isinstance(data, list):
        results = data
    else:
        return []
    pins = []
    for item in results:
        if not isinstance(item, dict):
            continue
        images = item.get("images")
        if not isinstance(images, dict):
            continue
        best = images.get("orig") or images.get("736x") or images.get("474x") or {}
        if not isinstance(best, dict) or not isinstance(best.get("url"), str):
            continue
        pins.append({
            "id": str(item.get("id", "")),
            "title": (item.get("title") or item.get("grid_title") or "").strip(),
            "description": (item.get("description") or "").strip()[:300],
            "image": best["url"],
            "link": f"https://www.pinterest.com/pin/{item.get('id', '')}/",
        })
        if len(pins) >= limit:
            break
    return pins


def session_headers(jar: http.cookiejar.CookieJar) -> dict:
    """هيدرات طلب النتائج. Pinterest يرفض الطلب (403) بدون رمز csrftoken من جلسة مفتوحة."""
    headers = {"User-Agent": UA, "Accept": "application/json", "X-Requested-With": "XMLHttpRequest",
               "X-Pinterest-PWS-Handler": "www/search/[scope].js", "X-Pinterest-AppState": "active",
               "Referer": SITE + "/"}
    for cookie in jar:
        if cookie.name == "csrftoken":
            headers["X-CSRFToken"] = cookie.value
    return headers


def fetch_json(url: str) -> dict:
    """يفتح صفحة البحث أول (حتى ياخذ كوكيز الجلسة)، وبعدها يطلب النتائج بنفس الجلسة."""
    jar = http.cookiejar.CookieJar()
    opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(jar))
    source = urllib.parse.parse_qs(urllib.parse.urlparse(url).query).get("source_url", ["/"])[0]
    with opener.open(urllib.request.Request(SITE + source, headers={"User-Agent": UA}), timeout=30) as r:
        r.read()
    with opener.open(urllib.request.Request(url, headers=session_headers(jar)), timeout=30) as r:
        return json.load(r)


def download(url: str, dest: Path) -> bool:
    """ينزّل صورة من pinimg.com بس، وبحد أقصى 15MB، ويرجع True إذا نزلت. أي رابط ثاني
    (http أو موقع غير Pinterest) يترك بصمت ويرجع False حتى ما نفتح على مصدر غريب."""
    parsed = urllib.parse.urlparse(url)
    if parsed.scheme != "https" or not (parsed.hostname or "").endswith("pinimg.com"):
        return False
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=30) as r:
        dest.write_bytes(r.read(MAX_DOWNLOAD_BYTES))
    return True


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="يبحث بـ Pinterest ويحفظ صور الأفكار")
    ap.add_argument("query")
    ap.add_argument("--limit", type=int, default=30)
    args = ap.parse_args(argv)
    try:
        data = fetch_json(search_url(args.query, args.limit))
        if not isinstance(data, dict):
            print("✗ خطأ: رد Pinterest مو مفهوم. يمكن غيّروا شكل الموقع.")
            return 1
        pins = parse_results(data, args.limit)
    except OSError as e:
        print(f"✗ خطأ: ما گدرت أوصل لـ Pinterest ({e}). تأكد إن *.pinterest.com و*.pinimg.com مفتوحة بالشبكة.")
        return 1
    except (ValueError, json.JSONDecodeError, AttributeError, TypeError):
        print("✗ خطأ: رد Pinterest مو مفهوم. يمكن غيّروا شكل الموقع.")
        return 1
    if not pins:
        print("✗ ما طلعت نتائج. جرّب كلمة بحث ثانية.")
        return 1
    try:
        out = OUT_DIR / slug(args.query)
        out.mkdir(parents=True, exist_ok=True)
        saved = 0
        for i, pin in enumerate(pins, 1):
            name = f"{i:02d}-{pin['id']}.jpg"
            try:
                if not download(pin["image"], out / name):
                    continue
            except OSError:
                continue
            pin["file"] = name
            saved += 1
        (out / "index.json").write_text(json.dumps(pins, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"✓ انحفظت {saved} صورة بـ {out}")
    except OSError as e:
        print(f"✗ خطأ: ما گدرت أحفظ الصور ({e}).")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
