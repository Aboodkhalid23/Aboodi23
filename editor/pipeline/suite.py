"""The editing suite: a web page where the owner sees the episode's timeline, edits it, and leaves requests on it.

  build  <episode_dir>            makes edit/work/suite/ — the page, a light preview (keyframe every 12 frames, so
                                  scrubbing is instant), one thumbnail per scene, the spoken words with their times,
                                  and 6 real pictures to choose from for every scene that searches for one.
  apply  <episode_dir> <edits.json>  brings what he saved on the page back into edit_plan.json (scenes, chosen
                                  pictures, reels) and prints his open requests.

The page itself is editor/suite/index.html; it is published as an Artifact with the folder's files beside it.
"""
import argparse
import json
import shutil
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor
from io import BytesIO
from pathlib import Path

PAGE = Path(__file__).resolve().parents[1] / "suite" / "index.html"
PICKS = 6          # pictures offered per search
THUMB_W = 192      # scene thumbnails on the timeline
CAND_W = 320       # pictures in the chooser
IMAGE_KINDS = {"image", "face_cutout", "graphic", "ai_image", "entity"}


def _run(cmd: list[str]) -> None:
    subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)


def _duration(path: Path) -> float:
    out = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(path)],
                         capture_output=True, text=True).stdout.strip()
    return float(out or 0)


def light_preview(src: Path, dest: Path) -> None:
    """540p, a keyframe every 12 frames and the index up front: the browser seeks to any spot without waiting."""
    _run(["ffmpeg", "-y", "-v", "error", "-i", str(src), "-vf", "scale=-2:540", "-c:v", "libx264", "-preset", "veryfast",
          "-crf", "27", "-g", "12", "-keyint_min", "12", "-sc_threshold", "0", "-pix_fmt", "yuv420p",
          "-movflags", "+faststart", "-c:a", "aac", "-b:a", "96k", str(dest)])


def thumbs(video: Path, beats: list[dict], out: Path) -> None:
    out.mkdir(parents=True, exist_ok=True)

    def one(i):
        b = beats[i]
        t = b["start"] + min(0.6, (b["end"] - b["start"]) / 2)
        _run(["ffmpeg", "-y", "-v", "error", "-ss", f"{t:.2f}", "-i", str(video), "-frames:v", "1",
              "-vf", f"scale={THUMB_W}:-2", "-q:v", "6", str(out / f"{i}.jpg")])
    with ThreadPoolExecutor(6) as pool:
        list(pool.map(one, range(len(beats))))


def _small(url: str) -> str:
    """Wikimedia serves any width of a picture: ask for a small one instead of the original."""
    if "upload.wikimedia.org" in url:
        from urllib.parse import unquote
        return f"https://commons.wikimedia.org/wiki/Special:FilePath/{unquote(url.split('/')[-1])}?width={CAND_W}"
    return url


def candidates(beats: list[dict], out: Path, log=print) -> dict:
    """{query: [{img, provider, title, license, artist, page, url, width, height}]} — real pictures only."""
    import requests
    from PIL import Image
    from .sources import HEADERS, find
    out.mkdir(parents=True, exist_ok=True)
    queries = {}
    for b in beats:
        if b.get("query") and b.get("kind") in IMAGE_KINDS:
            queries.setdefault(b["query"], b.get("source"))
    session, result, n = requests.Session(), {}, 0

    def grab(f):
        try:   # a small copy is enough to choose from; the full picture is downloaded only for the chosen one
            r = session.get(_small(f.url), headers=HEADERS, timeout=20)
            r.raise_for_status()
            im = Image.open(BytesIO(r.content)).convert("RGB")
        except Exception:   # one picture refusing to load is skipped, the others still show
            return None
        im.thumbnail((CAND_W, CAND_W))
        return im

    def search(item):
        q, src = item
        found = find(q, "image", src, session)[:PICKS * 2]
        with ThreadPoolExecutor(6) as pool:
            return q, list(zip(found, pool.map(grab, found)))

    with ThreadPoolExecutor(3) as pool:   # a few searches at once (each asks 8 libraries)
        for q, pairs in pool.map(search, queries.items()):
            result[q] = []
            for f, im in pairs:
                if im is None or len(result[q]) >= PICKS:
                    continue
                name = f"cand/{n}.jpg"
                im.save(out.parent / name, quality=78)
                n += 1
                result[q].append({"img": name, "provider": f.provider, "title": f.title[:120], "license": f.license,
                                  "artist": (f.artist or "")[:80], "page": f.page, "url": f.url,
                                  "width": f.width, "height": f.height})
            log(f"🖼️  {q}: {len(result[q])} صور", flush=True)
    return result


def build(ep_dir: Path, name: str | None = None, with_candidates: bool = True) -> Path:
    edit = ep_dir / "edit"
    plan = json.loads((edit / "edit_plan.json").read_text(encoding="utf-8"))
    out = edit / "work" / "suite"
    out.mkdir(parents=True, exist_ok=True)
    src = next((p for p in (edit / "preview.mp4", edit / "final.mp4", edit / "work" / "clean.mp4") if p.exists()), None)
    if src is None:
        raise SystemExit("ما اكو فيديو للحلقة (preview.mp4) — شغّل المونتاج أول")
    print("🎞️  نسخة خفيفة للصفحة…", flush=True)
    light_preview(src, out / "preview.mp4")
    beats = plan["beats"]
    print("🖼️  صور المشاهد…", flush=True)
    thumbs(out / "preview.mp4", beats, out / "thumbs")
    words_file = edit / "clean_words.json"
    words = json.loads(words_file.read_text(encoding="utf-8")) if words_file.exists() else []
    cands = candidates(beats, out / "cand") if with_candidates else {}
    data = {
        "episode": name or ep_dir.name,
        "duration": round(max(_duration(out / "preview.mp4"), beats[-1]["end"] if beats else 0), 2),
        "beats": [{**b, "thumb": f"thumbs/{i}.jpg"} for i, b in enumerate(beats)],
        "words": [[w["t"], w["s"], w["e"]] for w in words],
        "chapters": plan.get("chapters", []),
        "shorts": plan.get("shorts", []),
        "music": plan.get("music", []),
        "candidates": cands,
    }
    (out / "data.json").write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")
    shutil.copy(PAGE, out / "index.html")
    print(f"✅ الصفحة جاهزة بـ {out}", flush=True)
    return out


# ---------- back from the page ----------

PAGE_ONLY = {"thumb", "uid", "orig"}


def apply(ep_dir: Path, edits_file: Path) -> list[dict]:
    """`edits_file`: {"edits": <db doc edits/current>, "requests": [<db docs in requests/>]}."""
    from .plan import load_plan, save_plan, Beat
    d = json.loads(edits_file.read_text(encoding="utf-8"))
    edits, requests_ = d.get("edits") or {}, d.get("requests") or []
    plan_path = ep_dir / "edit" / "edit_plan.json"
    plan = load_plan(plan_path)
    if edits.get("beats"):
        fields = set(Beat.__dataclass_fields__)
        plan.beats = [Beat(**{k: v for k, v in b.items() if k in fields and k not in PAGE_ONLY}) for b in edits["beats"]]
    if "reels" in edits:
        plan.shorts = [{"from": r["from"], "to": r["to"], "title": r.get("title", "")} for r in edits["reels"]]
    save_plan(plan, plan_path)
    open_ = [r for r in requests_ if r.get("status") != "done"]
    open_.sort(key=lambda r: r.get("t", 0))
    return open_


def main(argv=None):
    ap = argparse.ArgumentParser(prog="python -m editor.pipeline.suite")
    sub = ap.add_subparsers(dest="cmd", required=True)
    b = sub.add_parser("build")
    b.add_argument("episode")
    b.add_argument("--name")
    b.add_argument("--no-candidates", action="store_true")
    a = sub.add_parser("apply")
    a.add_argument("episode")
    a.add_argument("edits")
    args = ap.parse_args(argv)
    if args.cmd == "build":
        build(Path(args.episode), args.name, not args.no_candidates)
    else:
        for r in apply(Path(args.episode), Path(args.edits)):
            span = f"{r.get('t', 0):.2f}" + (f"–{r['t2']:.2f}" if r.get("t2") else "")
            print(f"[{span}] {r.get('text', '')}" + ("  (صوت)" if r.get("audio") else ""))


if __name__ == "__main__":
    sys.exit(main())
