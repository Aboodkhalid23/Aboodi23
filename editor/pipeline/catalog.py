"""The catalog of every media source (editor/sources/catalog.json): `python -m editor.pipeline.catalog` writes the
readable list (editor/sources/CATALOG.md); `--check` first asks every source if it is up and records it, so a
source that breaks is noticed (and the pipeline's search simply skips it meanwhile)."""
import json
import sys
from datetime import date
from pathlib import Path

import requests

DIR = Path(__file__).resolve().parent.parent / "sources"
FILE = DIR / "catalog.json"
USE_AR = {"linked": "مربوط تلقائي", "manual": "يدوي", "blocked": "ممنوع"}


def load() -> dict:
    return json.loads(FILE.read_text(encoding="utf-8"))


def check(data: dict) -> dict:
    for s in data["sources"]:
        try:
            code = requests.get(s["check"], timeout=12, headers={"User-Agent": "Aboodi23-editor/0.1"}).status_code
        except requests.RequestException:
            code = 0
        s["status"] = ("up" if 0 < code < 400 else "up (refuses robots or busy)" if code in (401, 403, 405, 429)
                       else f"down ({code or 'no answer'})")
        s["checked"] = date.today().isoformat()
    FILE.write_text(json.dumps(data, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    return data


def markdown(data: dict) -> str:
    rows = ["# مصادر المونتير (صور، فيديو، أرشيف، أنميشن، موسيقى، مؤثرات)", "",
            "يتحدث تلقائياً من `catalog.json`. **مربوط** = المونتير يدوّر بيه لحاله. **يدوي** = Claude يستخدمه باليد. "
            "**ممنوع** = رخصته ما تسمح بقناة بيها أرباح.", "",
            "| المصدر | شنو يعطي | الرخصة | الربط | الحالة | ليش نستخدمه |", "|---|---|---|---|---|---|"]
    for s in data["sources"]:
        use = next((v for k, v in USE_AR.items() if s["use"].startswith(k)), s["use"])
        rows.append(f"| [{s['name']}]({s['url']}) | {s['kind']} | {s['licence']} | {use} | {s.get('status', '—')} | {s['ar']} |")
    return "\n".join(rows) + "\n"


if __name__ == "__main__":
    d = check(load()) if "--check" in sys.argv else load()
    (DIR / "CATALOG.md").write_text(markdown(d), encoding="utf-8")
    down = [s["name"] for s in d["sources"] if str(s.get("status", "up")).startswith("down")]
    print(f"📚 {len(d['sources'])} مصدر" + (f" — واقفة: {', '.join(down)}" if down else " — كلها شغالة"))
