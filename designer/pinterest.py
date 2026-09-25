"""يجمع أفكار أغلفة من Pinterest: يبحث ويحفظ صور أحسن النتائج حتى المصمم يدرسها (مو حتى ينسخها).

    python3 designer/pinterest.py "youtube thumbnail" --limit 30

الصور تنحفظ بـ designer/references/pinterest/<البحث>/ (يتجاهلها git) ومعاها index.json.
يحتاج الشبكة مفتوحة لـ *.pinterest.com و*.pinimg.com.
"""
import argparse
import json
import re
import sys
import urllib.parse
import urllib.request
from pathlib import Path

OUT_DIR = Path(__file__).resolve().parent / "references" / "pinterest"
SEARCH_URL = "https://www.pinterest.com/resource/BaseSearchResource/get/"
UA = "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36"


def slug(query: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", query.lower()).strip("-") or "search"


def search_url(query: str, limit: int) -> str:
    data = {"options": {"query": query, "scope": "pins", "page_size": min(max(limit, 1), 50)}, "context": {}}
    params = {"source_url": "/search/pins/?q=" + urllib.parse.quote(query), "data": json.dumps(data)}
    return SEARCH_URL + "?" + urllib.parse.urlencode(params)


def parse_results(payload: dict, limit: int) -> list[dict]:
    """يطلع من رد Pinterest قائمة: رقم الـ pin، والعنوان، والوصف، ورابط أكبر صورة."""
    results = (payload.get("resource_response") or {}).get("data") or {}
    if isinstance(results, dict):
        results = results.get("results") or []
    pins = []
    for item in results:
        if not isinstance(item, dict):
            continue
        images = item.get("images") or {}
        best = images.get("orig") or images.get("736x") or images.get("474x") or {}
        if not best.get("url"):
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


def fetch_json(url: str) -> dict:
    req = urllib.request.Request(url, headers={
        "User-Agent": UA, "Accept": "application/json", "X-Requested-With": "XMLHttpRequest"})
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.load(r)


def download(url: str, dest: Path) -> None:
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=30) as r:
        dest.write_bytes(r.read())


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="يبحث بـ Pinterest ويحفظ صور الأفكار")
    ap.add_argument("query")
    ap.add_argument("--limit", type=int, default=30)
    args = ap.parse_args(argv)
    try:
        pins = parse_results(fetch_json(search_url(args.query, args.limit)), args.limit)
    except OSError as e:
        print(f"✗ خطأ: ما گدرت أوصل لـ Pinterest ({e}). تأكد إن *.pinterest.com و*.pinimg.com مفتوحة بالشبكة.")
        return 1
    except (ValueError, json.JSONDecodeError):
        print("✗ خطأ: رد Pinterest مو مفهوم. يمكن غيّروا شكل الموقع.")
        return 1
    if not pins:
        print("✗ ما طلعت نتائج. جرّب كلمة بحث ثانية.")
        return 1
    out = OUT_DIR / slug(args.query)
    out.mkdir(parents=True, exist_ok=True)
    saved = 0
    for i, pin in enumerate(pins, 1):
        name = f"{i:02d}-{pin['id']}.jpg"
        try:
            download(pin["image"], out / name)
        except OSError:
            continue
        pin["file"] = name
        saved += 1
    (out / "index.json").write_text(json.dumps(pins, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"✓ انحفظت {saved} صورة بـ {out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
