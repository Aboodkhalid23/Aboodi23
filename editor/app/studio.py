"""What each screen of the Mac studio shows, and what it writes back (owner, 2026-10-24: "نفس الواجهة ونفس
المميزات" of an Arabic editing studio he saw in a reel).

  new clip   probe + look thumbnails made from a frame of his own footage, flat/log detection
  الجمل      every phrase with keep/cut and why (the cutter's own decision), his changes → cuts_override.json
  الكابشن    the kept words with Whisper's doubt, his corrections → clean_words.json and transcript.json
  الخطة      the plan as storyboard cards (words, what shows, motion, picture, source)
  timeline   waveform, filmstrip, caption blocks, scenes
Everything is computed from the episode folder; nothing here needs Claude.
"""
import hashlib
import json
import re
import subprocess
from pathlib import Path

import numpy as np

from editor.pipeline.clean import decide, keep_segments, loudness
from editor.pipeline.grade import LOOK_NAMES, LOOKS, POLISH, adjust_filter
from editor.pipeline.paths import Episode
from editor.pipeline.transcribe import Word, load_words, save_words

THUMB_LOOKS = ["none", "natural", "cinema", "documentary", "vivid", "action", "golden", "warm-film", "soft-film", "teal-orange",
               "night", "bleach", "mono", "log", "log-vivid"]
CAMERA_LOOKS = ["natural", "cinema", "documentary", "vivid", "action", "golden", "warm-film", "soft-film", "teal-orange",
                "night", "bleach", "mono"]   # on top of a camera conversion (the generic "log" curves make no sense there)
LOW = 0.55            # Whisper's confidence under this: the word is underlined for a check
REASON_GROUP = {"إعادة": "إعادة", "إعادة (تكملة غلط)": "إعادة", "إشارة غلط": "إعادة", "قبل إشارة الغلط": "إعادة",
                "بدأ الجملة من جديد": "بداية متعثرة", "كلمة مقطوعة": "بداية متعثرة", "تأتأة": "بداية متعثرة",
                "حشو": "بلا كلام", "حذف يدوي": "حذفتها انت"}
KIND_AR = {"face": "وجهك", "face_zoom_in": "وجهك، تقريب", "face_zoom_out": "وجهك، تبعيد", "face_punch": "وجهك، ضربة",
           "face_paper": "أوراق يمّك", "face_fx": "وجهك ويه حركة", "face_cutout": "وجهك مقصوص", "face_split": "شاشة مقسومة", "image": "صورة حقيقية",
           "entity": "صورة شخص", "graphic": "موشن جرافك", "footage": "أرشيف حقيقي", "ai_image": "صورة ذكاء اصطناعي",
           "ai_video": "فيديو ذكاء اصطناعي", "avatar": "شخصيتك المرسومة", "cinematic_title": "عنوان سينمائي",
           "halftone_cutout": "مقصوص نقاط", "kinetic": "كتابة متحركة", "band": "شريط صورة وورقة", "desk": "مكتب ورق"}


def _ff(args: list[str]) -> subprocess.CompletedProcess:
    return subprocess.run(["ffmpeg", "-y", "-v", "error", *args], capture_output=True, text=True)


def _duration(path: Path) -> float:
    out = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(path)],
                         capture_output=True, text=True).stdout.strip()
    try:
        return float(out)
    except ValueError:
        return 0.0


# ---------- new clip ----------

def _signal(frame: Path) -> dict:
    out = subprocess.run(["ffmpeg", "-v", "error", "-i", str(frame), "-vf", "signalstats,metadata=print:file=-",
                          "-f", "null", "-"], capture_output=True, text=True).stdout
    return {k: float(v) for k, v in re.findall(r"lavfi\.signalstats\.(YLOW|YHIGH|SATAVG|YAVG)=([\d.]+)", out)}


def _sony(src: Path) -> bool:
    """Sony cameras write their name in the file's tags (XAVC)."""
    out = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format_tags:stream_tags", "-of", "json", str(src)],
                         capture_output=True, text=True).stdout.lower()
    return "sony" in out or "xavc" in out


def look_thumbs(frame: Path, out: Path, source: str, strength: float = 1.0, keys: list[str] | None = None) -> dict:
    """One small picture per look of his own frame, through the same cube the render uses.
    `keys`: only these looks (a group of the big library, made when he opens that group)."""
    from editor.pipeline.grade import LOOKS as ALL, look_chain
    from editor.pipeline.luts import bake, split_chain
    looks = {}
    for k in ([x for x in keys if x in ALL] if keys else CAMERA_LOOKS + ["none"] if source != "rec709" else THUMB_LOOKS):
        pix, spatial = split_chain(look_chain(k))
        cube = bake(out / "cubes", source, pix, strength)
        chain = ",".join(x for x in ("scale=-2:240", f"lut3d=file='{cube}'", spatial) if x)
        jpg = out / f"look_{source}_{k}.jpg"
        if jpg.exists() or _ff(["-i", str(frame), "-vf", chain, "-q:v", "4", str(jpg)]).returncode == 0:
            looks[k] = {"name": LOOK_NAMES.get(k, k), "img": f"{out.name}/{jpg.name}"}
    return looks


def group_thumbs(src: Path, cache: Path, source: str, keys: list[str]) -> dict:
    """Pictures for one group of the big colour library, from the frame the probe already took."""
    d = probe_source(src, cache)
    out = cache / d["key"]
    return look_thumbs(out / "frame.png", out, source if source in ("rec709", "slog3") else d["source"], keys=keys)


def probe_source(src: Path, cache: Path, source: str | None = None) -> dict:
    """Length, size, the camera (flat log? Sony?) and one thumbnail per look, from a frame a third of the way in.
    `source`: the camera conversion the owner picked (rec709 | slog3); a guess when not given."""
    from editor.pipeline.luts import SOURCES
    src = Path(src).expanduser()
    key = hashlib.sha1(f"{src}:{src.stat().st_size}:{src.stat().st_mtime}".encode()).hexdigest()[:16]
    out = cache / key
    meta = out / "probe.json"
    if meta.exists():
        d = json.loads(meta.read_text(encoding="utf-8"))
        if source and source in SOURCES and source != d.get("source"):
            d.update(source=source, looks=look_thumbs(out / "frame.png", out, source),
                     suggest="cinema" if source != "rec709" else ("log" if d["flat"] else "cinema"))
            meta.write_text(json.dumps(d, ensure_ascii=False), encoding="utf-8")
        return d
    out.mkdir(parents=True, exist_ok=True)
    dur = _duration(src)
    frame = out / "frame.png"
    _ff(["-ss", f"{dur * 0.33:.2f}", "-i", str(src), "-frames:v", "1", "-vf", "scale=-2:360", str(frame)])
    if not frame.exists():
        raise ValueError("ما گدرت أقرا الفيديو")
    st = _signal(frame)
    # flat (log) footage: little contrast and little colour (a normal phone picture has SATAVG ≈ 25–45)
    flat = bool(st) and st.get("SATAVG", 99) < 16 and st.get("YHIGH", 255) - st.get("YLOW", 0) < 175
    sony = _sony(src)
    if not source or source not in SOURCES:
        source = "slog3" if flat and sony else "rec709"
    d = {"key": key, "path": str(src), "name": src.stem, "duration": round(dur, 2), "size": src.stat().st_size,
         "flat": flat, "sony": sony, "source": source, "looks": look_thumbs(frame, out, source),
         "suggest": "cinema" if source != "rec709" else ("log" if flat else "cinema")}
    meta.write_text(json.dumps(d, ensure_ascii=False), encoding="utf-8")
    return d


def lut_preview(cache_dir: Path, lut: Path) -> str:
    """A thumbnail of the probed frame through the owner's .cube file."""
    out = cache_dir / f"look_lut_{hashlib.sha1(str(lut).encode()).hexdigest()[:8]}.jpg"
    _ff(["-i", str(cache_dir / "frame.png"), "-vf", f"scale=-2:240,lut3d=file='{lut}'", "-q:v", "4", str(out)])
    return out.name if out.exists() else ""


def save_look(ep: Episode, look: dict) -> dict:
    from editor.pipeline.luts import SOURCES
    keep = {k: look[k] for k in ("look", "temp", "tint", "exposure", "lut", "source", "strength") if k in look}
    keep["source"] = keep.get("source") if keep.get("source") in SOURCES else "rec709"
    keep["strength"] = max(0.0, min(1.0, float(keep.get("strength", 1.0) if keep.get("strength") is not None else 1.0)))
    if keep.get("look") not in LOOKS:
        keep["look"] = "cinema"
    for k in ("temp", "tint"):
        keep[k] = max(-100.0, min(100.0, float(keep.get(k, 0) or 0)))
    keep["exposure"] = max(-2.0, min(2.0, float(keep.get("exposure", 0) or 0)))
    ep.edit.mkdir(parents=True, exist_ok=True)
    (ep.edit / "look.json").write_text(json.dumps(keep, ensure_ascii=False, indent=1), encoding="utf-8")
    return keep


# ---------- الجمل ----------

def units(words: list[Word], pause: float = 0.35, most: int = 14) -> list[list[Word]]:
    """Sentence-sized pieces: a short pause, a full stop or a question mark ends one (the cutter's own phrases are
    breath-long, too long to judge one by one)."""
    out, cur = [], []
    for i, w in enumerate(words):
        cur.append(w)
        nxt = words[i + 1] if i + 1 < len(words) else None
        if nxt is None or nxt.start - w.end >= pause or (re.search(r"[.؟?!،,]$", w.text) and len(cur) >= 3) \
                or len(cur) >= most:
            out.append(cur)
            cur = []
    return out


def _auto(words: list[Word], overrides: dict) -> tuple[set, dict]:
    kept, removed = decide(words, overrides)
    kept_ids = {id(w) for w in kept}
    why = {}
    for ws, reason in removed:
        for w in ws:
            why[id(w)] = reason
    return kept_ids, why


def _overrides(ep: Episode) -> dict:
    f = ep.edit / "cuts_override.json"
    try:
        return json.loads(f.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}


def sentences(ep: Episode) -> dict:
    """Every phrase of the raw talk: kept or cut, and why (the same decision the cutter makes)."""
    if not ep.transcript.exists():
        return {"ready": False, "items": []}
    words = load_words(ep.transcript)
    kept_ids, why = _auto(words, _overrides(ep))
    items, groups = [], {}
    for i, p in enumerate(units(words)):
        gone = [w for w in p if id(w) not in kept_ids]
        reasons = [why.get(id(w), "حذف يدوي") for w in gone]
        main = max(set(reasons), key=reasons.count) if reasons else None
        keep = len(gone) < len(p) / 2
        group = REASON_GROUP.get(main or "", main) if not keep else None
        if group:
            groups[group] = groups.get(group, 0) + 1
        items.append({"i": i, "s": round(p[0].start, 2), "e": round(p[-1].end, 2), "text": " ".join(w.text for w in p),
                      "keep": keep, "why": group, "partial": bool(gone) and keep,
                      "cut_words": [w.text for w in gone] if keep and gone else []})
    kept_words = [w for w in words if id(w) in kept_ids]
    kept_secs = sum(e - s for s, e in keep_segments([kept_words])) if kept_words else 0.0
    raw = _duration(ep.source) if ep.source.exists() else (words[-1].end if words else 0)
    return {"ready": True, "items": items, "raw": round(raw, 1), "after": round(kept_secs, 1),
            "removed": sum(not x["keep"] for x in items), "total": len(items), "groups": groups,
            "cut_done": ep.cuts.exists() and ep.clean_video.exists()}


def set_sentences(ep: Episode, keep: dict) -> dict:
    """`keep`: {phrase index: true/false} as the owner left them. Only what differs from the automatic
    decision is written, so the cutter's own improvements keep working."""
    words = load_words(ep.transcript)
    phrases = units(words)
    kept_ids, _ = _auto(words, {})
    drop, back = [], []
    for k, want in keep.items():
        i = int(k)
        if not 0 <= i < len(phrases):
            continue
        p = phrases[i]
        auto_keep = sum(id(w) in kept_ids for w in p) >= len(p) / 2
        if want and not auto_keep:
            back.append([round(p[0].start - 0.01, 3), round(p[-1].end + 0.01, 3)])
        elif not want and auto_keep:
            drop.append([round(p[0].start - 0.01, 3), round(p[-1].end + 0.01, 3)])
    ov = _overrides(ep)
    ov["keep"], ov["drop"] = back, drop + ov.get("drop_words", [])
    (ep.edit / "cuts_override.json").write_text(json.dumps(ov, ensure_ascii=False, indent=1), encoding="utf-8")
    return sentences(ep)


# ---------- الكابشن ----------

def _to_raw(t: float, segs: list) -> float:
    """A time on the cleaned video → the same moment in the raw footage."""
    acc = 0.0
    for s, e in segs:
        if t <= acc + (e - s):
            return s + (t - acc)
        acc += e - s
    return segs[-1][1] if segs else t


def captions(ep: Episode) -> dict:
    if not ep.clean_words.exists():
        return {"ready": False, "lines": []}
    words = load_words(ep.clean_words)
    lines, flat = [], []
    for p in units(words, pause=0.5, most=12):
        line = []
        for w in p:
            i = len(flat)
            flat.append(w)
            line.append({"i": i, "t": w.text, "s": round(w.start, 2), "e": round(w.end, 2), "doubt": w.p < LOW})
        lines.append(line)
    pauses = sum(b.start - a.end > 0.5 for a, b in zip(words, words[1:]))
    return {"ready": True, "lines": lines, "doubt": sum(w.p < LOW for w in words), "long_pauses": pauses}


def edit_words(ep: Episode, fixes: dict, delete: list) -> dict:
    """`fixes`: {word index: new text}; `delete`: word indexes to cut out of the video (needs a new cut)."""
    words = load_words(ep.clean_words)
    segs = json.loads(ep.cuts.read_text(encoding="utf-8")) if ep.cuts.exists() else []
    raw = load_words(ep.transcript) if ep.transcript.exists() else []
    for k, text in fixes.items():
        i = int(k)
        if 0 <= i < len(words) and text.strip():
            words[i].text, words[i].p = text.strip(), 1.0
            t = _to_raw((words[i].start + words[i].end) / 2, segs)      # the same word in the raw transcript
            near = min(raw, key=lambda w: abs((w.start + w.end) / 2 - t), default=None)
            if near and abs((near.start + near.end) / 2 - t) < 0.4:
                near.text, near.p = text.strip(), 1.0
    save_words(words, ep.clean_words)
    if raw:
        save_words(raw, ep.transcript)
    if delete:
        ov = _overrides(ep)
        extra = [[round(_to_raw(words[i].start, segs), 3), round(_to_raw(words[i].end, segs), 3)]
                 for i in map(int, delete) if 0 <= i < len(words)]
        ov["drop_words"] = ov.get("drop_words", []) + extra
        ov["drop"] = ov.get("drop", []) + extra
        (ep.edit / "cuts_override.json").write_text(json.dumps(ov, ensure_ascii=False, indent=1), encoding="utf-8")
    return {**captions(ep), "needs_cut": bool(delete)}


# ---------- الخطة ----------

_LATIN = re.compile(r"[A-Za-z]")


def ar(text) -> str:
    """Arabic text only: search words and AI prompts are English by design and never reach the owner's screen."""
    t = str(text or "").strip()
    return "" if not t or len(_LATIN.findall(t)) > len(t) / 4 else t


def _beat_image(ep: Episode, i: int, b: dict) -> str | None:
    for stem in (f"img_{i}", f"ai_{i}", f"paper_{i}_0", f"cutout_{i}"):
        for f in sorted(ep.assets.glob(stem + ".*")):
            if f.suffix.lower() in (".jpg", ".jpeg", ".png", ".webp"):
                return f"edit/assets/{f.name}"
    if b.get("kind") == "entity" and b.get("entity"):
        from editor.pipeline.entities import entity_image
        f = entity_image(ep, b["entity"])
        if f and f.exists():
            try:
                return str(f.relative_to(ep.root))
            except ValueError:
                return None
    thumb = ep.work / "suite" / "thumbs" / f"{i}.jpg"
    return f"edit/work/suite/thumbs/{i}.jpg" if thumb.exists() else None


MOTION_AR = {"zoom": "تقريب", "flash": "وميض", "whip": "سحبة سريعة", "glitch": "تشويش", "shutter": "باب ينزل", "slide": "ورقة تنسحب",
             "code": "حركة طبقات", "ai": "حركة ذكاء اصطناعي", "subscribe": "زر الاشتراك", "search": "صفحة يوتيوب بقناتك",
             "tv": "تلفزيون", "none": ""}


def _credits(ep: Episode) -> list[str]:
    f = ep.credits
    return [l.strip() for l in f.read_text(encoding="utf-8").splitlines() if l.strip()] if f.exists() else []


def storyboard(ep: Episode) -> dict:
    if not ep.plan.exists():
        return {"ready": False, "cards": []}
    plan = json.loads(ep.plan.read_text(encoding="utf-8"))
    words = load_words(ep.clean_words) if ep.clean_words.exists() else []
    off = sum(e - s for s, e in plan.get("teaser", []))
    credits = _credits(ep)
    cards = []
    for i, b in enumerate(plan.get("beats", [])):
        said = " ".join(w.text for w in words if b["start"] - off <= (w.start + w.end) / 2 < b["end"] - off)
        shows = ar(b.get("caption")) or ar(b.get("title")) or ar(b.get("prompt"))
        if b.get("papers"):
            shows = "، ".join(x for x in (ar(p.get("title")) for p in b["papers"]) if x)
        motion = "، ".join(MOTION_AR.get(x, "") for x in (b.get("transition"), b.get("animate"), b.get("fx")) if MOTION_AR.get(x))
        q = (b.get("query") or "").lower()
        src = next((c for c in credits if q and q.split()[0] in c.lower()), "") if q else ""
        cards.append({"i": i, "start": b["start"], "end": b["end"], "kind": b["kind"],
                      "kind_ar": KIND_AR.get(b["kind"], "مشهد"), "title": ar(b.get("title")) or ar(b.get("caption"))
                      or KIND_AR.get(b["kind"], "مشهد"), "said": said, "shows": shows,
                      "motion": motion, "source": src, "img": _beat_image(ep, i, b), "note": b.get("note", ""),
                      "effect": b.get("effect"), "transition": b.get("transition"), "stickers": b.get("stickers") or [],
                      "text": ar(b.get("title")) or ar(b.get("caption")), "own": bool((b.get("pick") or {}).get("local")),
                      "sfx": b.get("sfx"), "treatment": b.get("treatment"),
                      "query_raw": b.get("query") if b.get("query") not in ("own footage", "own picture", "chosen picture", "chosen footage") else ""})
    return {"ready": True, "cards": cards, "style": plan.get("style", {}).get("primary"),
            "summary": plan.get("style_reason", ""), "chapters": plan.get("chapters", [])}


def edit_beat(ep: Episode, i: int, change: dict) -> dict:
    """The owner's hand on one card: a note for the assistant, new words on screen, or remove it (the time goes to
    the scene before, as his face)."""
    plan = json.loads(ep.plan.read_text(encoding="utf-8"))
    beats = plan["beats"]
    if not 0 <= i < len(beats):
        raise ValueError("المشهد مو موجود")
    if "split" in change:   # the timeline's blade: one scene becomes two at this moment (plan time)
        t = float(change["split"])
        b = beats[i]
        if not b["start"] + 0.5 <= t <= b["end"] - 0.5:
            raise ValueError("القص لازم يكون نص ثانية أبعد من حافة المشهد")
        second = {k: v for k, v in b.items() if k in ("zone", "kind", "query", "caption", "source", "grade")}
        second.update(start=round(t, 3), end=b["end"])
        if second["kind"].startswith("face") and second["kind"] != "face_zoom_in":
            second["kind"] = "face_zoom_in"
        b["end"] = round(t, 3)
        beats.insert(i + 1, second)
    elif "edge" in change:   # trim: move the border between this scene and the next
        t = float(change["edge"])
        if i + 1 >= len(beats) or not beats[i]["start"] + 0.5 <= t <= beats[i + 1]["end"] - 0.5:
            raise ValueError("الحافة لازم تبقى بين المشهدين")
        beats[i]["end"] = beats[i + 1]["start"] = round(t, 3)
    elif change.get("remove"):
        b = beats.pop(i)
        if beats:
            j = max(0, i - 1)
            if j < len(beats):
                if j == i - 1:
                    beats[j]["end"] = b["end"]
                else:
                    beats[j]["start"] = b["start"]
    elif "insert" in change:   # text from the app's text panel: a short scene of its own at the playhead
        ins = change["insert"]
        t, dur = float(ins.get("t", beats[i]["start"])), max(1.5, min(8.0, float(ins.get("dur", 3))))
        b = beats[i]
        t = max(b["start"], min(t, b["end"] - 1.0))
        end = min(b["end"], t + dur)
        new = {"start": round(t, 3), "end": round(end, 3), "zone": b["zone"], **_text_scene(ins)}
        pieces = []
        if t - b["start"] >= 0.5:
            pieces.append({**b, "end": round(t, 3)})
        pieces.append(new)
        if b["end"] - end >= 0.5:
            rest = {k: v for k, v in b.items() if k in ("zone", "kind", "query", "caption", "source", "grade", "effect")}
            pieces.append({**rest, "start": round(end, 3), "end": b["end"]})
        else:
            new["end"] = b["end"]
        beats[i:i + 1] = pieces
    elif "sticker" in change:   # the stickers panel: on his face it becomes a face scene that can carry them
        st = change["sticker"]
        if st.get("remove") is not None:
            sts = beats[i].get("stickers") or []
            del sts[int(st["remove"])]
            beats[i]["stickers"] = sts or None
        else:
            if beats[i]["kind"] not in MARKABLE:
                beats[i]["kind"], beats[i]["fx"] = "face_fx", "none"
            at = max(0.2, min(float(st.get("at", 0.3)), beats[i]["end"] - beats[i]["start"] - 0.5))
            item = {"type": st.get("type", "stamp"), "at": round(at, 2), **({"text": st["text"]} if st.get("text") else {})}
            beats[i]["stickers"] = (beats[i].get("stickers") or []) + [item]
    elif "media" in change:   # his own picture or clip on this scene
        src = ep.edit / "media" / Path(str(change["media"])).name
        if not src.exists():
            raise ValueError("الملف مو موجود بمواد الحلقة")
        for old in list(ep.assets.glob(f"img_{i}.*")) + list(ep.assets.glob(f"footage_{i}.*")):
            old.unlink()
        ep.assets.mkdir(parents=True, exist_ok=True)
        if src.suffix.lower() in VIDEO_EXT:
            import shutil
            shutil.copyfile(src, ep.assets / f"footage_{i}.mp4")
            beats[i].update(kind="footage", query="own footage", pick={"local": True})
            (ep.assets / f"footage_{i}.json").write_text(json.dumps({"query": "own footage", "credit": "من تصويرك"}), encoding="utf-8")
        else:
            import shutil
            shutil.copyfile(src, ep.assets / f"img_{i}{src.suffix.lower()}")
            beats[i].update(kind="image", query=beats[i].get("query") or "own picture", pick={"local": True})
            beats[i].setdefault("caption", src.stem)
    elif "cutout" in change:   # his background removed for this scene: paper world behind him, or a word
        mode = change["cutout"]
        b = beats[i]
        if mode == "split":   # him on one half, a picture on the other
            q = str(change.get("query") or b.get("query") or "").strip()
            if not q or q in ("own footage", "own picture", "chosen picture", "chosen footage"):
                raise ValueError("اكتب بخانة «اقترح بدائل» شنو الصورة الي تطلع يمّك")
            b.update(kind="face_split", query=q)
            b.pop("treatment", None)
            b.pop("pick", None)
            for old in ep.assets.glob(f"img_{i}.*"):
                old.unlink()
        elif mode in ("paper", "title"):
            b.update(kind="face_cutout", treatment=mode)
            if mode == "title":
                b["title"] = str(change.get("title") or b.get("title") or b.get("caption") or "").strip() or None
                if not b["title"]:
                    raise ValueError("اكتب الكلمة الي تطلع ورا ظهرك")
        elif b["kind"] in ("face_cutout", "face_split"):
            b["kind"] = "face"
            b.pop("treatment", None)
    elif "choose" in change:   # one of the suggested pictures or clips (downloaded by suggest_choose)
        c = change["choose"]
        for old in list(ep.assets.glob(f"img_{i}.*")) + list(ep.assets.glob(f"footage_{i}.*")):
            old.unlink()
        if c["kind"] == "video":
            beats[i].update(kind="footage", query=c.get("query") or "chosen footage")
        else:
            beats[i].update(kind="image", query=c.get("query") or beats[i].get("query") or "chosen picture",
                            pick={"local": True, "credit": c.get("credit", "")})
    else:
        for k in ("note", "caption", "query", "title", "effect", "transition", "sfx"):
            if k in change:
                beats[i][k] = str(change[k]).strip() or None
    ep.plan.write_text(json.dumps(plan, ensure_ascii=False, indent=1), encoding="utf-8")
    return storyboard(ep)


VIDEO_EXT = {".mp4", ".mov", ".m4v", ".mkv"}
MEDIA_EXT = VIDEO_EXT | {".jpg", ".jpeg", ".png", ".webp", ".mp3", ".wav", ".m4a"}
MARKABLE = ("face_fx", "image", "ai_image", "graphic", "entity", "footage", "avatar")


def _text_scene(ins: dict) -> dict:
    text = str(ins.get("text", "")).strip() or "عنوان"
    style = ins.get("style", "title")
    if style == "title":
        return {"kind": "cinematic_title", "title": text, "caption": text}
    if style == "words":
        return {"kind": "kinetic", "caption": text}
    return {"kind": "graphic", "caption": text, "graphic": {"type": "text", "text": text}}


# ---------- the episode's own media (photos, clips, sounds he brings) ----------

def media_list(ep: Episode) -> list[dict]:
    folder = ep.edit / "media"
    if not folder.exists():
        return []
    out, notes = [], media_notes(ep)
    for f in sorted(folder.iterdir()):
        if f.suffix.lower() not in MEDIA_EXT or f.name.startswith("."):
            continue
        kind = "video" if f.suffix.lower() in VIDEO_EXT else "audio" if f.suffix.lower() in {".mp3", ".wav", ".m4a"} else "image"
        thumb = f if kind == "image" else ep.work / "app" / "media" / (f.stem + ".jpg")
        if kind == "video" and not thumb.exists():
            thumb.parent.mkdir(parents=True, exist_ok=True)
            _ff(["-ss", "0.5", "-i", str(f), "-frames:v", "1", "-vf", "scale=-2:180", str(thumb)])
        n = notes.get(f.name) or {}
        out.append({"name": f.name, "kind": kind, "size": f.stat().st_size, "note": n.get("note", ""), "use": n.get("use", ""),
                    "thumb": str(thumb.relative_to(ep.root)) if kind != "audio" and thumb.exists() else None})
    return out


def ai_variants(ep: Episode, i: int) -> list[dict]:
    """The versions the generator made for one AI scene (ai_<i>.* is the one in use, ai_<i>_v2… the others)."""
    out = []
    for f in sorted(ep.assets.glob(f"ai_{i}.*")) + sorted(ep.assets.glob(f"ai_{i}_v*.*")):
        out.append({"name": f.name, "video": f.suffix.lower() in VIDEO_EXT, "used": f.stem == f"ai_{i}",
                    "path": str(f.relative_to(ep.root))})
    return out


def ai_choose(ep: Episode, i: int, name: str) -> list[dict]:
    """Swap a version in: the chosen file becomes ai_<i>, the old one keeps its place among the versions."""
    pick = ep.assets / Path(name).name
    if not pick.is_file() or not pick.stem.startswith(f"ai_{i}_v"):
        return ai_variants(ep, i)
    cur = next(iter(sorted(ep.assets.glob(f"ai_{i}.*"))), None)
    tmp = ep.assets / f"ai_{i}_swap{pick.suffix}"
    pick.rename(tmp)
    if cur:
        cur.rename(ep.assets / f"{pick.stem}{cur.suffix}")
    tmp.rename(ep.assets / f"ai_{i}{pick.suffix}")
    return ai_variants(ep, i)


def media_notes(ep: Episode) -> dict:
    try:
        return json.loads((ep.edit / "media" / ".notes.json").read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}


def media_note(ep: Episode, name: str, note: str | None = None, use: str | None = None) -> list[dict]:
    """What he wants done with one of his files (owner, 2026-10-25: "انطيها للذكاء الاصطناعي، أگله هاي الصورة خليها
    بطريقة احترافية… هاي الموسيقى مشتريها، خليها بالفيديو"). `use`: "" | "auto" (the assistant places it) | "music"
    (an audio file becomes the episode's music)."""
    f = ep.edit / "media" / Path(name).name
    if not f.is_file():
        raise ValueError("هذا الملف مو موجود")
    notes = media_notes(ep)
    cur = notes.get(f.name) or {}
    if note is not None:
        cur["note"] = str(note).strip()[:600]
    if use is not None:
        cur["use"] = use if use in ("", "auto", "music") else ""
    notes[f.name] = cur
    if use == "music":   # one music for the episode: his
        for k, v in notes.items():
            if k != f.name and v.get("use") == "music":
                v["use"] = ""
    (ep.edit / "media" / ".notes.json").write_text(json.dumps(notes, ensure_ascii=False, indent=1), encoding="utf-8")
    snd_f = ep.edit / "sound.json"
    try:
        snd = json.loads(snd_f.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        snd = {}
    if use == "music":
        snd["music"] = "own:" + f.name
    elif use is not None and snd.get("music") == "own:" + f.name:
        snd["music"] = "auto"
    snd_f.write_text(json.dumps(snd, ensure_ascii=False, indent=1), encoding="utf-8")
    return media_list(ep)


def media_for_assistant(ep: Episode) -> list[str]:
    """Lines for the plan/chat prompts: his files and what he wants done with each."""
    out = []
    for m in media_list(ep):
        if m["use"] == "music":
            out.append(f"  - «{m['name']}» (صوت): موسيقى الحلقة كلها (محطوطة لحالها، لا تحط plan.music).")
        elif m["use"] == "auto" or m["note"]:
            kind = {"image": "صورة", "video": "فيديو", "audio": "صوت"}[m["kind"]]
            how = 'مشهد image بـ pick: {"local": true, "file": "' + m["name"] + '"}' if m["kind"] == "image" else \
                  'مشهد footage بـ pick: {"local": true, "file": "' + m["name"] + '"}' if m["kind"] == "video" else 'sfx أو موسيقى'
            out.append(f"  - «{m['name']}» ({kind}): {m['note'] or 'حطه بأنسب مكان'} → {how}، بأنسب لحظة بالكلام وبشكل احترافي.")
    return out


def apply_own_media(ep: Episode) -> int:
    """After the assistant planned: scenes that point to one of his files get that file as their picture/clip."""
    import shutil
    if not ep.plan.exists():
        return 0
    plan = json.loads(ep.plan.read_text(encoding="utf-8"))
    n = 0
    for i, b in enumerate(plan.get("beats", [])):
        name = (b.get("pick") or {}).get("file")
        src = ep.edit / "media" / Path(name).name if name else None
        if not src or not src.is_file():
            continue
        ep.assets.mkdir(parents=True, exist_ok=True)
        for old in list(ep.assets.glob(f"img_{i}.*")) + list(ep.assets.glob(f"footage_{i}.*")):
            old.unlink()
        if src.suffix.lower() in VIDEO_EXT:
            shutil.copyfile(src, ep.assets / f"footage_{i}.mp4")
            (ep.assets / f"footage_{i}.json").write_text(json.dumps({"query": "own footage", "credit": "من ملفاتك"}), encoding="utf-8")
            b["kind"] = "footage"
        else:
            shutil.copyfile(src, ep.assets / f"img_{i}{src.suffix.lower()}")
            if b.get("kind") != "face_split":
                b["kind"] = "image"
        b.setdefault("query", "own picture")
        b["pick"] = {"local": True, "file": src.name, "credit": "من ملفاتك"}
        n += 1
    ep.plan.write_text(json.dumps(plan, ensure_ascii=False, indent=1), encoding="utf-8")
    return n


def media_add(ep: Episode, path: str) -> list[dict]:
    import shutil
    src = Path(path).expanduser()
    if not src.is_file() or src.suffix.lower() not in MEDIA_EXT:
        raise ValueError("هذا مو صورة ولا فيديو ولا صوت")
    folder = ep.edit / "media"
    folder.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(src, folder / src.name)
    return media_list(ep)


# ---------- suggestions: pictures and clips he chooses from ----------

def suggest(query: str, kind: str = "image", n: int = 8) -> list[dict]:
    import requests
    from editor.pipeline.sources import find
    from editor.pipeline.suite import _small
    errors = []
    found = find(query, "video" if kind == "video" else "image", None, requests.Session(), set(), errors)[:n]
    return [{"kind": kind, "query": query, "provider": f.provider, "title": f.title, "url": f.url,
             "thumb": _small(f.url) if kind != "video" else f.url, "license": f.license, "artist": f.artist,
             "page": f.page, "width": f.width, "height": f.height, "duration": f.duration,
             "credit": f"{f.title} — {f.artist} — {f.license} — {f.page}"} for f in found]


def suggest_choose(ep: Episode, i: int, cand: dict) -> dict:
    """Download the one he picked onto scene `i`, then the plan points to it."""
    import requests
    from editor.pipeline.sources import Found, download
    fields = Found.__dataclass_fields__
    if not str(cand.get("url", "")).startswith("http"):
        raise ValueError("هذا الاختيار ما بيه رابط")
    base = {"provider": "", "title": "", "width": 0, "height": 0, "license": "", "artist": "", "page": ""}
    data = download(Found(**{k: v for k, v in {**base, **cand}.items() if k in fields}), requests.Session())
    for old in list(ep.assets.glob(f"img_{i}.*")) + list(ep.assets.glob(f"footage_{i}.*")):
        old.unlink()
    ep.assets.mkdir(parents=True, exist_ok=True)
    if cand.get("kind") == "video":
        (ep.assets / f"footage_{i}.mp4").write_bytes(data)
        (ep.assets / f"footage_{i}.json").write_text(json.dumps({"query": cand.get("query") or "chosen footage",
                                                                "credit": cand.get("credit", "")}), encoding="utf-8")
    else:
        ext = Path(cand["url"].split("?")[0]).suffix.lower()
        (ep.assets / f"img_{i}{ext if ext in ('.jpg', '.jpeg', '.png', '.webp') else '.jpg'}").write_bytes(data)
    plan = json.loads(ep.plan.read_text(encoding="utf-8"))
    b = plan["beats"][i]
    if cand.get("kind") == "video":
        b.update(kind="footage", query=cand.get("query") or "chosen footage")
    else:
        b.update(kind="image", query=cand.get("query") or b.get("query") or "chosen picture",
                 pick={"local": True, "credit": cand.get("credit", "")})
    ep.plan.write_text(json.dumps(plan, ensure_ascii=False, indent=1), encoding="utf-8")
    return storyboard(ep)


# ---------- the effects library ----------

def effect_thumbs(ep: Episode) -> dict:
    """One small picture per effect, of his own footage (the effects panel)."""
    from types import SimpleNamespace
    from editor.pipeline.compose import effect_filter
    from editor.pipeline.plan import EFFECTS
    video = ep.clean_video if ep.clean_video.exists() else ep.source
    out = ep.work / "app" / "fx"
    out.mkdir(parents=True, exist_ok=True)
    frame = out / "frame.png"
    if not frame.exists() and video.exists():
        _ff(["-ss", f"{_duration(video) * 0.4:.2f}", "-i", str(video), "-frames:v", "1", "-vf", "scale=-2:200", str(frame)])
    res = {}
    for e in EFFECTS:
        jpg = out / f"{e}.jpg"
        if not jpg.exists() and frame.exists():
            cv = SimpleNamespace(width=356, height=200)
            chain = "scale=356:200,setsar=1,loop=loop=12:size=1" + effect_filter(e, cv)
            _ff(["-i", str(frame), "-vf", chain, "-vframes", "1", "-ss", "0.2", "-q:v", "4", str(jpg)])
            if not jpg.exists():   # filters that need time (flash, shake): a still from the first frame
                _ff(["-i", str(frame), "-vf", "scale=356:200,setsar=1" + effect_filter(e, cv), "-frames:v", "1", "-q:v", "4", str(jpg)])
        res[e] = {"name": EFFECT_NAMES.get(e, e), "img": str(jpg.relative_to(ep.root)) if jpg.exists() else None}
    return res


EFFECT_NAMES = {"xray": "أشعة إكس", "glow": "توهّج", "slow_push": "تقريب بطيء", "letterbox": "أشرطة سينما",
                "sepia": "بني قديم", "warm": "دافي", "cold": "بارد", "spotlight": "بقعة ضوء", "pixel_in": "دخول بكسلات",
                "blur_in": "دخول ضبابي", "punchy": "ألوان قوية", "dreamy_glow": "توهّج حالم", "shake": "اهتزاز", "vhs": "شريط قديم", "retro_shake": "قديم ويهتز", "bw": "أبيض وأسود", "night": "ليل مخيف",
                "dream": "حلم", "rgb_split": "انقسام ألوان", "flash_in": "دخول بوميض", "sharpen": "حدّة", "film": "فلم سينما"}


# ---------- undo / redo (the plan, colours, sound, cuts) ----------

UNDO_FILES = ("edit_plan.json", "look.json", "sound.json", "cuts_override.json", "clean_words.json")


def snapshot(ep: Episode) -> None:
    """Keep the editable files as they are now, before a change (50 steps back)."""
    import shutil
    hist = ep.work / "app" / "undo"
    stamp = f"{len(list(hist.glob('*'))) if hist.exists() else 0:05d}"
    d = hist / stamp
    d.mkdir(parents=True, exist_ok=True)
    for name in UNDO_FILES:
        f = ep.edit / name
        if f.exists():
            shutil.copyfile(f, d / name)
    (ep.work / "app" / "redo").exists() and shutil.rmtree(ep.work / "app" / "redo")
    for old in sorted(hist.iterdir())[:-50]:
        shutil.rmtree(old)


def _restore(ep: Episode, frm: str, to: str) -> bool:
    import shutil
    src = ep.work / "app" / frm
    if not src.exists() or not any(src.iterdir()):
        return False
    last = sorted(src.iterdir())[-1]
    keep = ep.work / "app" / to / f"{len(list((ep.work / 'app' / to).glob('*'))) if (ep.work / 'app' / to).exists() else 0:05d}"
    keep.mkdir(parents=True, exist_ok=True)
    for name in UNDO_FILES:
        cur = ep.edit / name
        if cur.exists():
            shutil.copyfile(cur, keep / name)
        if (last / name).exists():
            shutil.copyfile(last / name, cur)
        elif cur.exists() and name != "clean_words.json":
            cur.unlink()
    shutil.rmtree(last)
    return True


# ---------- versions (owner, 2026-10-25: "مثل الطبقات… أختار هاي الطبقة الي أريد أشتغل عليها") ----------
# A whole version of the episode: its editable files plus the preview it built, kept side by side. He watches any
# of them and picks one to keep working on; the current state is kept as a version first, so nothing is lost.

VERSION_FILES = UNDO_FILES + ("style.txt", "options.json", "idea.txt", "captions_en.json")
KEEP_AUTO = 8


def _vdir(ep: Episode) -> Path:
    return ep.edit / "versions"


def save_version(ep: Episode, name: str = "", auto: bool = False) -> dict:
    import shutil
    import time
    root = _vdir(ep)
    root.mkdir(parents=True, exist_ok=True)
    n = max([int(p.name) for p in root.iterdir() if p.name.isdigit()] or [0]) + 1
    d = root / f"{n:03d}"
    d.mkdir()
    for f in VERSION_FILES:
        if (ep.edit / f).exists():
            shutil.copyfile(ep.edit / f, d / f)
    prev = ep.edit / "preview.mp4"
    if prev.exists():
        shutil.copyfile(prev, d / "preview.mp4")   # a real copy: a hard link would be overwritten by the next build
        _ff(["-ss", "3", "-i", str(prev), "-frames:v", "1", "-vf", "scale=320:-2", str(d / "cover.jpg")])
    style = (ep.edit / "style.txt").read_text(encoding="utf-8").strip() if (ep.edit / "style.txt").exists() else ""
    if not style and ep.plan.exists():
        style = (json.loads(ep.plan.read_text(encoding="utf-8")).get("style") or {}).get("primary", "")
    meta = {"n": n, "name": name or f"النسخة {n}", "at": time.time(), "style": style, "auto": auto}
    (d / "meta.json").write_text(json.dumps(meta, ensure_ascii=False), encoding="utf-8")
    autos = sorted(p for p in root.iterdir() if p.name.isdigit() and json.loads((p / "meta.json").read_text(encoding="utf-8")).get("auto"))
    for old in autos[:-KEEP_AUTO]:
        shutil.rmtree(old, ignore_errors=True)
    return meta


def list_versions(ep: Episode) -> list[dict]:
    root = _vdir(ep)
    out = []
    for d in sorted(root.iterdir(), reverse=True) if root.exists() else []:
        try:
            m = json.loads((d / "meta.json").read_text(encoding="utf-8"))
        except (OSError, ValueError):
            continue
        m["preview"] = str((d / "preview.mp4").relative_to(ep.root)) if (d / "preview.mp4").exists() else None
        m["cover"] = str((d / "cover.jpg").relative_to(ep.root)) if (d / "cover.jpg").exists() else None
        out.append(m)
    return out


def use_version(ep: Episode, n: int) -> list[dict]:
    import shutil
    d = _vdir(ep) / f"{int(n):03d}"
    if not d.is_dir():
        raise ValueError("هاي النسخة مو موجودة")
    snapshot(ep)
    save_version(ep, "قبل ما ترجع للنسخة " + str(int(n)), auto=True)
    for f in VERSION_FILES:
        if (d / f).exists():
            shutil.copyfile(d / f, ep.edit / f)
        elif f in ("captions_en.json", "idea.txt", "style.txt") and (ep.edit / f).exists():
            (ep.edit / f).unlink()
    if (d / "preview.mp4").exists():
        (ep.edit / "preview.mp4").unlink(missing_ok=True)
        shutil.copyfile(d / "preview.mp4", ep.edit / "preview.mp4")
    return list_versions(ep)


def rename_version(ep: Episode, n: int, name: str) -> list[dict]:
    f = _vdir(ep) / f"{int(n):03d}" / "meta.json"
    m = json.loads(f.read_text(encoding="utf-8"))
    m["name"], m["auto"] = str(name).strip()[:60] or m["name"], False   # a named version is never cleaned away
    f.write_text(json.dumps(m, ensure_ascii=False), encoding="utf-8")
    return list_versions(ep)


def delete_version(ep: Episode, n: int) -> list[dict]:
    import shutil
    shutil.rmtree(_vdir(ep) / f"{int(n):03d}", ignore_errors=True)
    return list_versions(ep)


def undo(ep: Episode) -> bool:
    return _restore(ep, "undo", "redo")


def redo(ep: Episode) -> bool:
    return _restore(ep, "redo", "undo")


# ---------- timeline ----------

def filmstrip(ep: Episode, video: Path, n: int = 60) -> str | None:
    """One strip of `n` small frames across the video (the timeline's video track)."""
    out = ep.work / "app" / f"strip_{n}.jpg"
    if out.exists() and out.stat().st_mtime >= video.stat().st_mtime:
        return "edit/work/app/" + out.name
    out.parent.mkdir(parents=True, exist_ok=True)
    dur = _duration(video)
    if dur <= 0:
        return None
    r = _ff(["-i", str(video), "-vf", f"fps={n / dur:.5f},scale=-2:72,tile={n}x1", "-frames:v", "1", "-q:v", "6", str(out)])
    return "edit/work/app/" + out.name if r.returncode == 0 and out.exists() else None


def waveform(video: Path, points: int = 1500) -> list[float]:
    env = loudness(video)
    if not len(env):
        return []
    step = max(1, len(env) // points)
    w = env[: len(env) // step * step].reshape(-1, step).max(axis=1)
    top = float(np.percentile(w, 99)) or 1.0
    return [round(min(1.0, float(v) / top), 3) for v in w]


def timeline(ep: Episode) -> dict:
    """Everything the timeline draws, on the cleaned video (or the raw one before the cut)."""
    video = ep.clean_video if ep.clean_video.exists() else ep.source
    if not video.exists():
        return {"ready": False}
    cache = ep.work / "app" / "timeline.json"
    stamp = f"v3:{video}:{video.stat().st_mtime}:{ep.plan.stat().st_mtime if ep.plan.exists() else 0}"
    if cache.exists():
        d = json.loads(cache.read_text(encoding="utf-8"))
        if d.get("stamp") == stamp:
            return d
    dur = _duration(video)
    wave = waveform(video)
    caps = captions(ep) if video == ep.clean_video else {"lines": []}
    blocks = [{"s": l[0]["s"], "e": l[-1]["e"], "t": " ".join(w["t"] for w in l)} for l in caps.get("lines", []) if l]
    plan = json.loads(ep.plan.read_text(encoding="utf-8")) if ep.plan.exists() else {}
    off = sum(e - s for s, e in plan.get("teaser", []))
    scenes = [{"i": i, "s": round(b["start"] - off, 2), "e": round(b["end"] - off, 2), "kind": b["kind"],
               "face": b["kind"].startswith("face") and b["kind"] != "face_paper", "kind_ar": KIND_AR.get(b["kind"], b["kind"]),
               "label": ar(b.get("title")) or ar(b.get("caption")) or KIND_AR.get(b["kind"], "مشهد"),
               "effect": b.get("effect")}
              for i, b in enumerate(plan.get("beats", []))]
    sounds = [{"s": round(m.get("t", 0) - off, 2), "label": m.get("mood") or "موسيقى"} for m in plan.get("music", [])]
    d = {"ready": True, "stamp": stamp, "offset": off, "video": str(video.relative_to(ep.root)), "duration": round(dur, 2),
         "wave": wave, "wave_hop": round(dur / max(1, len(wave)), 4), "strip": filmstrip(ep, video),
         "captions": blocks, "scenes": scenes, "sounds": sounds, "clean": video == ep.clean_video}
    cache.parent.mkdir(parents=True, exist_ok=True)
    cache.write_text(json.dumps(d, ensure_ascii=False), encoding="utf-8")
    return d
