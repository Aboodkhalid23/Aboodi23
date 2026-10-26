#!/usr/bin/env bash
# فحص صحة الاستوديو: هل الأدوات منصّبة، والسكربتات سليمة، والسكيلزات محدّثة؟
#
#   scripts/doctor.sh          # فحص سريع (أقل من دقيقة)
#   scripts/doctor.sh --full   # ويا اختبارات المصمم ومصادر البحث (2-3 دقايق)
set -uo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"
FULL=0; [[ "${1:-}" == "--full" ]] && FULL=1
bad=0
ok()   { echo "✅ $1"; }
fail() { echo "❌ $1"; bad=1; }

echo "## الأدوات"
for t in python3 node ffmpeg ffprobe yt-dlp edge-tts git; do
  command -v "$t" >/dev/null && ok "$t" || fail "$t ما منصّب (scripts/setup-tools.sh)"
done

echo "## السكربتات"
for f in scripts/*.py designer/*.py $(find .claude/skills -name '*.py' -not -path '*/examples/*'); do
  python3 -m py_compile "$f" 2>/dev/null || fail "خطأ كتابة: $f"
done
for f in scripts/*.sh; do bash -n "$f" || fail "خطأ كتابة: $f"; done
for f in scripts/script-check.py scripts/teleprompter.py scripts/voice-preview.py scripts/yt-transcript.py; do
  python3 "$f" --help >/dev/null 2>&1; [[ $? -le 1 ]] || fail "$f يطيح"
done
[[ $bad -eq 0 ]] && ok "كل السكربتات سليمة"

echo "## السكيلزات"
out="$(bash scripts/update-skills.sh --check 2>&1)"
if grep -q "✗" <<<"$out"; then fail "سكيل ما نزل:"; grep "✗" <<<"$out"
elif grep -q "↑" <<<"$out"; then echo "⬆️ اكو تحديثات: شغّل scripts/update-skills.sh"; grep "↑" <<<"$out"
else ok "كل السكيلزات محدّثة ($(ls -d .claude/skills/*/ | wc -l) سكيل)"; fi

if [[ $FULL -eq 1 ]]; then
  echo "## اختبارات المصمم"
  python3 -m pytest -q designer/tests 2>&1 | tail -1
  echo "## مصادر البحث"
  python3 scripts/deep-search.py "Nokia" --limit 1 --json 2>/dev/null \
    | python3 -c "import json,sys;[print(('✅ ' if 'FAIL' not in v else '❌ ')+k+': '+v) for k,v in json.load(sys.stdin)['status'].items()]" \
    || fail "أداة البحث طاحت"
fi

echo
[[ $bad -eq 0 ]] && echo "🟢 الاستوديو سليم" || echo "🔴 اكو مشاكل فوگ"
exit $bad
