"""The owner's optional extras from the Mac app (edit/options.json), all off until he turns them on (owner,
2026-10-24: "كلهم اختياري، أني اختارهم أو أشيلهم").

  captions  words burned on the video, reels style: a few words at a time, the one being said lit up
            (styles: pop | clean | box). Arabic is shaped by libass with our own font (editor/fonts: Vazirmatn, OFL; it has the Iraqi letters چ گ پ ڤ).
  pace      who sets the rhythm: "off" (the cutter's normal pauses), or the assistant: calm | normal | fast
            (how much of every pause stays; the plan prompt gets it too, for how long scenes last)
  intro     a short channel opening before the episode (his picture and name, a whoosh)
  outro     the YouTube end screen (plan.end_screen; on by default)

post_process() runs after compose when captions or the intro are on: one extra pass over the final file.
"""
import json
import re
import subprocess
from pathlib import Path

from .media import MediaError, probe
from .paths import Episode

FONTS = Path(__file__).resolve().parents[1] / "fonts"
DEFAULTS = {"captions": {"on": False, "style": "pop", "words": 3}, "pace": "off", "intro": False, "outro": True}
PACE = {"calm": (0.7, 0.18), "normal": (0.45, 0.12), "fast": (0.28, 0.07)}   # (longest pause kept, breath at a cut)
INTRO_SECONDS = 2.6


def load_options(ep: Episode) -> dict:
    try:
        d = json.loads((ep.edit / "options.json").read_text(encoding="utf-8"))
    except (OSError, ValueError):
        d = {}
    out = {**DEFAULTS, **{k: v for k, v in d.items() if k in DEFAULTS}}
    out["captions"] = {**DEFAULTS["captions"], **(d.get("captions") or {})}
    return out


def save_options(ep: Episode, change: dict) -> dict:
    cur = load_options(ep)
    if "captions" in change:
        c = {**cur["captions"], **(change["captions"] or {})}
        c["style"] = c["style"] if c.get("style") in ("pop", "clean", "box") else "pop"
        c["words"] = max(1, min(6, int(c.get("words", 3))))
        c["on"] = bool(c.get("on"))
        cur["captions"] = c
    if change.get("pace") in ("off", "calm", "normal", "fast"):
        cur["pace"] = change["pace"]
    for k in ("intro", "outro"):
        if k in change:
            cur[k] = bool(change[k])
    ep.edit.mkdir(parents=True, exist_ok=True)
    (ep.edit / "options.json").write_text(json.dumps(cur, ensure_ascii=False, indent=1), encoding="utf-8")
    if "outro" in change and ep.plan.exists():   # the end screen lives in the plan
        plan = json.loads(ep.plan.read_text(encoding="utf-8"))
        plan["end_screen"] = 20.0 if cur["outro"] else 0
        ep.plan.write_text(json.dumps(plan, ensure_ascii=False, indent=1), encoding="utf-8")
    return cur


def pace_gaps(ep: Episode) -> tuple[float, float] | None:
    """(max pause, breath) for the cutter when the assistant sets the rhythm; None = the cutter's own."""
    p = load_options(ep)["pace"]
    return PACE.get(p) if p != "off" else None


# ---------- captions on the video ----------

def _ass_time(t: float) -> str:
    t = max(0.0, t)
    return f"{int(t // 3600)}:{int(t % 3600 // 60):02d}:{t % 60:05.2f}"


def _clean(text: str) -> str:
    return re.sub(r"[{}\\]", "", text).strip()


def captions_ass(words: list, offset: float, width: int, height: int, style: str = "pop", per: int = 3,
                 until: float | None = None) -> str:
    """ASS subtitles: `per` words on screen, the spoken one highlighted. `words`: [(text, start, end)] on the
    cleaned timeline; `offset`: where that timeline starts in the final video (the teaser before it)."""
    size = round(height * (0.072 if style == "pop" else 0.055))
    outline = {"pop": max(3, size // 9), "clean": 0, "box": 6}[style]
    shadow = {"pop": 0, "clean": 2, "box": 0}[style]
    border = 3 if style == "box" else 1
    back = "&H99000000" if style == "box" else "&H66000000"
    head = f"""[Script Info]
ScriptType: v4.00+
PlayResX: {width}
PlayResY: {height}
WrapStyle: 2
ScaledBorderAndShadow: yes

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Cap,Vazirmatn,{size},&H00FFFFFF,&H00FFFFFF,&H00000000,{back},-1,0,0,0,100,100,0,0,{border},{outline},{shadow},2,{round(width * 0.08)},{round(width * 0.08)},{round(height * 0.11)},178

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""
    lit = "{\\c&H4CD2FF&" + ("\\fscx110\\fscy110" if style == "pop" else "") + "}"
    lines = []
    clean_words = [(_clean(t), s, e) for t, s, e in words if _clean(t)]
    for g in range(0, len(clean_words), per):
        group = clean_words[g:g + per]
        for k, (text, s, e) in enumerate(group):
            nxt = group[k + 1][1] if k + 1 < len(group) else min(e + 0.35, clean_words[g + per][1] if g + per < len(clean_words) else e + 0.35)
            start, end = s + offset, max(nxt, e) + offset
            if until is not None and start >= until:
                break
            # libass lays tagged runs out left to right and merges look-alike neighbours: every word gets its own run
            # (a different, invisible outline shade) and the runs go in reverse, so Arabic reads right to left
            runs = [(lit[:-1] if j == k else "{\\c&HFFFFFF&\\fscx100\\fscy100") + f"\\3c&H00000{j % 10}&}}" + w for j, (w, _, _) in enumerate(group)]
            shown = " ".join(reversed(runs))
            lines.append(f"Dialogue: 0,{_ass_time(start)},{_ass_time(min(end, until) if until else end)},Cap,,0,0,0,,{shown}")
    return head + "\n".join(lines) + "\n"


# ---------- the channel opening ----------

def _channel_title() -> str:
    from .channel import load_channel
    name = load_channel()["name"]
    parts = [p.strip() for p in name.split("•")]
    arabic = [p for p in parts if re.search(r"[؀-ۿ]", p)]
    return arabic[0] if arabic else parts[-1]


def intro_clip(ep: Episode, width: int, height: int, fps: int, out: Path) -> Path:
    """2.6 s: his channel picture grows in a ring of light, his name fades in, a whoosh and a soft hit."""
    from .channel import channel_avatar
    from .sfx import sfx_path
    avatar = channel_avatar(ep.work)
    ass = out.with_suffix(".ass")
    size = round(height * 0.075)
    ass.write_text(f"""[Script Info]
ScriptType: v4.00+
PlayResX: {width}
PlayResY: {height}

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: T,Vazirmatn,{size},&H00F0F3F4,&H00F0F3F4,&H00000000,&H00000000,-1,0,0,0,100,100,0,0,1,0,0,2,0,0,{round(height * 0.2)},178

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
Dialogue: 0,0:00:00.70,0:00:02.60,T,,0,0,0,,{{\\fad(350,250)\\fscx92\\fscy92\\t(0,600,\\fscx100\\fscy100)}}{_clean(_channel_title())}
""", encoding="utf-8")
    d = INTRO_SECONDS
    a = round(height * 0.3) // 2 * 2
    graph = (f"color=c=0x0B0B0D:s={width}x{height}:r={fps}:d={d},format=rgba[bg];"
             f"[1:v]scale={a}:{a},format=rgba,geq=r='r(X,Y)':g='g(X,Y)':b='b(X,Y)':a='if(lte(hypot(X-W/2,Y-H/2),W/2-1),255,0)',"
             f"fade=t=in:st=0.1:d=0.45:alpha=1,fade=t=out:st={d - 0.3}:d=0.3:alpha=1[av];"
             f"[bg][av]overlay=(W-w)/2:(H-h)/2-{round(height * 0.06)}:format=auto,"
             f"ass=filename='{ass}':fontsdir='{FONTS}':shaping=complex,fade=t=out:st={d - 0.25}:d=0.25,format=yuv420p[v];"
             f"[2:a]adelay=80|80[w];[3:a]adelay=650|650,volume=0.6[h];[w][h]amix=inputs=2:normalize=0,apad,atrim=0:{d},"
             f"aformat=sample_rates=48000:channel_layouts=stereo[a]")
    inputs = ["-f", "lavfi", "-i", "anullsrc=r=48000:cl=stereo", "-loop", "1", "-t", str(d),
              "-i", str(avatar) if avatar else str(FONTS / "OFL.txt")]
    if not avatar:   # no picture: a ring of the accent colour instead
        inputs[-1] = "color=c=0xF2C94C:s=64x64"
        inputs[-2:-2] = ["-f", "lavfi"]
    inputs += ["-i", str(sfx_path("whoosh")), "-i", str(sfx_path("hit"))]
    gfile = out.with_suffix(".graph")
    gfile.write_text(graph, encoding="utf-8")
    from .media import filter_script, run_ffmpeg
    run_ffmpeg([*inputs, *filter_script(gfile), "-map", "[v]", "-map", "[a]", "-t", str(d), "-c:v", "libx264", "-crf", "16",
                "-preset", "veryfast", "-c:a", "aac", "-b:a", "320k", str(out)])
    return out


# ---------- the extra pass ----------

def post_process(ep: Episode, final: Path, teaser_total: float) -> Path:
    """Captions on the video and/or the opening, in one pass over the final file (only when he turned them on)."""
    from .media import filter_script, run_ffmpeg
    from .transcribe import load_words
    opts = load_options(ep)
    caps, intro = opts["captions"]["on"], opts["intro"]
    if not (caps or intro):
        return final
    info = probe(final)
    work = ep.work / "post"
    work.mkdir(parents=True, exist_ok=True)
    chain = "[0:v]null"
    if caps and ep.clean_words.exists():
        words = [(w.text, w.start, w.end) for w in load_words(ep.clean_words)]
        ass = work / "captions.ass"
        ass.write_text(captions_ass(words, teaser_total, info.width, info.height, opts["captions"]["style"],
                                    opts["captions"]["words"], until=info.duration), encoding="utf-8")
        chain = f"[0:v]ass=filename='{ass}':fontsdir='{FONTS}':shaping=complex"
    inputs = ["-i", str(final)]
    if intro:
        clip = intro_clip(ep, info.width, info.height, round(info.fps or 30), work / "intro.mp4")
        inputs += ["-i", str(clip)]
        graph = f"{chain}[main];[1:v][1:a][main][0:a]concat=n=2:v=1:a=1[v][a]"
    else:
        graph = f"{chain}[v];[0:a]anull[a]"
    gfile = work / "post.graph"
    gfile.write_text(graph, encoding="utf-8")
    out = final.with_name(final.stem + ".post.mp4")
    print("✍️  " + "، ".join(x for x in ("الكابشن على الفيديو" if caps else "", "البداية الجاهزة" if intro else "") if x) + "…", flush=True)
    run_ffmpeg([*inputs, *filter_script(gfile), "-map", "[v]", "-map", "[a]", "-c:v", "libx264", "-crf", "16", "-preset", "veryfast",
                "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "320k", "-movflags", "+faststart", str(out)])
    final.replace(work / "master_clean.mp4")   # kept for the reels (they get their own tall captions)
    out.replace(final)
    if intro:   # YouTube chapters move by the opening's length
        ch = ep.edit / "chapters.txt"
        ch.exists() and ch.write_text(_shift_chapters(ch.read_text(encoding="utf-8"), INTRO_SECONDS), encoding="utf-8")
    return final


def _shift_chapters(text: str, by: float) -> str:
    def shift(m):
        parts = [int(x) for x in m.group(1).split(":")]
        secs = sum(v * 60 ** i for i, v in enumerate(reversed(parts)))
        if secs == 0:
            return m.group(0)
        secs = int(secs + by)
        return (f"{secs // 3600}:{secs % 3600 // 60:02d}:{secs % 60:02d}" if secs >= 3600 else f"{secs // 60}:{secs % 60:02d}") + m.group(2)
    return re.sub(r"^(\d+(?::\d\d){1,2})(\s)", shift, text, flags=re.M)
