#!/usr/bin/env bash
# تسريع تابلت سامسونگ (Galaxy Tab A9) من الماك بوك، بدون روت وبدون ما يتغير النظام.
# الربط بالواي فاي (تصحيح الأخطاء اللاسلكي). الاستخدام (بالطرفية Terminal مال الماك):
#   bash <(curl -fsSL https://raw.githubusercontent.com/aboodkhalid23/aboodi23/claude/github-skills-development-3orc6c/scripts/tablet-speedup.sh)
# للتراجع ورجوع كل البرامج المحذوفة:
#   bash <(curl -fsSL ...نفس الرابط...) --restore
# للوضع الخفيف (بدون حركات + واجهة خفيفة بدل واجهة سامسونگ):
#   bash <(curl -fsSL ...نفس الرابط...) --lite
# لوضع قارئ النصوص (تلقين التصوير): الخفيف + حذف أكثر + شاشة ما تطفي + عدم الإزعاج:
#   bash <(curl -fsSL ...نفس الرابط...) --prompter
# للسرعة القصوى (قارئ النصوص + حذف خدمات الخلفية + منع البرامج الباقية من الشغل بالخلفية):
#   bash <(curl -fsSL ...نفس الرابط...) --extreme
# الأقوى (القصوى + تعطيل كل البرامج المنزّلة الي ما يحتاجها قارئ النصوص + ضبط الرام + قياس قبل وبعد):
#   bash <(curl -fsSL ...نفس الرابط...) --max

set -u

TOOLS_DIR="$HOME/android-tools"
ADB="$TOOLS_DIR/platform-tools/adb"
REMOVED_LIST="$TOOLS_DIR/removed.txt"
BG_LIST="$TOOLS_DIR/background-blocked.txt"
DISABLED_LIST="$TOOLS_DIR/disabled.txt"

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

# برامج زايدة إضافية لتابلت مخصص لقراءة النصوص بس. هم يرجعن بأمر --restore.
PROMPTER_BLOAT="
com.samsung.android.email.provider
com.samsung.android.calendar
com.samsung.android.app.reminder
com.samsung.android.app.notes
com.samsung.android.oneconnect
com.samsung.android.voc
com.samsung.android.themestore
com.samsung.android.app.dressroom
com.samsung.android.aircommandmanager
com.samsung.android.app.taskedge
com.samsung.android.app.cocktailbarservice
com.samsung.android.service.peoplestripe
com.samsung.android.kidsinstaller
com.sec.android.app.kidshome
com.sec.android.app.samsungapps
com.sec.android.app.popupcalculator
com.sec.android.app.clockpackage
com.samsung.android.video
com.google.android.youtube
com.google.android.apps.maps
com.google.android.apps.photos
com.google.android.apps.messaging
com.google.android.apps.googleassistant
com.google.android.googlequicksearchbox
"

# خدمات خلفية تاكل رام وبطارية، حذفها آمن ويرجع بأمر --restore
EXTREME_BLOAT="
com.samsung.android.rubin.app
com.samsung.android.smartsuggestions
com.samsung.android.app.galaxyfinder
com.samsung.android.bixby.service
com.samsung.android.app.settings.bixby
com.samsung.android.intellivoiceservice
com.samsung.android.svoiceime
com.samsung.android.mateagent
com.samsung.android.app.omcagent
com.samsung.android.beaconmanager
com.samsung.android.scloud
com.samsung.android.dqagent
com.samsung.android.samsungpass
com.samsung.android.samsungpassautofill
com.samsung.android.ipsgeofence
com.samsung.android.easysetup
com.samsung.android.privateshare
com.samsung.android.dynamiclock
com.samsung.android.allshare.service.mediashare
com.samsung.android.app.simplesharing
com.samsung.android.smartface
com.sec.android.easyMover
com.sec.android.app.chromecustomizations
com.sec.android.gallery3d
com.google.android.apps.turbo
com.google.android.apps.wellbeing
com.google.android.projection.gearhead
com.google.android.apps.subscriptions.red
com.google.ar.core
"

# برامج لازم تبقى تشتغل بالخلفية (ما ينمنعن)
KEEP_BG="com.android.chrome com.google.android.apps.docs com.google.android.gm com.android.vending app.lawnchair"

# الرام المستخدم بالگيگا (الكلي ناقص المتوفر)
ram_used() {
  "$ADB" shell cat /proc/meminfo </dev/null | tr -d '\r' | awk '
    /^MemTotal/ {t=$2} /^MemAvailable/ {a=$2}
    END {printf "%.1f من %.1f", (t-a)/1048576, t/1048576}'
}

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
  [ -f "$REMOVED_LIST" ] || [ -f "$BG_LIST" ] || [ -f "$DISABLED_LIST" ] || die "ماكو شي محذوف حتى أرجعه."
  touch "$REMOVED_LIST"
  say "دا أرجّع البرامج المحذوفة..."
  while read -r pkg; do
    [ -n "$pkg" ] && "$ADB" shell cmd package install-existing "$pkg" </dev/null >/dev/null 2>&1 && echo "  رجع: $pkg"
  done < "$REMOVED_LIST"
  rm -f "$REMOVED_LIST"
  if [ -f "$DISABLED_LIST" ]; then
    while read -r pkg; do
      [ -n "$pkg" ] && "$ADB" shell pm enable "$pkg" </dev/null >/dev/null 2>&1 && echo "  رجع: $pkg"
    done < "$DISABLED_LIST"
    rm -f "$DISABLED_LIST"
  fi
  "$ADB" shell device_config delete activity_manager max_cached_processes </dev/null >/dev/null 2>&1
  if [ -f "$BG_LIST" ]; then
    while read -r pkg; do
      [ -n "$pkg" ] && "$ADB" shell cmd appops set "$pkg" RUN_ANY_IN_BACKGROUND allow </dev/null >/dev/null 2>&1
    done < "$BG_LIST"
    rm -f "$BG_LIST"
  fi
  say "خلص. كل البرامج رجعت."
}

speedup() {
  model=$("$ADB" shell getprop ro.product.model | tr -d '\r')
  say "لگيت التابلت: $model"
  RAM_BEFORE=$(ram_used)
  echo "  الرام المستخدم هسه: $RAM_BEFORE گيگا"

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

  if [ "$PROMPTER" = 1 ]; then
    say "وضع قارئ النصوص: دا أحذف البرامج الي ما يحتاجها قارئ النصوص..."
    for pkg in $PROMPTER_BLOAT; do
      if "$ADB" shell pm uninstall -k --user 0 "$pkg" 2>/dev/null | grep -q Success; then
        echo "$pkg" >> "$REMOVED_LIST"
        echo "  انحذف: $pkg"
      fi
    done

    say "دا أضبط الشاشة للتصوير..."
    # الشاشة ما تطفي وهو على الشاحن، وبدونه تبقى 30 دقيقة
    "$ADB" shell settings put global stay_on_while_plugged_in 7
    "$ADB" shell settings put system screen_off_timeout 1800000
    # إضاءة ثابتة (التلقائية تتغير ويا ضوء التصوير وتشتت)
    "$ADB" shell settings put system screen_brightness_mode 0
    # الشاشة ما تدور وحدها إذا تحرك التابلت
    "$ADB" shell settings put system accelerometer_rotation 0
    # عدم الإزعاج: ماكو إشعارات تطلع فوق النص
    "$ADB" shell cmd notification set_dnd priority >/dev/null 2>&1
    # ما يدوّر على شبكات وأجهزة بالخلفية
    "$ADB" shell settings put global wifi_scan_always_enabled 0
    "$ADB" shell settings put global ble_scan_always_enabled 0
  fi

  if [ "$EXTREME" = 1 ]; then
    say "السرعة القصوى: دا أحذف خدمات الخلفية الي تاكل الرام..."
    for pkg in $EXTREME_BLOAT; do
      if "$ADB" shell pm uninstall -k --user 0 "$pkg" 2>/dev/null | grep -q Success; then
        echo "$pkg" >> "$REMOVED_LIST"
        echo "  انحذف: $pkg"
      fi
    done

    say "دا أمنع البرامج الباقية من الشغل بالخلفية..."
    for pkg in $("$ADB" shell pm list packages -3 | tr -d '\r' | cut -d: -f2); do
      case " $KEEP_BG " in *" $pkg "*) continue ;; esac
      "$ADB" shell cmd appops set "$pkg" RUN_ANY_IN_BACKGROUND ignore >/dev/null 2>&1 \
        && echo "$pkg" >> "$BG_LIST" && echo "  انمنع بالخلفية: $pkg"
    done
  fi

  if [ "$MAX" = 1 ]; then
    say "الأقوى: دا أعطّل البرامج المنزّلة الي ما يحتاجها قارئ النصوص..."
    for pkg in $("$ADB" shell pm list packages -3 | tr -d '\r' | cut -d: -f2); do
      case " $KEEP_BG " in *" $pkg "*) continue ;; esac
      case "$pkg" in *prompt*|*Prompt*) continue ;; esac
      "$ADB" shell pm disable-user --user 0 "$pkg" 2>/dev/null | grep -q "disabled" \
        && echo "$pkg" >> "$DISABLED_LIST" && echo "  تعطّل: $pkg"
    done

    say "دا أضبط الرام: أقل برامج محفوظة بالذاكرة، وتجميد البرامج النايمة..."
    "$ADB" shell device_config put activity_manager max_cached_processes 8 >/dev/null 2>&1
    "$ADB" shell settings put global cached_apps_freezer enabled
    # ما يحدّث البرامج وحده بنص التصوير
    "$ADB" shell settings put global auto_update_apps 0 >/dev/null 2>&1
  fi

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

  if [ "$MAX" = 1 ]; then
    say "دا أنتظر التابلت يشتغل حتى أقيس الرام (دقيقة تقريباً)..."
    "$ADB" wait-for-device
    sleep 60
    echo "  الرام قبل: $RAM_BEFORE گيگا"
    echo "  الرام بعد: $(ram_used) گيگا"
  fi

  echo
  echo "✔ خلص التسريع."
  echo "شغلة أخيرة بإيدك: الإعدادات ← العناية بالجهاز ← الذاكرة ← (RAM Plus) طفّيه."
  echo "إذا تريد ترجع البرامج المحذوفة: شغّل نفس الأمر وضيف بآخره --restore"
  if [ "$PROMPTER" = 1 ]; then
    echo "قارئ النصوص جاهز: الشاشة ما تطفي على الشاحن، وعدم الإزعاج شغّال، والدوران مقفول."
    echo "الإضاءة: نزّل شريط الإشعارات وخلّيها بالمستوى الي يريحك للتصوير."
  fi
  echo "وإذا تريد ترجع واجهة سامسونگ: الإعدادات ← التطبيقات ← اختيار التطبيقات الافتراضية ← تطبيق الشاشة الرئيسية ← One UI Home"
}

install_adb
connect
LITE=0
PROMPTER=0
EXTREME=0
MAX=0
[ "${1:-}" = "--lite" ] && LITE=1
[ "${1:-}" = "--prompter" ] && LITE=1 && PROMPTER=1
[ "${1:-}" = "--extreme" ] && LITE=1 && PROMPTER=1 && EXTREME=1
[ "${1:-}" = "--max" ] && LITE=1 && PROMPTER=1 && EXTREME=1 && MAX=1
if [ "${1:-}" = "--restore" ]; then restore; else speedup; fi
