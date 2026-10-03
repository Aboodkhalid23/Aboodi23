"""Variety: pictures and text cards rotate through the style's treatments, so no two in a row look alike
(the owner: "don't stick to one look for the whole video")."""
from .plan import EditPlan
from .styles import Style

PICTURE_KINDS = ("image", "ai_image")


def _cycle(options: list[str]):
    i = 0
    last = None
    def nxt() -> str:
        nonlocal i, last
        pick = options[i % len(options)]
        if pick == last and len(options) > 1:
            i += 1
            pick = options[i % len(options)]
        i += 1
        last = pick
        return pick
    def mark(used: str):
        nonlocal last
        last = used
    return nxt, mark


def assign_variety(plan: EditPlan, style: Style) -> EditPlan:
    """Fill in `treatment` (pictures) and `graphic.variant` (text cards) where the plan left them empty.
    Choices the plan made itself are kept, and the rotation steps around them."""
    pic_next, pic_mark = _cycle(style.image_treatments or [style.image_treatment])
    txt_next, txt_mark = _cycle(style.text_variants or ["marker"])
    for b in plan.beats:
        if b.kind in PICTURE_KINDS:
            if b.treatment:
                pic_mark(b.treatment)
            else:
                b.treatment = pic_next()
        elif b.kind == "graphic" and (b.graphic or {}).get("type") == "text":
            if b.graphic.get("variant"):
                txt_mark(b.graphic["variant"])
            else:
                b.graphic["variant"] = txt_next()
    return plan
