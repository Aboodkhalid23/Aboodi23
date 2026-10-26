"""Arabic dialects for hearing, cutting and correcting (owner, 2026-10-26: "عراقي، فصيح، أردني، سعودي، قطري…").

Whisper hears every Arabic with one language code ("ar"); what makes it write each dialect the way it was said is the
example sentence it is given (initial prompt): it copies that spelling. So the app finds out which dialect he speaks
(from his script, or from the first pieces of talk), then reads the whole talk with that dialect's example, and tells
the assistant which dialect to keep when it corrects words. He can also pick it himself in the settings.
"""
import json
import re
from pathlib import Path

# example sentences in each dialect's own spelling, with the hesitations he really makes (Whisper copies the style)
DIALECTS = {
    "iraqi": {"name": "عراقي",
              "prompt": "هلا بيكم، اليوم راح نحچي عن قصة غريبة. شلون صار هيچ؟ خلي نشوف شنو الي صار بالضبط.",
              "markers": "شنو شلون هيچ هيج هواية كلش اكو ماكو هسه هسة چان گال يگول اريد ليش شگد وياه ويانه زين بعد خوش لعد شكو اشو اكلك گلت چ گ"},
    "gulf": {"name": "خليجي (سعودي، قطري، كويتي، إماراتي)",
             "prompt": "هلا والله، اليوم بنتكلم عن قصة غريبة. وش صار بالضبط؟ خلنا نشوف الحين ليش صار كذا.",
             "markers": "وش ايش الحين كذا واجد ابغى ابي يبي تبي حيل زين مب مو عشان علشان شلونك يالله وايد ترى خلنا بنتكلم ياخي اللحين"},
    "levant": {"name": "شامي (أردني، فلسطيني، سوري، لبناني)",
               "prompt": "أهلين فيكم، اليوم رح نحكي عن قصة غريبة. شو صار بالزبط؟ خلينا نشوف هلأ ليش صار هيك.",
               "markers": "شو هيك هلأ هلق كتير بدي بدك منيح مش رح عم هاد هاي ليش كمان تبع اشي إشي يعني هون هنيك زلمة"},
    "egypt": {"name": "مصري",
              "prompt": "أهلا بيكم، النهارده هنتكلم عن قصة غريبة. إيه اللي حصل بالظبط؟ تعالوا نشوف دلوقتي ليه حصل كده.",
              "markers": "ايه كده دلوقتي النهارده عايز عاوز اوي قوي مش ازاي ليه بقى خالص كمان احنا انتو هنا ده دي دول بتاع"},
    "msa": {"name": "عربي فصيح",
            "prompt": "مرحباً بكم، سنتحدث اليوم عن قصة غريبة. ماذا حدث بالضبط؟ دعونا نرى لماذا حدث ذلك.",
            "markers": "الذي التي الذين لقد سوف ماذا لماذا كيف هذا هذه ذلك تلك إن ان لكن حيث أيضا ايضا ليس كانت يكون نحن سنتحدث دعونا"},
}
DEFAULT = "iraqi"     # the channel's own voice when nothing tells otherwise
_NORM = str.maketrans({"أ": "ا", "إ": "ا", "آ": "ا", "ى": "ي", "ة": "ه"})


def _tokens(text: str) -> list[str]:
    return re.sub(r"[^\w\s]", " ", text.translate(_NORM)).split()


def detect(text: str) -> str:
    """The dialect of a piece of talk: the one whose everyday words come up most. Formal Arabic wins only when no
    dialect word shows up clearly (an Iraqi speaker uses formal words too)."""
    toks = _tokens(text)
    if not toks:
        return DEFAULT
    letters = set("".join(toks))
    score = {}
    for k, d in DIALECTS.items():
        marks = set(_tokens(d["markers"]))
        score[k] = sum(t in marks for t in toks) + (3 if k == "iraqi" and letters & {"چ", "گ"} else 0)
    spoken = {k: v for k, v in score.items() if k != "msa"}
    best = max(spoken, key=spoken.get)
    if spoken[best] >= 2 and spoken[best] >= score["msa"] * 0.6:
        return best
    return "msa" if score["msa"] >= 3 else (best if spoken[best] else DEFAULT)


def name(key: str) -> str:
    return DIALECTS.get(key, DIALECTS[DEFAULT])["name"]


def prompt(key: str) -> str:
    return DIALECTS.get(key, DIALECTS[DEFAULT])["prompt"]


def saved(edit: Path) -> str | None:
    try:
        return json.loads((Path(edit) / "dialect.json").read_text(encoding="utf-8")).get("dialect")
    except (OSError, ValueError):
        return None


def save(edit: Path, key: str, how: str) -> None:
    (Path(edit) / "dialect.json").write_text(json.dumps({"dialect": key, "how": how}, ensure_ascii=False), encoding="utf-8")


def chosen() -> str:
    """His setting in the app (prefs.json), or "auto"."""
    import os
    home = Path(os.environ.get("MONTIER_HOME") or "")
    try:
        k = json.loads((home / "prefs.json").read_text(encoding="utf-8")).get("dialect", "auto") if str(home) else "auto"
    except (OSError, ValueError):
        k = "auto"
    return k if k in DIALECTS else "auto"
