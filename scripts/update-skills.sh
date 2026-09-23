#!/usr/bin/env bash
# يثبّت ويحدّث السكيلزات المذكورة في skills.manifest من GitHub.
#
#   scripts/update-skills.sh            # يثبّت/يحدّث بمجلد المشروع .claude/skills
#   scripts/update-skills.sh --global   # يثبّت/يحدّث بـ ~/.claude/skills (لكل مشاريعك)
#   scripts/update-skills.sh --check    # يعرض بس شنو تغيّر بدون ما يثبّت
#
# رقم الـ commit لكل سكيل مثبت ينحفظ في .skills.lock داخل مجلد السكيلزات حتى تعرف شنو تغيّر.
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
MANIFEST="$ROOT/skills.manifest"
DEST="$ROOT/.claude/skills"
CHECK_ONLY=0

for arg in "$@"; do
  case "$arg" in
    --global) DEST="$HOME/.claude/skills" ;;
    --check)  CHECK_ONLY=1 ;;
    *) echo "unknown option: $arg" >&2; exit 2 ;;
  esac
done

LOCK="$DEST/.skills.lock"
TMP="$(mktemp -d)"
trap 'rm -rf "$TMP"' EXIT
mkdir -p "$DEST"
touch "$LOCK"

KEEP_FILES=(company-profile.md .env)
declare -A HEAD
changed=0; failed=0

while read -r repo path name; do
  [[ -z "${repo:-}" || "$repo" == \#* ]] && continue
  [[ -z "${name:-}" ]] && name="$(basename "$path")"
  src="$TMP/${repo//\//_}"

  if [[ -z "${HEAD[$repo]:-}" ]]; then
    if ! git clone -q --depth 1 "https://github.com/$repo" "$src" 2>/dev/null; then
      echo "✗ $repo: فشل التحميل"; failed=1; HEAD[$repo]="FAILED"; continue
    fi
    HEAD[$repo]="$(git -C "$src" rev-parse --short HEAD)"
  fi
  [[ "${HEAD[$repo]}" == "FAILED" ]] && continue

  if [[ ! -f "$src/$path/SKILL.md" ]]; then
    echo "✗ $name: ما لگيت SKILL.md في $repo/$path"; failed=1; continue
  fi

  old="$(awk -v n="$name" '$1==n {print $3}' "$LOCK")"
  new="${HEAD[$repo]}"
  if [[ "$old" == "$new" && -d "$DEST/$name" ]]; then
    echo "= $name ($new)"
    continue
  fi

  echo "↑ $name: ${old:-جديد} → $new"
  changed=1
  [[ $CHECK_ONLY -eq 1 ]] && continue

  # ملفاتك الشخصية داخل السكيل (مثل ملف شركتك أو مفتاح API) تبقى بعد التحديث
  keep="$TMP/keep-$name"; mkdir -p "$keep"
  for f in "${KEEP_FILES[@]}"; do
    [[ -f "$DEST/$name/$f" ]] && cp "$DEST/$name/$f" "$keep/$f"
  done

  rm -rf "${DEST:?}/$name"
  mkdir -p "$DEST/$name"
  (cd "$src/$path" && tar --exclude=.git --exclude=.github -cf - .) | tar -xf - -C "$DEST/$name"
  cp -a "$keep/." "$DEST/$name/"
  awk -v n="$name" '$1!=n' "$LOCK" > "$LOCK.tmp"
  echo "$name $repo $new" >> "$LOCK.tmp"
  sort -o "$LOCK" "$LOCK.tmp"; rm -f "$LOCK.tmp"
done < "$MANIFEST"

WANTED=""
while read -r repo path name; do
  [[ -z "${repo:-}" || "$repo" == \#* ]] && continue
  WANTED+=" ${name:-$(basename "$path")}"
done < "$MANIFEST"

# احذف السكيلزات الي انشالت من الـ manifest (بس الي ثبّتها هذا السكربت)
if [[ $CHECK_ONLY -eq 0 ]]; then
  while read -r name _; do
    [[ -z "$name" ]] && continue
    if [[ " $WANTED " != *" $name "* ]]; then
      echo "− $name: انشال من القائمة"
      rm -rf "${DEST:?}/$name"
      awk -v n="$name" '$1!=n' "$LOCK" > "$LOCK.tmp" && mv "$LOCK.tmp" "$LOCK"
      changed=1
    fi
  done < "$LOCK"
fi

[[ $changed -eq 0 ]] && echo "كل السكيلزات محدّثة ✓"
exit $failed
