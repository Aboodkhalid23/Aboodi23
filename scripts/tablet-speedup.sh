#!/usr/bin/env bash
# تسريع تابلت سامسونگ (Galaxy Tab A9) من الماك بوك، بدون روت وبدون ما يتغير النظام.
# الاستخدام (بالطرفية Terminal مال الماك):
#   bash <(curl -fsSL https://raw.githubusercontent.com/aboodkhalid23/aboodi23/claude/github-skills-development-3orc6c/scripts/tablet-speedup.sh)
# للتراجع ورجوع كل البرامج المحذوفة:
#   bash <(curl -fsSL ...نفس الرابط...) --restore

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

connect() {
  echo
  echo "شلون تريد تربط التابلت؟"
  echo "  1) بالكيبل (أسهل)"
  echo "  2) بالواي فاي"
  printf "اكتب 1 أو 2 واضغط إنتر: "
  read -r way

  if [ "$way" = "2" ]; then
    echo
    echo "بالتابلت: الإعدادات ← خيارات المطوّر ← تصحيح الأخطاء اللاسلكي ← شغّله"
    echo "بعدين اضغط: إقران الجهاز برمز الإقران"
    printf "اكتب العنوان والمنفذ الي يطلعلك بشاشة الإقران (مثل 192.168.1.5:37123): "
    read -r pair_addr
    "$ADB" pair "$pair_addr" || die "الإقران فشل. تأكد الرقم صح وعيد."
    echo
    printf "هسه اكتب العنوان والمنفذ الي بالشاشة الرئيسية لتصحيح الأخطاء اللاسلكي (مو مال الإقران): "
    read -r conn_addr
    "$ADB" connect "$conn_addr" >/dev/null
  else
    echo
    echo "بالتابلت: الإعدادات ← خيارات المطوّر ← شغّل (تصحيح أخطاء USB)"
    echo "اربط الكيبل، وإذا طلعلك سؤال على التابلت اضغط (سماح)."
    printf "اضغط إنتر لما تربط..."
    read -r _
  fi

  say "دا أنتظر التابلت..."
  for _ in $(seq 1 30); do
    state=$("$ADB" get-state 2>&1)
    case "$state" in
      device) return ;;
      *unauthorized*) echo "  وافق على رسالة السماح الي طلعت على التابلت..." ;;
    esac
    sleep 2
  done
  die "ما لگيت التابلت. تأكد إنك شغلت تصحيح الأخطاء وعيد."
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

  say "دا أرتّب البرامج حتى تفتح أسرع (ياخذ من 5 لـ 15 دقيقة، لا تفصل التابلت)..."
  "$ADB" shell cmd package bg-dexopt-job >/dev/null 2>&1

  say "دا أعيد تشغيل التابلت..."
  "$ADB" reboot

  echo
  echo "✔ خلص التسريع."
  echo "شغلة أخيرة بإيدك: الإعدادات ← العناية بالجهاز ← الذاكرة ← (RAM Plus) طفّيه."
  echo "إذا تريد ترجع البرامج المحذوفة: شغّل نفس الأمر وضيف بآخره --restore"
}

install_adb
connect
if [ "${1:-}" = "--restore" ]; then restore; else speedup; fi
