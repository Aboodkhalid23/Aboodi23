"""Real articles: screenshot the actual page and find the sentence to highlight (tools/article-shot.mjs).
If the site refuses (paywall, block, timeout) the beat falls back to a re-typeset headline card."""
import json
import subprocess
from pathlib import Path

from .paths import Episode
from .plan import EditPlan

TOOL = Path(__file__).resolve().parent.parent / "tools" / "article-shot.mjs"


def shoot(url: str, quote: str, out: Path) -> dict:
    job = out.with_suffix(".job.json")
    job.write_text(json.dumps({"url": url, "quote": quote, "out": str(out)}, ensure_ascii=False), encoding="utf-8")
    try:
        proc = subprocess.run(["node", str(TOOL), str(job)], capture_output=True, text=True, timeout=120)
    except subprocess.TimeoutExpired:
        return {"error": "timeout"}
    finally:
        job.unlink(missing_ok=True)
    line = next((ln for ln in reversed(proc.stdout.splitlines()) if ln.startswith("{")), "")
    return json.loads(line) if line else {"error": (proc.stderr or "no output")[-300:]}


def collect_articles(plan: EditPlan, ep: Episode) -> list[dict]:
    """Screenshot every `article` beat into assets/article_<i>.png (+ .json with the quote's position).
    Returns the fallbacks (beats turned into headline cards)."""
    fallbacks = []
    for i, b in enumerate(plan.beats):
        g = b.graphic or {}
        if b.kind != "graphic" or g.get("type") != "article":
            continue
        png, meta = ep.assets / f"article_{i}.png", ep.assets / f"article_{i}.json"
        old = json.loads(meta.read_text(encoding="utf-8")) if meta.exists() else {}
        if png.exists() and old.get("url") == g["url"] and old.get("quote") == g["quote"]:
            continue
        d = shoot(g["url"], g["quote"], png)
        if d.get("ok"):
            w, h = d["width"], d["height"]
            d["rects"] = [[r[0] / w, r[1] / h, r[2] / w, r[3] / h] for r in d["rects"]]
            meta.write_text(json.dumps({**d, "url": g["url"], "quote": g["quote"]}, ensure_ascii=False), encoding="utf-8")
            if not d["found"]:
                print(f"⚠️  beat {i}: الجملة ما انلگت بالصفحة، تطلع الصفحة بدون تظليل")
            continue
        fallbacks.append({"beat": i, "url": g["url"], "reason": d.get("error", "")[:200]})
        b.graphic = {"type": "headline", "outlet": g.get("outlet", ""), "title": g["title"],
                     "highlight": g.get("highlight", "")}
    return fallbacks
