#!/usr/bin/env bash
# تسريع تابلت سامسونگ (Galaxy Tab A9) من الماك بوك، بدون روت وبدون ما يتغير النظام.
# الربط بالواي فاي (تصحيح الأخطاء اللاسلكي). الاستخدام (بالطرفية Terminal مال الماك):
#   bash <(curl -fsSL https://raw.githubusercontent.com/aboodkhalid23/aboodi23/claude/github-skills-development-3orc6c/scripts/tablet-speedup.sh)
# للتراجع ورجوع كل البرامج المحذوفة:
#   bash <(curl -fsSL ...نفس الرابط...) --restore
# للوضع الخفيف (بدون حركات + واجهة خفيفة بدل واجهة سامسونگ):
#   bash <(curl -fsSL ...نفس الرابط...) --lite

set -u

TOOLS_DIR="$HOME/android-tools"
ADB="$TOOLS_DIR/platform-tools/adb"
REMOVED_LIST="$TOOLS_DIR/removed.txt"

# برامج تثگّل الجهاز وحذفها آمن. الحذف "للمستخدم" بس، فيرجع بأمر --restore.
BLOAT="
com.samsung.android.bixby.agent
com.samsung.android.bixby.wakeup
com.samsung.android.bixbyvision.framework
com.samsung.android.visionintelligence
com.samsung.android.app.routines
com.samsung.android.app.tips
com.samsung.android.app.spage
com.samsung.android.game.gamehome
com.samsung.android.game.gametools
com.samsung.android.game.gos
com.samsung.android.kidsinstaller
com.samsung.android.app.watchmanagerstub
com.samsung.android.stickercenter
com.samsung.android.ardrawing
com.samsung.android.aremoji
com.samsung.android.arzone
com.samsung.android.da.daagent
com.samsung.android.app.parentalcare
com.samsung.android.forest
com.samsung.android.livestickers
com.samsung.android.mdecservice
com.samsung.android.smartswitchassistant
com.samsung.android.tvplus
com.samsung.android.app.updatecenter
com.facebook.katana
com.facebook.appmanager
com.facebook.services
com.facebook.system
com.microsoft.skydrive
com.microsoft.office.officehubrow
com.linkedin.android
com.netflix.mediaclient
com.netflix.partner.activation
com.spotify.music
com.google.android.apps.tachyon
com.google.android.videos
com.google.android.apps.youtube.music
com.google.android.feedback
"

say() { printf '\n▶ %s\n' "$1"; }
die() { printf '\n✖ %s\n' "$1"; exit 1; }

install_adb() {
  if [ -x "$ADB" ]; then return; fi
  say "دا أنزّل أداة الربط ويا الأندرويد من گوگل (مرة وحدة بس)..."
  mkdir -p "$TOOLS_DIR"
  curl -fsSL -o "$TOOLS_DIR/pt.zip" \
    https://dl.google.com/android/repository/platform-tools-latest-darwin.zip \
    || die "ما گدرت أنزّل الأداة. تأكد من الإنترنت وعيد."
  unzip -qo "$TOOLS_DIR/pt.zip" -d "$TOOLS_DIR" && rm -f "$TOOLS_DIR/pt.zip"
  xattr -dr com.apple.quarantine "$TOOLS_DIR/platform-tools" 2>/dev/null
  [ -x "$ADB" ] || die "الأداة ما اشتغلت."
}

# يدوّر على التابلت بالشبكة ويطلع العنوان والمنفذ وحده (نوع الخدمة: إقران أو ربط)
find_service() {
  "$ADB" mdns services 2>/dev/null | awk -v t="$1" '$0 ~ t {print $NF; exit}'
}

is_connected() {
  "$ADB" devices | awk 'NR>1 && $2=="device"' | grep -q .
}

connect() {
  "$ADB" start-server >/dev/null 2>&1
  if is_connected; then return; fi

  # إذا انقرن قبل، يرتبط وحده بدون رمز
  addr=$(find_service _adb-tls-connect)
  if [ -n "$addr" ]; then
    "$ADB" connect "$addr" >/dev/null 2>&1
    sleep 2
    if is_connected; then return; fi
  fi

  echo
  echo "الماك والتابلت لازم يكونون على نفس الواي فاي."
  echo
  echo "بالتابلت:"
  echo "  1. الإعدادات ← خيارات المطوّر ← (تصحيح الأخطاء اللاسلكي) ← فعّل الزر"
  echo "  2. اضغط على الكلمة نفسها (تصحيح الأخطاء اللاسلكي) حتى تنفتح صفحتها"
  echo "  3. اضغط (إقران الجهاز برمز الإقران) وخلّي النافذة مفتوحة"
  echo
  printf "اضغط إنتر لما تنفتح نافذة الرمز..."
  read -r _

  say "دا أدوّر على التابلت بالشبكة..."
  pair_addr=""
  for _ in $(seq 1 15); do
    pair_addr=$(find_service _adb-tls-pairing)
    [ -n "$pair_addr" ] && break
    sleep 2
  done

  if [ -n "$pair_addr" ]; then
    echo "  ✔ لگيته: $pair_addr"
  else
    echo "  ما لگيته وحدي. اكتبه إنت:"
    printf "  اكتب السطر الي تحت الرمز بالنافذة كامل، مثل 192.168.1.64:41235 : "
    read -r pair_addr
    case "$pair_addr" in
      *:*) ;;
      *) die "لازم يكون وياه نقطتين ورقم بعدها. إذا ما تشوفه، صوّر النافذة ودزها." ;;
    esac
  fi

  printf "اكتب رمز الإقران الي بالنافذة (6 أرقام): "
  read -r code
  "$ADB" pair "$pair_addr" "$code" 2>&1 | grep -qi success \
    || die "الإقران فشل. سدّ النافذة وافتحها من جديد (الرمز يتغير)، وعيد."
  echo "  ✔ انقرن."

  say "دا أربط..."
  for _ in $(seq 1 10); do
    if is_connected; then return; fi
    addr=$(find_service _adb-tls-connect)
    [ -n "$addr" ] && "$ADB" connect "$addr" >/dev/null 2>&1
    sleep 2
  done

  # آخر حل: يكتبه بإيده
  ip=${pair_addr%:*}
  echo "  سدّ نافذة الإقران. بصفحة تصحيح الأخطاء اللاسلكي، تحت (عنوان IP والمنفذ)، أكو رقم بعد النقطتين."
  printf "  اكتب هذا الرقم بس: "
  read -r port
  "$ADB" connect "$ip:$port" >/dev/null 2>&1
  sleep 2
  is_connected || die "ما گدرت أربط. تأكد الماك والتابلت على نفس الواي فاي وعيد."
}

# يحط واجهة Lawnchair الخفيفة (مفتوحة المصدر) بدل واجهة سامسونگ، ويخليها الافتراضية
install_light_home() {
  say "دا أنزّل واجهة خفيفة اسمها Lawnchair..."
  url=$(curl -fsSL "https://api.github.com/repos/LawnchairLauncher/lawnchair/releases?per_page=5" \
    | grep -o '"browser_download_url": *"[^"]*\.apk"' | head -1 | sed 's/.*"\(http[^"]*\)"/\1/')
  if [ -z "$url" ] || ! curl -fsSL -o "$TOOLS_DIR/home.apk" "$url"; then
    echo "  ما گدرت أنزّلها. نزّل من سوگ پلي برنامج (Niagara Launcher) وخلّيه الافتراضي."
    return
  fi
  "$ADB" install -r "$TOOLS_DIR/home.apk" >/dev/null 2>&1 || { echo "  التثبيت فشل."; return; }
  rm -f "$TOOLS_DIR/home.apk"
  pkg=$("$ADB" shell pm list packages | tr -d '\r' | grep -i lawnchair | head -1 | cut -d: -f2)
  comp=$("$ADB" shell cmd package resolve-activity --brief -a android.intent.action.MAIN \
    -c android.intent.category.HOME "$pkg" | tr -d '\r' | tail -1)
  if [ -n "$pkg" ] && "$ADB" shell cmd package set-home-activity "$comp" >/dev/null 2>&1; then
    echo "  ✔ صارت الواجهة الافتراضية."
  else
    echo "  انثبتت. لما يشتغل التابلت اضغط زر البيت واختار Lawnchair ثم (دائماً)."
  fi
}

restore() {
  [ -f "$REMOVED_LIST" ] || die "ماكو برامج محذوفة حتى أرجعها."
  say "دا أرجّع البرامج المحذوفة..."
  while read -r pkg; do
    [ -n "$pkg" ] && "$ADB" shell cmd package install-existing "$pkg" >/dev/null 2>&1 && echo "  رجع: $pkg"
  done < "$REMOVED_LIST"
  rm -f "$REMOVED_LIST"
  say "خلص. كل البرامج رجعت."
}

speedup() {
  model=$("$ADB" shell getprop ro.product.model | tr -d '\r')
  say "لگيت التابلت: $model"

  say "دا أسرّع الحركات (نصّ الوقت)..."
  for k in window_animation_scale transition_animation_scale animator_duration_scale; do
    "$ADB" shell settings put global "$k" 0.5
  done

  say "دا أحذف البرامج الي تثگّل الجهاز..."
  count=0
  for pkg in $BLOAT; do
    if "$ADB" shell pm uninstall -k --user 0 "$pkg" 2>/dev/null | grep -q Success; then
      echo "$pkg" >> "$REMOVED_LIST"
      echo "  انحذف: $pkg"
      count=$((count + 1))
    fi
  done
  echo "  عدد المحذوفة: $count"

  say "دا أنظّف الملفات المؤقتة لكل البرامج..."
  "$ADB" shell pm trim-caches 999G >/dev/null 2>&1
  "$ADB" shell sm fstrim >/dev/null 2>&1

  say "دا أطفي تأثيرات الضبابية حتى تخف الشاشة..."
  "$ADB" shell settings put global disable_window_blurs 1
  "$ADB" shell settings put global accessibility_reduce_transparency 1

  say "دا أسد البرامج الشغالة بالخلفية..."
  "$ADB" shell am kill-all >/dev/null 2>&1

  say "دا أرتّب البرامج حتى تفتح أسرع (ياخذ من 5 لـ 15 دقيقة، لا تفصل التابلت)..."
  "$ADB" shell cmd package bg-dexopt-job >/dev/null 2>&1

  if [ "$LITE" = 1 ]; then
    say "الوضع الخفيف: دا أطفي الحركات كلياً..."
    for k in window_animation_scale transition_animation_scale animator_duration_scale; do
      "$ADB" shell settings put global "$k" 0
    done
    install_light_home
  fi

  say "دا أعيد تشغيل التابلت..."
  "$ADB" reboot

  echo
  echo "✔ خلص التسريع."
  echo "شغلة أخيرة بإيدك: الإعدادات ← العناية بالجهاز ← الذاكرة ← (RAM Plus) طفّيه."
  echo "إذا تريد ترجع البرامج المحذوفة: شغّل نفس الأمر وضيف بآخره --restore"
  echo "وإذا تريد ترجع واجهة سامسونگ: الإعدادات ← التطبيقات ← اختيار التطبيقات الافتراضية ← تطبيق الشاشة الرئيسية ← One UI Home"
}

install_adb
connect
LITE=0
[ "${1:-}" = "--lite" ] && LITE=1
if [ "${1:-}" = "--restore" ]; then restore; else speedup; fi
