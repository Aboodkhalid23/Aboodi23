"""Free music and sound effects (owner's choice: no credits spent on sound). Both come from Openverse,
which gathers openly licensed audio:

  music          Jamendo / ccMixter / Wikimedia tracks under CC BY or CC0 (CC BY needs the credit line, which
                 goes in the video description with the picture credits). No share-alike, no non-commercial.
  sound effects  Freesound recordings under CC0 only, so they need no credit and can live in the shared library
                 (editor/sfx/library/<name>/) for every episode.

`music-free` fills each music cue of the plan (or one bed for the whole episode); Artlist is only for a cue
that nothing free fits, and only when the owner allows the credits."""
import json
from dataclasses import dataclass
from pathlib import Path

import requests

from .media import MediaError
from .paths import Episode

API = "https://api.openverse.org/v1/audio/"
HEADERS = {"User-Agent": "Aboodi23-editor/0.1 (github.com/Aboodkhalid23/Aboodi23)"}
MIN_TRACK, MAX_TRACK = 90.0, 480.0          # seconds: long enough to loop gently, short enough to download
FILM_GENRES = ("filmscore", "soundtrack", "ambient", "cinematic", "classical", "instrumental", "piano", "electronic")
VOCAL_WORDS = ("vocal", "song", "rap", "feat", "remix", "lyrics", "singer")
FALLBACK_QUERIES = ("cinematic", "documentary", "ambient", "piano", "suspense")


@dataclass
class Track:
    title: str
    url: str
    seconds: float
    license: str
    creator: str
    page: str
    genres: tuple

    @property
    def credit(self) -> str:
        return f"Music: {self.title} — {self.creator} — {self.license} — {self.page}"


def search(q: str, session, category: str | None = "music", licenses: str = "cc0,by", source: str | None = None,
           size: int = 20) -> list[dict]:
    params = {"q": q, "license": licenses, "page_size": size}
    if category:
        params["category"] = category
    if source:
        params["source"] = source
    r = session.get(API, params=params, headers=HEADERS, timeout=45)
    r.raise_for_status()
    return r.json().get("results", [])


def _track(r: dict) -> Track:
    lic = "CC0" if r.get("license") == "cc0" else f"CC {r.get('license', '').upper()} {r.get('license_version') or ''}".strip()
    return Track(r.get("title") or "?", r["url"], (r.get("duration") or 0) / 1000, lic, r.get("creator") or "",
                 r.get("foreign_landing_url") or "", tuple(g.lower() for g in r.get("genres") or ()))


def score(t: Track) -> float:
    s = 1.0 if any(g in FILM_GENRES for g in t.genres) else 0.0
    s += 0.3 if t.license == "CC0" else 0.0                       # no credit line needed
    s -= 2.0 if any(w in t.title.lower() for w in VOCAL_WORDS) else 0.0
    s -= 0.5 if t.seconds > 300 else 0.0
    return s


def find_tracks(queries, session, used=frozenset()) -> list[Track]:
    """Instrumental-looking tracks of a usable length for the first query that has any, best first."""
    for q in [q for q in queries if q]:
        try:
            found = [_track(r) for r in search(q, session)]
        except (requests.RequestException, ValueError, KeyError):
            continue
        found = [t for t in found if MIN_TRACK <= t.seconds <= MAX_TRACK and t.url not in used]
        if found:
            return sorted(found, key=score, reverse=True)
    return []


def _download(url: str, out: Path, session) -> Path:
    from .music import audio_duration
    r = session.get(url, headers=HEADERS, timeout=180)
    r.raise_for_status()
    out.write_bytes(r.content)
    try:
        audio_duration(out)
    except MediaError:
        out.unlink(missing_ok=True)
        raise
    return out


def _cue_queries(m: dict, mood: str) -> list[str]:
    words = f"{m.get('mood', '')} {m.get('genre', '')}".replace("auto", "").strip()
    # catalogue search is literal: the full phrase first, then its single words, then safe film-score words
    return [m.get("search", ""), words, *words.split(), m.get("genre", ""), *mood.split(",")[:1], *FALLBACK_QUERIES]


def free_music(ep: Episode, total: float, session=None) -> list[str]:
    """Download a free track for every music cue still empty (assets/music_<k>.mp3), or one bed
    (assets/music.mp3) when the plan names no cues. Returns the cues nothing free was found for."""
    from .music import AUDIO_EXT, music_asset, segments
    from .plan import load_plan
    from .styles import load_style
    session = session or requests.Session()
    plan = load_plan(ep.plan)
    mood = load_style(plan.style["primary"]).music_mood or ""
    credits_file = ep.work / "music_credits.json"
    credits = json.loads(credits_file.read_text(encoding="utf-8")) if credits_file.exists() else {}
    used = {c["url"] for c in credits.values()}
    wanted = [(str(k), music_asset(ep, k), ep.assets / f"music_{k}.mp3", plan.music[k])
              for k, _, _ in segments(plan, total)]
    if not plan.music:
        have = next((p for p in sorted(ep.assets.glob("music.*")) if p.suffix.lower() in AUDIO_EXT), None)
        wanted = [("bed", have, ep.assets / "music.mp3", {})]
    missing = []
    for key, have, out, m in wanted:
        if have:
            continue
        for t in find_tracks(_cue_queries(m, mood), session, used)[:3]:
            try:
                _download(t.url, out, session)
            except (requests.RequestException, MediaError):
                continue
            credits[key] = {"url": t.url, "credit": t.credit}
            used.add(t.url)
            break
        else:
            missing.append(key)
    credits_file.write_text(json.dumps(credits, ensure_ascii=False, indent=1), encoding="utf-8")
    return missing


def fetch_sfx(name: str, library: Path, session=None, takes: int = 3) -> list[Path]:
    """CC0 recordings of `name` (e.g. "typewriter", "camera_shutter") from Freesound into the shared library."""
    session = session or requests.Session()
    folder = library / name
    try:
        results = search(name.replace("_", " "), session, category=None, licenses="cc0", source="freesound")
    except (requests.RequestException, ValueError):
        return []
    results = [r for r in results if 0.1 <= (r.get("duration") or 0) / 1000 <= 6]   # effects, not ambiences
    got = []
    for r in results[:takes]:
        folder.mkdir(parents=True, exist_ok=True)
        out = folder / f"freesound_{str(r.get('id', len(got)))[:8]}.mp3"
        try:
            got.append(out if out.exists() else _download(r["url"], out, session))
        except (requests.RequestException, MediaError, KeyError):
            continue
    if got:
        (folder / "SOURCE.txt").write_text("Freesound (via Openverse), CC0 — no attribution required\n" +
                                           "".join(f"{r.get('title')} — {r.get('foreign_landing_url')}\n" for r in results[:takes]),
                                           encoding="utf-8")
    return got
