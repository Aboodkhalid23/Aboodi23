#!/usr/bin/env bash
# يجهّز مشاريع الموشن (الرسوم المتحركة) الي سكيلزاتها مربوطة بمشروع كامل، مو ملف تعليمات بس.
#
#   scripts/motion-kit.sh new <اسم>   مشروع موشن جديد من قالب claude-motion بمجلد motion/<اسم>
#                                      سكيلزات motion-taste وmotion-review-loop وmotion-sound وmotion-web-sims تشتغل داخله
#   scripts/motion-kit.sh overlay      قالب الطبقات الشفافة (ترجمة متحركة، اسم وعنوان، عدّاد) من video-agent بـ motion/_overlay
#                                      سكيل remotion-graphics يشتغل داخله
#   scripts/motion-kit.sh browser      يطبع مسار المتصفح الي يستخدمه الرندر
#
# داخل أي مشروع: صدّر المتصفح قبل الرندر:  export REMOTION_BROWSER="$(scripts/motion-kit.sh browser)"
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
WORK="$ROOT/motion"

find_browser() {
  local c
  for c in "${REMOTION_BROWSER:-}" /opt/pw-browsers/chromium-*/chrome-linux64/chrome \
           /usr/bin/chromium /usr/bin/chromium-browser /usr/bin/google-chrome; do
    [[ -n "$c" && -x "$c" ]] && { echo "$c"; return 0; }
  done
  return 1
}

fetch() {  # fetch <owner/repo> <مجلد مؤقت>
  git clone -q --depth 1 "https://github.com/$1" "$2"
}

install_deps() {  # install_deps <مجلد>
  (cd "$1" && if [[ -f package-lock.json ]]; then npm ci --no-audit --no-fund --loglevel=error
             else npm install --no-audit --no-fund --loglevel=error; fi)
}

case "${1:-}" in
  new)
    name="${2:?اكتب اسم المشروع: scripts/motion-kit.sh new <اسم>}"
    dest="$WORK/$name"
    [[ -e "$dest" ]] && { echo "✗ المشروع موجود من قبل: motion/$name"; exit 1; }
    tmp="$(mktemp -d)"; trap 'rm -rf "$tmp"' EXIT
    fetch whaleyxbt/claude-motion "$tmp/src"
    mkdir -p "$dest"
    # القالب كامل بدون السكيلزات (مثبتة عدنا) ولا صور العرض الثقيلة
    (cd "$tmp/src" && tar --exclude=.git --exclude=.claude --exclude=media -cf - .) | tar -xf - -C "$dest"
    install_deps "$dest"
    echo "✓ جاهز: motion/$name"
    echo "  للتجربة:  cd motion/$name && export REMOTION_BROWSER=\"\$($ROOT/scripts/motion-kit.sh browser)\" && npm run draft && npm run sheet"
    ;;
  overlay)
    dest="$WORK/_overlay"
    if [[ -d "$dest/node_modules" ]]; then echo "= موجود: motion/_overlay"; exit 0; fi
    tmp="$(mktemp -d)"; trap 'rm -rf "$tmp"' EXIT
    fetch agamm/video-agent "$tmp/src"
    mkdir -p "$dest"
    (cd "$tmp/src/remotion" && tar -cf - .) | tar -xf - -C "$dest"
    install_deps "$dest"
    echo "✓ جاهز: motion/_overlay (طبقات: KineticCaption وLowerThird وTitleCard)"
    ;;
  browser)
    find_browser || { echo "✗ ما لگيت متصفح Chromium" >&2; exit 1; }
    ;;
  *)
    sed -n '2,10p' "$0" | sed 's/^# \{0,1\}//'
    exit 2
    ;;
esac
