"""Time expressions: musical, frame-exact times that read like an editor's notes.

    B12          beat 12 (offset + 12 · 60/bpm)            absolute
    S, E         start / end of the shot the expression is in   absolute
    drop         a named cue from the film's "cues"         absolute
    3.95, 3.95s  seconds                                     absolute when alone, a length when added
    1b, 0.5b     beats (a length)
    2f           frames (a length)

    "B12-2f"     two frames before beat 12
    "drop+1b"    one beat after the cue "drop"
    "S+0.25s"    a quarter second into the shot

An *instant* has exactly one absolute term (B…, S, E, a cue, or a bare number); a *length* ("dur") has none.
Everything resolves to seconds on the film's clock.
"""
from __future__ import annotations

import re
from dataclasses import dataclass

_TOKEN = re.compile(r"\s*([+-])?\s*(B-?\d+(?:\.\d+)?|[A-Za-z_][A-Za-z0-9_]*|\d+(?:\.\d+)?(?:[sbf])?)\s*")


class TimeError(ValueError):
    pass


@dataclass(frozen=True)
class Clock:
    bpm: float
    offset: float = 0.0
    fps: float = 24.0

    @property
    def beat(self) -> float:
        return 60.0 / self.bpm


def _terms(expr: str) -> list[tuple[int, str]]:
    s, pos, out = str(expr).strip(), 0, []
    if not s:
        raise TimeError("empty time")
    while pos < len(s):
        m = _TOKEN.match(s, pos)
        if not m or m.end() == pos:
            raise TimeError(f"cannot read {s!r} at {s[pos:]!r}")
        sign = -1 if m.group(1) == "-" else 1
        if out and m.group(1) is None:
            raise TimeError(f"missing + or - before {m.group(2)!r} in {s!r}")
        out.append((sign, m.group(2)))
        pos = m.end()
    return out


def resolve(expr, clock: Clock, cues: dict[str, float] | None = None, shot: tuple[float, float] | None = None,
            length: bool = False) -> float:
    """Seconds for an instant (length=False) or a length (length=True). Numbers are accepted as-is (seconds)."""
    if isinstance(expr, (int, float)):
        return float(expr)
    terms = _terms(expr)
    total, anchors = 0.0, 0
    for sign, tok in terms:
        if tok[0] == "B" and re.fullmatch(r"B-?\d+(?:\.\d+)?", tok):
            total += sign * (clock.offset + float(tok[1:]) * clock.beat)
            anchors += 1
        elif tok in ("S", "E"):
            if shot is None:
                raise TimeError(f"{tok!r} (shot start/end) is only valid inside a shot")
            total += sign * (shot[0] if tok == "S" else shot[1])
            anchors += 1
        elif re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*", tok):
            if not cues or tok not in cues:
                raise TimeError(f"unknown cue {tok!r}" + (f" (cues: {', '.join(sorted(cues))})" if cues else ""))
            total += sign * cues[tok]
            anchors += 1
        else:
            unit = tok[-1] if tok[-1] in "sbf" else ""
            v = float(tok[:-1] if unit else tok)
            total += sign * (v * clock.beat if unit == "b" else v / clock.fps if unit == "f" else v)
            if unit in ("", "s") and not length and len(terms) == 1:
                anchors += 1   # seconds on their own are an absolute time
    if length and anchors:
        raise TimeError(f"{expr!r} is an instant; a length takes only s / b / f terms")
    if not length and anchors != 1:
        raise TimeError(f"{expr!r} needs exactly one anchor (B…, S, E, a cue or a time in seconds), found {anchors}")
    return total
