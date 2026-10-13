#!/usr/bin/env python3
"""يقرا الهوك (أو السكربت كامل) بصوت عراقي، حتى صاحب القناة يسمعه قبل التصوير.

الاستخدام:
    python3 scripts/voice-preview.py episodes/<الحلقة>/02-draft.md          # الهوك بس
    python3 scripts/voice-preview.py <الملف> --all                          # السكربت كامل
    python3 scripts/voice-preview.py <الملف> --voice ar-IQ-RanaNeural       # صوت بنت
ينتج: نفس المجلد/hook-voice.mp3 (أو script-voice.mp3)

الأصوات العراقية المجانية: ar-IQ-BasselNeural (رجل)، ar-IQ-RanaNeural (امرأة).
ملاحظة: الصوت الآلي ينطق فصحى أحياناً. الهدف تسمع الإيقاع وطول الجمل، مو اللهجة بالضبط.
"""
import asyncio
import os
import re
import sys


def extract(text, full):
    if full:
        body = text
    else:
        m = re.search(r"الهوك\s*\n(.*?)(?:\n\s*السكربت\s*\n|\Z)", text, re.S)
        body = m.group(1) if m else "\n".join(text.splitlines()[:25])
    body = re.sub(r"^(الهوك|السكربت|هوك بديل)\s*$", "", body, flags=re.M)
    # كل سطر جملة: نخلي وقفة قصيرة بين الأسطر
    lines = [l.strip() for l in body.splitlines() if l.strip()]
    return "\n".join(lines)


async def speak(text, voice, out):
    import edge_tts
    await edge_tts.Communicate(text, voice, rate="-5%").save(out)


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)
    src = sys.argv[1]
    full = "--all" in sys.argv
    voice = "ar-IQ-BasselNeural"
    if "--voice" in sys.argv:
        voice = sys.argv[sys.argv.index("--voice") + 1]
    text = extract(open(src, encoding="utf-8").read(), full)
    out = os.path.join(os.path.dirname(src) or ".", "script-voice.mp3" if full else "hook-voice.mp3")
    asyncio.run(speak(text, voice, out))
    print(f"✅ {out}  ({len(text.split())} كلمة، صوت {voice})")


if __name__ == "__main__":
    main()
