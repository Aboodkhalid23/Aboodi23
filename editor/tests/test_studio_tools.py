import importlib.util
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def _load(name):
    spec = importlib.util.spec_from_file_location(name, ROOT / "studio" / "tools" / f"{name}.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def test_script_check_catches_fusha_cliches_iraq_and_a_flat_hook(tmp_path):
    sc = _load("script_check")
    bad = tmp_path / "bad.md"
    bad.write_text("في عالم مليء بالأسرار، الذي حدث في العراق كان غريباً. " * 50, encoding="utf-8")
    r = sc.check(bad)
    text = " ".join(r["issues"])
    assert r["score"] < 50 and "قصير" in text and "فصحى" in text and "كليشيهات" in text and "العراق" in text


def test_script_check_likes_iraqi_spoken_script(tmp_path):
    sc = _load("script_check")
    para = ("تخيّل انت عندك 300 مليار دولار ديون؟ شنو تسوي؟ بس هذا مو أغرب شي، راح أگولك بعدين. "
            "سنة 2021 الناس اقتحموا المقر. شوف شلون صارت القصة. وهنا الصدمة الحقيقية بدت. ")
    good = tmp_path / "good.md"
    good.write_text(para * 120, encoding="utf-8")
    r = sc.check(good)
    assert r["score"] >= 85, r["issues"]


def test_prompter_builds_a_page_with_delivery_marks(tmp_path):
    pr = _load("prompter")
    ep = tmp_path / "ep"
    ep.mkdir()
    (ep / "04-script.md").write_text("أول فقرة بالسكربت.\n\nهنا الصدمة الكبيرة يا جماعة.", encoding="utf-8")
    (ep / "08-shoot.md").write_text("- «هنا الصدمة» → وگفة ثانية قبلها\n", encoding="utf-8")
    page = pr.build(ep).read_text(encoding="utf-8")
    assert "وگفة ثانية قبلها" in page and "أول فقرة" in page and "<title>الملقّن</title>" in page
