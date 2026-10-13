#!/usr/bin/env bash
# تثبيت أدوات الاستوديو ببداية كل جلسة (الحاوية تنمسح، فلازم تنعاد).
# faster-whisper: تفريغ الصوت للنص | edge-tts: صوت عراقي يقرا السكربت
# trafilatura: سحب نص المقالات | internetarchive: البحث بأرشيف الإنترنت
pip install -q faster-whisper edge-tts trafilatura internetarchive >/dev/null 2>&1 || true
# داخل حاوية Claude بس: edge-tts يحتاج شهادة البروكسي داخل certifi
if [ -f /root/.ccr/ca-bundle.crt ]; then
  CERT=$(python3 -c 'import certifi;print(certifi.where())' 2>/dev/null)
  if [ -n "$CERT" ] && ! grep -q "ccr-proxy-ca" "$CERT" 2>/dev/null; then
    { echo "# ccr-proxy-ca"; cat /root/.ccr/ca-bundle.crt; } >> "$CERT"
  fi
fi
