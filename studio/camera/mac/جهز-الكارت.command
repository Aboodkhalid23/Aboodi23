#!/bin/bash
# برنامج الماك: يجهّز كارت الكاميرا (Sony ZV-E10 II) بدوسة وحدة.
# 1) يحط الفلاتر السبعة بالمكان الي الكاميرا تدوّر بيه (PRIVATE/SONY/PRO/LUT)
# 2) ياخذ نسخة من ملفات إعدادات الكاميرا الي بالكارت ويحفظها بالماك
# 3) يرجّع النسخة للكارت (إذا مسحت الكارت أو خربت الإعدادات)
# يشتغل على bash 3.2 (الموجود بالماك)، بلا أي برنامج إضافي.

DIR="$(cd "$(dirname "$0")" && pwd)"
LUTS="$DIR/luts"
VOLUMES="${VOLUMES_DIR:-/Volumes}"          # للاختبار بس
BACKUP="${BACKUP_DIR:-$HOME/Documents/إعدادات-الكاميرا}"

say_line() { printf '\n%s\n' "$1"; }
pause_exit() { printf '\n'; read -r -p "دوس Enter حتى تسد الشاشة " _; exit "${1:-0}"; }

[ -f "$LUTS/1.cube" ] || { say_line "❌ ما لگيت الفلاتر. خلي مجلد luts جنب هذا الملف."; pause_exit 1; }

# ---- نلگي الكارت: أي قرص بيه DCIM أو PRIVATE ----
cards=()
for v in "$VOLUMES"/*; do
  [ -d "$v" ] || continue
  case "$(basename "$v")" in "Macintosh HD"*|Recovery|Preboot|VM|Data) continue ;; esac
  if [ -d "$v/DCIM" ] || [ -d "$v/PRIVATE" ]; then cards+=("$v"); fi
done

if [ ${#cards[@]} -eq 0 ]; then
  say_line "❌ ما لگيت كارت الكاميرا."
  say_line "دخّل الكارت بالماك (قارئ كارت)، ولازم يكون انفرمت بالكاميرا مرة وحدة على الأقل. وبعدين شغّلني من جديد."
  pause_exit 1
fi

CARD="${cards[0]}"
if [ ${#cards[@]} -gt 1 ]; then
  say_line "لگيت أكثر من كارت. اكتب رقم الكارت:"
  i=1; for c in "${cards[@]}"; do echo "  $i) $(basename "$c")"; i=$((i+1)); done
  read -r -p "الرقم: " n
  case "$n" in ''|*[!0-9]*) n=1 ;; esac
  [ "$n" -ge 1 ] && [ "$n" -le ${#cards[@]} ] || n=1
  CARD="${cards[$((n-1))]}"
fi

say_line "📷 الكارت: $(basename "$CARD")"
echo "شتريد؟"
echo "  1) حط الفلاتر السبعة بالكارت"
echo "  2) احفظ نسخة من إعدادات الكاميرا على الماك"
echo "  3) رجّع الإعدادات المحفوظة للكارت"
read -r -p "اكتب 1 أو 2 أو 3 (Enter = 1): " choice
choice="${choice:-1}"

eject_card() {
  sync
  if command -v diskutil >/dev/null 2>&1 && [ -z "$VOLUMES_DIR" ]; then
    diskutil eject "$CARD" >/dev/null 2>&1 && say_line "✅ طلّعت الكارت. تگدر تسحبه هسه." \
      || say_line "طلّع الكارت من الماك (اسحبه لسلة المهملات) قبل ما تسحبه."
  fi
}

case "$choice" in
  1)
    dest="$CARD/PRIVATE/SONY/PRO/LUT"
    mkdir -p "$dest" || { say_line "❌ ما گدرت أكتب على الكارت. يمكن قفل الحماية مسدود (الزر الصغير بجنب الكارت)."; pause_exit 1; }
    n=0
    for f in "$LUTS"/[1-7].cube; do cp -f "$f" "$dest/" && n=$((n+1)); done
    say_line "✅ حطيت $n فلاتر بالكارت."
    eject_card
    say_line "هسه بالكاميرا: MENU > Exposure/Color > Color/Tone > Manage User LUTs > Import/Edit"
    echo "ودخّل 1.cube بـUser1، و2.cube بـUser2، لحد 7. (الخطوة 16 بالتطبيق)"
    ;;
  2)
    stamp="$(date +%Y-%m-%d_%H-%M)"
    out="$BACKUP/$stamp"
    found=0
    if [ -d "$CARD/PRIVATE/SONY" ]; then
      while IFS= read -r -d '' f; do
        rel="${f#"$CARD"/}"
        mkdir -p "$out/$(dirname "$rel")" && cp -p "$f" "$out/$rel" && found=$((found+1))
      done < <(find "$CARD/PRIVATE/SONY" -type f \( -iname '*.dat' -o -iname '*.set' -o -iname '*.cfg' \) -not -path '*/PRO/LUT/*' -print0)
    fi
    if [ "$found" -eq 0 ]; then
      say_line "ما لگيت ملف إعدادات بالكارت."
      echo "بالكاميرا أول: MENU > Setup > Reset/Save Settings > Save/Load Settings > Save New"
      echo "وبعدين دخّل الكارت وشغّلني من جديد."
      rmdir "$out" 2>/dev/null
    else
      say_line "✅ حفظت $found ملف بالماك، بمجلد:"
      echo "   $out"
      eject_card
    fi
    ;;
  3)
    [ -d "$BACKUP" ] || { say_line "ماكو نسخة محفوظة بعد. سوّي الخيار 2 أول."; pause_exit 1; }
    last="$(ls -1d "$BACKUP"/*/ 2>/dev/null | sort | tail -n 1)"
    [ -n "$last" ] || { say_line "ماكو نسخة محفوظة بعد. سوّي الخيار 2 أول."; pause_exit 1; }
    (cd "$last" && find . -type f -print0) | while IFS= read -r -d '' f; do
      mkdir -p "$CARD/$(dirname "${f#./}")" && cp -p "$last/${f#./}" "$CARD/${f#./}"
    done
    say_line "✅ رجّعت آخر نسخة ($(basename "$last")) للكارت."
    eject_card
    echo "هسه بالكاميرا: MENU > Setup > Reset/Save Settings > Save/Load Settings > Load"
    echo "(طلّع الكاميرا من وضع MR قبل، لأن بيه ما يشتغل.)"
    ;;
  *) say_line "اختيار غلط. شغّلني من جديد." ;;
esac
pause_exit 0
