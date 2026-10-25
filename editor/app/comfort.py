"""Comfort features (owner, 2026-10-25): a notification when a job ends, templates from a good episode, a nightly
backup of every project's edit decisions, and a phone page on the home Wi-Fi.

Nothing here leaves his computer except the backup copy, which goes only into his own Google Drive folder (the Drive
app syncs it). The phone page is off until he turns it on, listens on his home network only, and every request needs
the secret code shown in the settings."""
import json
import secrets
import shutil
import socket
import subprocess
import sys
import time
from pathlib import Path

MAC = sys.platform == "darwin"
TEMPLATE_FILES = ("style.txt", "look.json", "sound.json", "options.json")
BACKUP_KEEP = ("edit_plan.json", "look.json", "sound.json", "options.json", "style.txt", "idea.txt", "chapters.txt",
               "credits.txt", "captions_en.json", "clean_words.json", "voice_patches.json", "cuts_override.json")


# ---------- notification ----------

def notify(title: str, text: str) -> None:
    if not MAC:
        return
    esc = lambda s: str(s).replace("\\", "\\\\").replace('"', '\\"')[:180]
    subprocess.Popen(["osascript", "-e", f'display notification "{esc(text)}" with title "{esc(title)}" sound name "Glass"'])


# ---------- templates ----------

def _tdir(home: Path) -> Path:
    d = Path(home) / "templates"
    d.mkdir(parents=True, exist_ok=True)
    return d


def save_template(home: Path, edit: Path, name: str) -> list[dict]:
    name = "".join(c for c in str(name).strip() if c not in '/\\:*?"<>|')[:40]
    if not name:
        raise ValueError("سمّ القالب")
    d = _tdir(home) / name
    d.mkdir(exist_ok=True)
    got = 0
    for f in TEMPLATE_FILES:
        if (edit / f).exists():
            shutil.copyfile(edit / f, d / f)
            got += 1
    if not got:
        shutil.rmtree(d, ignore_errors=True)
        raise ValueError("هالحلقة بعد ما بيها ستايل أو ألوان أو صوت تنحفظ")
    (d / "meta.json").write_text(json.dumps({"name": name, "at": time.time()}, ensure_ascii=False), encoding="utf-8")
    return templates(home)


def templates(home: Path) -> list[dict]:
    out = []
    for d in sorted(_tdir(home).iterdir()):
        if d.is_dir():
            out.append({"name": d.name, "has": [f for f in TEMPLATE_FILES if (d / f).exists()]})
    return out


def apply_template(home: Path, edit: Path, name: str) -> None:
    d = _tdir(home) / Path(str(name)).name
    if not d.is_dir():
        raise ValueError("القالب مو موجود")
    edit.mkdir(parents=True, exist_ok=True)
    for f in TEMPLATE_FILES:
        if (d / f).exists():
            shutil.copyfile(d / f, edit / f)


def delete_template(home: Path, name: str) -> list[dict]:
    shutil.rmtree(_tdir(home) / Path(str(name)).name, ignore_errors=True)
    return templates(home)


# ---------- backup into his Google Drive folder ----------

def drive_folder() -> Path | None:
    """Google Drive for desktop's folder on the Mac (~/Library/CloudStorage/GoogleDrive-<account>/My Drive)."""
    base = Path.home() / "Library" / "CloudStorage"
    for d in sorted(base.glob("GoogleDrive-*")) if base.exists() else []:
        for sub in ("My Drive", "ملفي", "Mon Drive"):
            if (d / sub).is_dir():
                return d / sub
    return None


def backup(home: Path, episodes: Path, dest: Path | None = None) -> dict:
    """Every project's decisions (plans, looks, captions, notes: small files, no videos), into Drive. A lost Mac
    loses only the raw videos, which he keeps anyway."""
    dest = dest or drive_folder()
    if not dest:
        return {"ok": False, "why": "ما لگيت درايف على الماك. نزّل تطبيق «گوگل درايف» للماك وسجّل بحسابك"}
    root = Path(dest) / "URU نسخة احتياطية"
    n = 0
    for ep in sorted(Path(episodes).iterdir()) if Path(episodes).exists() else []:
        edit = ep / "edit"
        if not edit.is_dir():
            continue
        out = root / ep.name
        out.mkdir(parents=True, exist_ok=True)
        for f in BACKUP_KEEP:
            if (edit / f).exists():
                shutil.copy2(edit / f, out / f)
        for f in ("meta.json",):
            if (ep / f).exists():
                shutil.copy2(ep / f, out / f)
        n += 1
    st = {"ok": True, "at": time.time(), "count": n, "where": str(root)}
    (Path(home) / "backup.json").write_text(json.dumps(st, ensure_ascii=False), encoding="utf-8")
    return st


def backup_status(home: Path) -> dict:
    try:
        st = json.loads((Path(home) / "backup.json").read_text(encoding="utf-8"))
    except (OSError, ValueError):
        st = {}
    st["drive"] = bool(drive_folder())
    return st


def backup_due(home: Path, every: float = 24 * 3600) -> bool:
    return time.time() - backup_status(home).get("at", 0) > every


# ---------- the phone page ----------

def phone_settings(home: Path) -> dict:
    f = Path(home) / "phone.json"
    try:
        return json.loads(f.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {"on": False}


def set_phone(home: Path, on: bool) -> dict:
    f = Path(home) / "phone.json"
    st = phone_settings(home)
    st["on"] = bool(on)
    if on and not st.get("code"):
        st["code"] = secrets.token_hex(3).upper()   # six characters he types once on the phone
    f.write_text(json.dumps(st), encoding="utf-8")
    f.chmod(0o600)
    return st


def lan_ip() -> str:
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(("10.255.255.255", 1))   # no packet is sent; it only picks the Wi-Fi address
        return s.getsockname()[0]
    except OSError:
        return "127.0.0.1"
    finally:
        s.close()
