"""صوت مقاطع أوّاب: الراوي (edge-tts) ومعالجته، وجو طبيعي خفيف، والتسوية النهائية.
- لا موسيقى ولا آلات نهائياً. الجو: هوا، ماي، سكون غرفة، وهمسة خفيفة عند تبدّل المشهد.
- التلاوة (مشاري العفاسي): بس تكبير ثابت للصوت (والمحدِّد يلمس قمم نادرة بحد 3 dB)، بلا أي معالجة ثانية، وبلا جو فوكها.
- المخرج أحادي (mono) بـ -14 LUFS: الموبايل يشغله بالسماعتين بنفس القوة.
- كل صوت من edge-tts ينحفظ بذاكرة مؤقتة (~/.cache/awwab-tts) حتى إعادة الصنع تصير أسرع."""
import asyncio, hashlib, json, os, re, subprocess
from pathlib import Path
import numpy as np

SR = 48000
TARGET_I, TARGET_TP = -14.0, -1.0       # الهدف النهائي: -14 LUFS، والذروة الحقيقية تحت -1 dBTP
LIMIT_DB = -1.8                          # سقف المحدِّد (قبل AAC) حتى يبقى الملف النهائي تحت -1
QURAN_I, QURAN_MAX_LIMIT_DB = -15.0, 3.0  # التلاوة: نقرّبها للهدف، والمحدِّد ما يلمس أكثر من 3 dB بأعلى القمم (0 = تكبير ثابت بس)
CACHE = Path(os.environ.get("AWWAB_TTS_CACHE", "~/.cache/awwab-tts")).expanduser()

# سلسلة الصوت: قص الهمهمة الواطية، تنظيف الطين، ضغط على 3 مراحل، دفا، وضوح ~3kHz، تخفيف السين
VOICE_CHAIN = ",".join([
    "aresample=48000",
    "highpass=f=80:p=2", "highpass=f=70:p=2",
    "equalizer=f=320:t=q:w=1.2:g=-2.5",
    "acompressor=threshold=-30dB:ratio=2.5:attack=8:release=120:knee=6",
    "acompressor=threshold=-26dB:ratio=3:attack=2:release=50:knee=4",
    "acompressor=threshold=-24dB:ratio=6:attack=0.2:release=40:knee=3:detection=peak",   # يمسك القمم الحادة قبل المحدِّد
    "bass=g=1.5:f=150:w=0.6",
    "equalizer=f=3000:t=q:w=1.0:g=2",
    "equalizer=f=6500:t=q:w=1.4:g=-2.5",
    "deesser=i=0.5:m=0.5:f=0.45:s=o",
])
REVERB_WET_DB = -21.0                    # غرفة صغيرة جداً: يحس بيها المستمع وما يسمعها كصدى
AMB_DB = -31.0                           # الجو تحت الكلام بـ31 dB (قبل الإخماد وقت الكلام)
DUCK_DB = 7.0                            # كم ينزل الجو وقت الكلام
WHOOSH_DB = -27.0                        # همسة تبدّل المشهد

# ---------------------------------------------------------------- أدوات ffmpeg

def decode(path, sr=SR):
    raw = subprocess.check_output(["ffmpeg", "-v", "error", "-i", str(path), "-ac", "1", "-ar", str(sr), "-f", "f32le", "-"])
    return np.frombuffer(raw, np.float32).copy()

def ffilter(x, chain, ch=1):
    """يمرر عينات numpy خلال فلاتر ffmpeg ويرجعها"""
    raw = subprocess.run(["ffmpeg", "-v", "error", "-f", "f32le", "-ar", str(SR), "-ac", str(ch), "-i", "-", "-af", chain,
                          "-ar", str(SR), "-f", "f32le", "-"], input=np.ascontiguousarray(x, np.float32).tobytes(),
                         capture_output=True, check=True).stdout
    y = np.frombuffer(raw, np.float32).copy()
    return y.reshape(-1, ch) if ch > 1 else y

def loudness(x, ch=1):
    """BS.1770 بـ ffmpeg: (الشدة المتكاملة LUFS، الذروة الحقيقية dBTP، المدى LRA)"""
    o = subprocess.run(["ffmpeg", "-nostats", "-f", "f32le", "-ar", str(SR), "-ac", str(ch), "-i", "-", "-af", "ebur128=peak=true",
                        "-f", "null", "-"], input=np.ascontiguousarray(x, np.float32).tobytes(), capture_output=True).stderr.decode()
    return _summary(o)

def file_loudness(path):
    o = subprocess.run(["ffmpeg", "-nostats", "-i", str(path), "-vn", "-af", "ebur128=peak=true", "-f", "null", "-"], capture_output=True).stderr.decode()
    return _summary(o)

def _summary(o):
    s = o[o.rfind("Summary:"):]
    g = lambda k: float(re.search(k + r":\s+(-?[\d.]+|-inf)", s).group(1).replace("-inf", "-99"))
    return g("I"), g("Peak"), g("LRA")

# ---------------------------------------------------------------- الراوي (edge-tts ويا ذاكرة)

async def _synth(text, voice, rate, pitch, mp3):
    import edge_tts
    words, buf = [], bytearray()
    async for ch in edge_tts.Communicate(text, voice, rate=rate, pitch=pitch, boundary="WordBoundary").stream():
        if ch["type"] == "audio": buf += ch["data"]
        elif ch["type"] == "WordBoundary": words.append((ch["offset"] / 1e7, (ch["offset"] + ch["duration"]) / 1e7, ch["text"]))
    if not buf: raise RuntimeError("NoAudioReceived")
    mp3.write_bytes(bytes(buf))
    return words

def tts(text, voice, rate, pitch):
    """يرجع (ملف mp3، كلمات بأوقاتها). من الذاكرة إذا انصنع قبل"""
    CACHE.mkdir(parents=True, exist_ok=True)
    h = hashlib.sha1(json.dumps([text, voice, rate, pitch, "wb1"], ensure_ascii=False).encode()).hexdigest()[:20]
    mp3, js = CACHE / f"{h}.mp3", CACHE / f"{h}.json"
    if mp3.exists() and js.exists() and mp3.stat().st_size > 0:
        return mp3, [tuple(w) for w in json.loads(js.read_text(encoding="utf-8"))]
    for i in range(10):  # خدمة الصوت أحياناً ترفض من كثر الطلبات، نعيد بصبر
        try:
            words = asyncio.run(_synth(text, voice, rate, pitch, mp3.with_suffix(".part")))
            mp3.with_suffix(".part").replace(mp3)
            js.write_text(json.dumps(words, ensure_ascii=False), encoding="utf-8")
            return mp3, words
        except Exception:
            if i == 9: raise
            __import__("time").sleep(3 + i * 4)

def _key(w):
    w = re.sub(r"[ؐ-ًؚ-ٰٟۖ-ۭـ]", "", w).lower()
    w = re.sub(r"[أإآٱ]", "ا", w).replace("ى", "ي").replace("ة", "ه")
    return re.sub(r"[^ء-يa-z0-9]", "", w)

def speak(parts, voice, rate, pitch):
    """يقرا عدة مقاطع نص بنفس النَّفَس (جملة كاملة)، ويرجع (العينات بعد قص السكوت، [بداية، نهاية] لكل مقطع)"""
    text = " ".join(p for p in parts if p)
    mp3, words = tts(text, voice, rate, pitch)
    x = decode(mp3)
    total = len(x) / SR
    if not words:
        return x, _even(parts, 0.0, total)
    a = max(0.0, words[0][0] - 0.05)
    b = min(total, words[-1][1] + 0.16)
    x = x[int(a * SR):int(b * SR)]
    fade = int(0.012 * SR); x[:fade] *= np.linspace(0, 1, fade); x[-fade:] *= np.linspace(1, 0, fade)
    words = [(s - a, e - a, t) for s, e, t in words]
    # نربط كل كلمة منطوقة بالمقطع الي هي منه
    flat = [(i, _key(w)) for i, p in enumerate(parts) for w in p.split() if _key(w)]
    first, last, p = {}, {}, 0
    for s, e, t in words:
        k = _key(t)
        if not k: continue
        for j in range(p, min(p + 4, len(flat))):
            fk = flat[j][1]
            if fk == k or (len(k) > 1 and (k in fk or fk in k)):
                si = flat[j][0]; first.setdefault(si, s); last[si] = e; p = j + 1; break
    spoken = [i for i, pt in enumerate(parts) if any(_key(w) for w in pt.split())]
    if any(i not in first for i in spoken):
        return x, _even(parts, 0.0, len(x) / SR)
    out, dur = [], len(x) / SR
    for i in range(len(parts)):
        st = first.get(i, out[-1][1] if out else 0.0)
        out.append([st, None])
    out[0][0] = 0.0
    for i in range(len(out)):
        out[i][1] = out[i + 1][0] if i + 1 < len(out) else dur
    return x, out

def _even(parts, a, b):
    wc = [max(1, len(p.split())) for p in parts]; out, st = [], a
    for w in wc:
        d = (b - a) * w / sum(wc); out.append([st, st + d]); st += d
    return out

# ---------------------------------------------------------------- مساحة الغرفة

def _shape(n, curve, rng, ch=2):
    """ضوضاء بيضا مشكّلة بالترددات: curve(f) ترجع المكسب الخطي"""
    X = np.fft.rfft(rng.standard_normal((ch, n)), axis=1)
    f = np.fft.rfftfreq(n, 1 / SR)
    y = np.fft.irfft(X * curve(f)[None, :], n=n, axis=1)
    return (y / (np.sqrt(np.mean(y ** 2)) + 1e-12)).astype(np.float32)

def room_ir(rng):
    """استجابة غرفة صغيرة (ستيريو): انعكاسات مبكرة قليلة وذيل قصير غامق"""
    n = int(0.55 * SR); t = np.arange(n) / SR
    tail = _shape(n, lambda f: np.where(f < 180, (f / 180) ** 2, 1) / (1 + (f / 3500) ** 2), rng)
    tail *= np.exp(-6.91 * t / 0.38)[None, :]           # RT60 ≈ 0.38 ث
    tail[:, :int(0.012 * SR)] = 0                         # تأخير أولي
    for d in (0.007, 0.011, 0.017, 0.023, 0.031):
        k = int(d * SR); tail[0, k] += 0.35 * rng.choice([-1, 1]) * np.exp(-d / 0.05); tail[1, k + int(rng.integers(5, 40))] += 0.35 * rng.choice([-1, 1]) * np.exp(-d / 0.05)
    return tail / np.sqrt(np.sum(tail ** 2, axis=1, keepdims=True))

def convolve(x, ir):
    n = len(x) + ir.shape[1]; N = 1 << (n - 1).bit_length()
    X = np.fft.rfft(x, N)
    return np.stack([np.fft.irfft(X * np.fft.rfft(h, N), N)[:len(x)] for h in ir], axis=1).astype(np.float32)

# ---------------------------------------------------------------- الجو الطبيعي (بلا نغمات)

AMB_KIND = {"day": "air", "garden": "air", "valley": "air", "dawn": "air", "light": "air",
            "desert": "wind", "sky": "wind", "storm": "storm", "sea": "water", "deep": "deep",
            "night": "night", "mosque": "room", "home": "room", "scroll": "room", "market": "room",
            "dark": "room", "cavein": "cave", "space": "space", "hell": "rumble"}
AMB_GAIN = {"air": 0, "wind": 1, "storm": 3, "water": 2, "deep": 1, "night": -2, "room": -3, "cave": -1, "space": -5, "rumble": 1}

def _slow(n, rng, period, depth):
    """غلاف بطيء عشوائي (هبّات) بين 1-depth و 1"""
    k = max(4, int(n / SR / period * 4)); pts = rng.random(k + 3)
    env = np.interp(np.linspace(0, k, n), np.arange(k + 3), pts)
    env = _smooth(env, int(SR * period / 4)) if n > SR * period else env
    env = (env - env.min()) / (np.ptp(env) + 1e-9)
    return (1 - depth + depth * env).astype(np.float32)

def bed(kind, n, rng):
    lp = lambda fc, o=2: (lambda f: 1 / np.sqrt(1 + (f / fc) ** (2 * o)))
    hp = lambda fc, o=2: (lambda f: 1 / np.sqrt(1 + (fc / np.maximum(f, 1)) ** (2 * o)))
    pink = lambda f: 1 / np.sqrt(np.maximum(f, 20) / 20)
    if kind == "air":     # هوا مفتوح هادي
        y = _shape(n, lambda f: pink(f) * hp(250)(f) * lp(3500)(f), rng); y *= _slow(n, rng, 6, 0.35)[None, :]
    elif kind in ("wind", "storm"):
        lo = _shape(n, lambda f: pink(f) * hp(120)(f) * lp(700 if kind == "wind" else 500, 3)(f), rng)
        hi = _shape(n, lambda f: hp(900)(f) * lp(2600)(f), rng)
        g1, g2 = _slow(n, rng, 5, 0.75), _slow(n, rng, 3, 0.8)
        y = lo * g1[None, :] + 0.35 * hi * (g1 * g2)[None, :]
    elif kind == "water": # موج بعيد: انتفاخ كل 6-8 ث
        t = np.arange(n) / SR
        sw = 0.55 + 0.45 * np.sin(2 * np.pi * t / 7.3) * np.sin(2 * np.pi * t / 7.3 + 0.6 * np.sin(t / 3))
        y = _shape(n, lambda f: pink(f) * hp(80)(f) * lp(900)(f), rng) * sw[None, :]
        y += 0.3 * _shape(n, lambda f: hp(1500)(f) * lp(5000)(f), rng) * (sw ** 3)[None, :]
    elif kind == "deep":
        y = _shape(n, lambda f: hp(50)(f) * lp(350, 3)(f), rng) * _slow(n, rng, 8, 0.4)[None, :]
    elif kind == "night":
        y = _shape(n, lambda f: pink(f) * hp(150)(f) * lp(1800)(f), rng) * _slow(n, rng, 9, 0.25)[None, :]
    elif kind == "cave":
        y = _shape(n, lambda f: hp(60)(f) * lp(450, 3)(f), rng) * _slow(n, rng, 7, 0.5)[None, :]
    elif kind == "space":
        y = _shape(n, lambda f: hp(400)(f) * lp(2500)(f), rng) * _slow(n, rng, 10, 0.3)[None, :]
    elif kind == "rumble":
        y = _shape(n, lambda f: hp(45)(f) * lp(260, 3)(f), rng) * _slow(n, rng, 4, 0.5)[None, :]
    else:                 # room: سكون غرفة
        y = _shape(n, lambda f: pink(f) * hp(90)(f) * lp(900)(f), rng)
    y = y[0]
    return (y / (np.sqrt(np.mean(y ** 2)) + 1e-12)).astype(np.float32)

def whoosh(rng, dur=0.75):
    """همسة هوا قصيرة: ضوضاء بمرشح يمسح من 350 إلى 1500 Hz (بلا نغمة)"""
    n = int(dur * SR); x = rng.standard_normal(n).astype(np.float64)
    fc = 350 * (1500 / 350) ** (np.linspace(0, 1, n) ** 0.8)
    F = 2 * np.sin(np.pi * fc / SR); q = 1 / 1.4; low = band = 0.0; y = np.empty(n)
    for i in range(n):
        low += F[i] * band; high = x[i] - low - q * band; band += F[i] * high; y[i] = band
    t = np.linspace(0, 1, n); peak = 0.62
    env = np.where(t < peak, (t / peak) ** 2.2, np.exp(-(t - peak) / 0.09))
    y = y * env; y /= np.sqrt(np.mean(y[env > 0.3] ** 2)) + 1e-9
    return y.astype(np.float32), peak * dur

def _smooth(x, k):
    """متوسط متحرك سريع (بالمجموع التراكمي)"""
    c = np.cumsum(np.concatenate([[0.0], np.asarray(x, np.float64)])); h = k // 2
    i = np.arange(len(x)); lo = np.clip(i - h, 0, len(x)); hi = np.clip(i + k - h, 0, len(x))
    return (c[hi] - c[lo]) / np.maximum(hi - lo, 1)

def envelope_db(x, win=0.03):
    return 10 * np.log10(_smooth(np.asarray(x, np.float64) ** 2, int(win * SR)) + 1e-12)

def ambience(beats, total, voice, seed):
    """يبني فرشة الجو للمشاهد ويا تداخل ناعم عند التبدّل، ويخمدها وقت الكلام. يرجع (الفرشة، الهمسات)"""
    rng = np.random.default_rng(seed); n = int(total * SR)
    spans = []
    for i, b in enumerate(beats):
        k = AMB_KIND.get(b["bg"], "room"); t0 = 0.0 if i == 0 else b["t"]
        if spans and spans[-1][0] == k: continue
        spans.append([k, t0])
    out = np.zeros(n, np.float32); xf = 1.4
    for i, (k, t0) in enumerate(spans):
        t1 = spans[i + 1][1] if i + 1 < len(spans) else total
        a, b = max(0, int((t0 - xf / 2) * SR)), min(n, int((t1 + xf / 2) * SR))
        seg = bed(k, b - a, rng) * 10 ** (AMB_GAIN[k] / 20)
        g = np.ones(b - a, np.float32); f = int(xf * SR)
        if i > 0: g[:f] = np.sin(np.linspace(0, np.pi / 2, f))   # تداخل بنفس القدرة
        else: g[:int(1.5 * SR)] = np.linspace(0, 1, int(1.5 * SR))
        if i + 1 < len(spans): g[-f:] = np.cos(np.linspace(0, np.pi / 2, f))
        else: g[-int(2.0 * SR):] = np.linspace(1, 0, int(2.0 * SR))
        out[a:b] += seg * g
    # الإخماد تحت الكلام: هجوم سريع ورجوع بطيء
    act = (envelope_db(voice) > envelope_db(voice).max() - 35).astype(np.float64)
    hop = 480; a_ = act[::hop]; s = np.zeros_like(a_); v = 0.0
    for i, z in enumerate(a_):
        v += (z - v) * (0.5 if z > v else 0.06); s[i] = v
    duck = 10 ** (-DUCK_DB * np.interp(np.arange(n), np.arange(len(s)) * hop, s) / 20)
    out *= duck.astype(np.float32)
    # همسة عند تبدّل المشهد (مو أكثر من وحدة كل 2.5 ث)
    wh = np.zeros_like(out); last = -9
    for b in beats[1:]:
        if b["t"] - last < 2.5 or b["t"] < 1.0 or b["t"] > total - 1.0: continue
        prev = [x for x in beats if x["t"] < b["t"]]
        if not prev or prev[-1]["bg"] == b["bg"]: continue
        w, pk = whoosh(rng); st = int((b["t"] - pk) * SR)
        if st < 0: continue
        e = min(n, st + len(w)); wh[st:e] += w[:e - st]; last = b["t"]
    return out, wh

# ---------------------------------------------------------------- التسوية النهائية

def master(voice, out, beats=None, total=None, amb=True, seed=0, quran=False):
    """voice: مسار الكلام (أحادي 48k). يكتب m4a أحادي (الموبايل يشغله بالسماعتين بنفس القوة) ويرجع القياسات"""
    if quran:
        # التلاوة: تكبير ثابت بس، بلا ضغط ولا تعديل. المحدِّد يلمس بس قمم نادرة وبحد أقصى QURAN_MAX_LIMIT_DB
        I, tp, _ = loudness(voice)
        g = min(QURAN_I - I, (TARGET_TP - 0.3 + QURAN_MAX_LIMIT_DB) - tp)
        return _encode(voice, out, gain=g, limit=tp + g > LIMIT_DB, target=None)
    I0 = loudness(voice)[0]
    v = ffilter(voice * np.float32(10 ** ((-24 - I0) / 20)), VOICE_CHAIN)   # نثبّت المستوى قبل الضغط حتى العتبات تشتغل نفس الشي لكل صوت
    v = v[:len(voice)] if len(v) >= len(voice) else np.pad(v, (0, len(voice) - len(v)))
    mix = v + convolve(v, room_ir(np.random.default_rng(7))[:1])[:, 0] * 10 ** (REVERB_WET_DB / 20)
    if amb and beats:
        bd, wh = ambience(beats, len(v) / SR, v, seed)
        vr = np.sqrt(np.mean(v[envelope_db(v) > envelope_db(v).max() - 30] ** 2))
        mix = mix + bd * vr * 10 ** (AMB_DB / 20) + wh * vr * 10 ** (WHOOSH_DB / 20)
    return _encode(mix, out)

def _encode(mix, out, gain=None, limit=True, target=TARGET_I):
    """يكتب AAC ويتأكد: الشدة على الهدف، والذروة الحقيقية بعد الترميز تحت TARGET_TP"""
    if gain is None: gain = target - loudness(mix)[0]
    lim, data = LIMIT_DB, np.ascontiguousarray(mix, np.float32).tobytes()
    if os.environ.get("AWWAB_DEBUG"):
        y = np.abs(np.asarray(mix, np.float64)) * 10 ** (gain / 20); over = 20 * np.log10(np.maximum(y, 1e-9)) - LIMIT_DB
        k = int(0.05 * SR); blocks = over[:len(over) // k * k].reshape(-1, k).max(axis=1)
        print(f"   قبل المحدِّد: ذروة {loudness(mix)[1] + gain:.1f} dBTP · قطع 50ms فوك السقف: {int((blocks > 0).sum())} (فوك 2 dB: {int((blocks > 2).sum())}) من {len(blocks)}")
    for k in range(9):
        chain = f"volume={gain:.2f}dB"
        if limit: chain += f",aresample=192000,alimiter=limit={10 ** (lim / 20):.4f}:attack=4:release=80:level=0,aresample={SR}"
        br = ("128k", "112k", "144k")[k % 3]   # مرمّز AAC أحياناً يطلّع قمة بإطار وحد، نجرب معدل ثاني
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "f32le", "-ar", str(SR), "-ac", "1", "-i", "-", "-af", chain,
                        "-c:a", "aac", "-b:a", br, "-ar", str(SR), str(out)], input=data, check=True)
        I2, tp2, lra = file_loudness(out)
        if target is not None and abs(I2 - target) > 0.3: gain += target - I2; continue
        if tp2 <= TARGET_TP: break
        if k % 3 == 2:
            if limit: lim -= 0.5
            else: gain -= 0.5
    return {"I": I2, "TP": tp2, "LRA": lra}
