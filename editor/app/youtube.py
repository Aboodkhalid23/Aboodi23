"""His YouTube channel inside the app (owner, 2026-10-25): the finished episode goes up by itself at its best
quality as a PRIVATE video; he opens YouTube Studio, adds the title, description, thumbnail, and publishes.

Linking uses Google's sign-in for desktop apps (OAuth with PKCE and a 127.0.0.1 return address). The Google
"client" (id + secret) is his own, made once in Google Cloud and pasted in the app: nothing secret lives in the
public repo. Everything is kept in $MONTIER_HOME/youtube.json (mode 600) on his Mac.
Google keeps videos uploaded by a not-yet-reviewed client private; that is exactly what he wants until publishing,
and the free review lifts it (the app's guide says how)."""
import base64
import hashlib
import json
import os
import secrets
import time
import urllib.parse
from pathlib import Path

import requests

AUTH = "https://accounts.google.com/o/oauth2/v2/auth"
TOKEN = "https://oauth2.googleapis.com/token"
UPLOAD = "https://www.googleapis.com/upload/youtube/v3/videos"
CHANNELS = "https://www.googleapis.com/youtube/v3/channels"
SCOPES = "https://www.googleapis.com/auth/youtube.upload https://www.googleapis.com/auth/youtube.readonly"
CHUNK = 16 * 1024 * 1024
PENDING: dict = {}      # state -> verifier, while he signs in


def _file(home: Path) -> Path:
    return home / "youtube.json"


def load(home: Path) -> dict:
    try:
        return json.loads(_file(home).read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}


def _save(home: Path, d: dict) -> None:
    f = _file(home)
    f.write_text(json.dumps(d, ensure_ascii=False, indent=1), encoding="utf-8")
    os.chmod(f, 0o600)


def status(home: Path) -> dict:
    d = load(home)
    return {"client": bool(d.get("client_id")), "linked": bool(d.get("refresh_token")), "channel": d.get("channel", "")}


def set_client(home: Path, client_id: str, client_secret: str) -> dict:
    client_id, client_secret = client_id.strip(), client_secret.strip()
    if not client_id.endswith(".apps.googleusercontent.com") or len(client_secret) < 10:
        raise ValueError("الرمزين مو صحيحين. انسخهم مثل ما هم من صفحة گوگل")
    d = load(home)
    d.update(client_id=client_id, client_secret=client_secret)
    d.pop("refresh_token", None)
    _save(home, d)
    return status(home)


def auth_url(home: Path, redirect: str) -> str:
    d = load(home)
    if not d.get("client_id"):
        raise ValueError("حط رمز گوگل أول (مرة وحدة)")
    verifier = secrets.token_urlsafe(48)
    state = secrets.token_urlsafe(16)
    PENDING[state] = verifier
    challenge = base64.urlsafe_b64encode(hashlib.sha256(verifier.encode()).digest()).rstrip(b"=").decode()
    q = {"client_id": d["client_id"], "redirect_uri": redirect, "response_type": "code", "scope": SCOPES,
         "access_type": "offline", "prompt": "consent", "state": state, "code_challenge": challenge,
         "code_challenge_method": "S256"}
    return AUTH + "?" + urllib.parse.urlencode(q)


def finish(home: Path, code: str, state: str, redirect: str, session=None) -> dict:
    verifier = PENDING.pop(state, None)
    if not verifier:
        raise ValueError("انتهت محاولة الربط. عيدها من التطبيق")
    d = load(home)
    s = session or requests
    r = s.post(TOKEN, data={"code": code, "client_id": d["client_id"], "client_secret": d["client_secret"],
                            "redirect_uri": redirect, "grant_type": "authorization_code", "code_verifier": verifier}, timeout=30)
    if r.status_code != 200:
        raise ValueError("گوگل رفض الربط: " + r.text[:200])
    tok = r.json()
    d.update(refresh_token=tok.get("refresh_token") or d.get("refresh_token"), access_token=tok["access_token"],
             expires=time.time() + int(tok.get("expires_in", 3600)) - 60)
    try:
        ch = s.get(CHANNELS, params={"part": "snippet", "mine": "true"},
                   headers={"Authorization": "Bearer " + d["access_token"]}, timeout=30).json()
        d["channel"] = ch["items"][0]["snippet"]["title"]
    except Exception:
        d["channel"] = ""
    _save(home, d)
    return status(home)


def unlink(home: Path) -> dict:
    d = load(home)
    for k in ("refresh_token", "access_token", "expires", "channel"):
        d.pop(k, None)
    _save(home, d)
    return status(home)


def _access(home: Path, session=None) -> str:
    d = load(home)
    if not d.get("refresh_token"):
        raise ValueError("قناة يوتيوب مو مربوطة")
    if d.get("access_token") and d.get("expires", 0) > time.time():
        return d["access_token"]
    s = session or requests
    r = s.post(TOKEN, data={"client_id": d["client_id"], "client_secret": d["client_secret"],
                            "refresh_token": d["refresh_token"], "grant_type": "refresh_token"}, timeout=30)
    if r.status_code != 200:
        raise ValueError("انتهى ربط يوتيوب. اربطه من جديد من الإعدادات")
    tok = r.json()
    d.update(access_token=tok["access_token"], expires=time.time() + int(tok.get("expires_in", 3600)) - 60)
    _save(home, d)
    return d["access_token"]


def upload(home: Path, video: Path, title: str, description: str = "", tags: list | None = None,
           progress=None, session=None) -> str:
    """Resumable upload, private. Returns the video id."""
    s = session or requests.Session()
    size = video.stat().st_size
    meta = {"snippet": {"title": (title or video.stem)[:100], "description": description[:4900], "tags": tags or [],
                        "categoryId": "27", "defaultLanguage": "ar", "defaultAudioLanguage": "ar"},
            "status": {"privacyStatus": "private", "selfDeclaredMadeForKids": False}}
    r = s.post(UPLOAD, params={"uploadType": "resumable", "part": "snippet,status"}, json=meta, timeout=60,
               headers={"Authorization": "Bearer " + _access(home, s), "X-Upload-Content-Type": "video/*",
                        "X-Upload-Content-Length": str(size)})
    if r.status_code != 200 or "Location" not in r.headers:
        raise ValueError("يوتيوب ما قبل يبدي الرفع: " + r.text[:300])
    where, sent = r.headers["Location"], 0
    with open(video, "rb") as f:
        while sent < size:
            f.seek(sent)
            chunk = f.read(CHUNK)
            for attempt in range(5):
                try:
                    r = s.put(where, data=chunk, timeout=600, headers={
                        "Authorization": "Bearer " + _access(home, s),
                        "Content-Range": f"bytes {sent}-{sent + len(chunk) - 1}/{size}"})
                    break
                except requests.RequestException:
                    time.sleep(2 ** attempt)
            else:
                raise ValueError("النت انقطع أثناء الرفع. عيد وراح يكمل")
            if r.status_code in (200, 201):
                if progress:
                    progress(100)
                return r.json()["id"]
            if r.status_code != 308:
                raise ValueError("الرفع وگف: " + r.text[:300])
            rng = r.headers.get("Range", "")
            sent = int(rng.split("-")[1]) + 1 if rng else sent
            if progress:
                progress(min(99, int(sent / size * 100)))
    raise ValueError("الرفع ما كمل")
