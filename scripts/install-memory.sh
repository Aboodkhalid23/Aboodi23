#!/usr/bin/env bash
# يركّب نظام الذاكرة (MEMORY.md + سكيل session-memory + hook بداية الجلسة) بأي ريبو ثاني.
#
#   bash scripts/install-memory.sh /path/to/other-repo
#
# آمن تعيد تشغيله: ما يمسح شي موجود، يضيف بس الناقص.
set -euo pipefail
SRC="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
DEST="$(cd "${1:?اكتب مسار الريبو}" && pwd)"

mkdir -p "$DEST/.claude/skills"
# 1) السكيل
if [[ ! -d "$DEST/.claude/skills/session-memory" ]]; then
  cp -r "$SRC/.claude/skills/session-memory" "$DEST/.claude/skills/"
fi
[[ -f "$DEST/.claude/session-memory.json" ]] || echo '{}' > "$DEST/.claude/session-memory.json"

# 2) ملف الذاكرة
if [[ ! -f "$DEST/MEMORY.md" ]]; then
  cat > "$DEST/MEMORY.md" <<'EOF'
# MEMORY — ذاكرة المشروع بين الجلسات

> كل جلسة تقرا **آخر هذا الملف بس**. بنهاية كل مهمة ينضاف قسم قصير: الحالة، والقرارات، والخطوة الجاية.
> سطر لكل حقيقة، بدون شرح طويل، وتحديث الحالة بدل تكرارها.
EOF
fi

# 3) hook: يطلّع آخر الذاكرة ببداية الجلسة، وبعد /clear والضغط التلقائي
python3 - "$DEST/.claude/settings.json" <<'EOF'
import json, os, sys
p = sys.argv[1]
d = json.load(open(p)) if os.path.exists(p) else {}
cmd = 'tail -n 45 "$CLAUDE_PROJECT_DIR"/MEMORY.md 2>/dev/null || true'
ss = d.setdefault("hooks", {}).setdefault("SessionStart", [])
if not any(h.get("command") == cmd for b in ss for h in b.get("hooks", [])):
    ss.append({"matcher": "startup|clear|compact", "hooks": [{"type": "command", "command": cmd, "timeout": 10}]})
json.dump(d, open(p, "w"), ensure_ascii=False, indent=2)
open(p, "a").write("\n")
EOF

# 4) القاعدة بـ CLAUDE.md
if ! grep -q "الذاكرة بين الجلسات" "$DEST/CLAUDE.md" 2>/dev/null; then
  cat >> "$DEST/CLAUDE.md" <<'EOF'

## الذاكرة بين الجلسات (توفير توكينز)
- **ببداية كل جلسة:** آخر `MEMORY.md` يطلع تلقائياً. اعتمد عليه، ولا تعيد قراءة ملفات كبيرة إلا وقت الحاجة.
- **بنهاية كل مهمة كبيرة:** شغّل `session-memory end`، أو ضيف قسم قصير بآخر `MEMORY.md`، وسوّ commit.
- **كل مهمة جديدة بجلسة جديدة (أو `/clear`).** المحادثة الطويلة تغلى ويه كل رسالة.
EOF
fi
echo "✅ نظام الذاكرة تركّب بـ $DEST. سوّ commit هناك حتى ينحفظ."
