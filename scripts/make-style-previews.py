"""A real picture for every style in the Styles panel (owner, 2026-10-26: "اريد اسم الستايل والصورة").

Each one is drawn by the same graphics engine that builds the episode: the top shows the style's own way of showing a
photo (one public-domain portrait: Einstein, 1947), the band below its title text on its own paper, colours and fonts.
    python scripts/make-style-previews.py            # only styles without a picture
    python scripts/make-style-previews.py --all      # all again
Writes editor/app/ui/styles/<style>.jpg (~25 KB each).
"""
import sys
from pathlib import Path

from PIL import Image

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from editor.pipeline.graphics import RenderJob, ensure_bundle, render_batch   # noqa: E402
from editor.pipeline.styles import _style_files, load_style                     # noqa: E402

OUT = Path(__file__).resolve().parents[1] / "editor" / "app" / "ui" / "styles"
TMP = Path(__file__).resolve().parents[1] / "editor" / "remotion" / "out" / "style-previews"


def main(redo: bool) -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    TMP.mkdir(parents=True, exist_ok=True)
    jobs = []
    for f in _style_files():
        if not redo and (OUT / f"{f.stem}.jpg").exists():
            continue
        st = load_style(f.stem)
        sp = {"style": {"palette": st.palette, "fonts": st.fonts, "texture": st.texture}, "durationSec": 2}
        jobs.append(RenderJob("image", {**sp, "src": "style-sample.jpg", "treatment": st.image_treatment,
                                        "caption": "ألبرت أينشتاين"}, TMP / f"{f.stem}.png", scale=0.3, still=True, frame=54))
        jobs.append(RenderJob("text", {**sp, "text": "العقل الي غيّر العالم",
                                       "variant": (st.text_variants or ["highlight"])[0]},
                              TMP / f"t-{f.stem}.png", scale=0.3, still=True, frame=54))
    if not jobs:
        print("كل الستايلات عندها صورة")
        return
    for i in range(0, len(jobs), 20):   # one browser per 10 styles, so a failure costs little
        render_batch(jobs[i:i + 20], ensure_bundle())
        for j in jobs[i:i + 20:2]:
            pic, txt = Path(j.out), TMP / f"t-{Path(j.out).name}"
            im, tx = Image.open(pic).convert("RGB"), Image.open(txt).convert("RGB")
            w, h = im.size
            band = tx.crop((0, int(h * 0.30), w, int(h * 0.64)))
            im.paste(band, (0, h - band.size[1]))
            im.save(OUT / f"{pic.stem}.jpg", quality=72, optimize=True)
            pic.unlink()
            txt.unlink()
        print(f"{min(i + 20, len(jobs)) // 2}/{len(jobs) // 2}", flush=True)


if __name__ == "__main__":
    main("--all" in sys.argv)
