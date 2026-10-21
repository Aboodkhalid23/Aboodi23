#!/bin/bash
# ملف تسريع التلفزيون الشامل. ينحط على سطح المكتب باسم "تسريع التلفزيون" وتشغّله بدبل كلك كل ما تحس التلفزيون ثقل.
# كل شي ينرجع: "تسريع التلفزيون.command undo" يرجّع كلشي مثل ما چان.
TV="${TV:-192.168.1.154}"
DIR="$HOME/AboodTV"
RAW="https://github.com/Aboodkhalid23/Aboodi23/raw/claude/project-thread-4ztr10/tv-launcher"
ADB="$DIR/platform-tools/adb"
# تطبيقات نظام زايدة تشتغل بالخلفية وتسحب نت ورام. نوقفها بس (ما تنحذف).
EXTRA="com.google.android.tvrecommendations com.google.android.leanbacklauncher.recommendations com.google.android.play.games com.google.android.videos com.google.android.music com.google.android.feedback com.google.android.backdrop com.android.printspooler com.google.android.tvlauncher"
# هذني ما نخليها تشتغل بالخلفية بعد ما تطلع منها.
NOBG="com.google.android.youtube.tv com.netflix.ninja com.mxtech.videoplayer.ad com.esaba.downloader"
# هذني ممنوع يستخدمن النت بالخلفية (يشتغلن عادي لما تفتحهن).
NONET="com.google.android.play.games com.google.android.videos com.google.android.music com.google.android.youtube.tvmusic com.google.android.apps.youtube.music com.amazon.amazonvideo.livingroom com.disney.disneyplus"
FASTAPPS="com.google.android.youtube.tv com.netflix.ninja com.mbm_soft.darplayer com.spotify.tv.android com.aboodi.tvhome"

S() { "$ADB" -s "$TV:5555" shell "$@" </dev/null; }

setup_mac() {
  mkdir -p "$DIR"
  if [ ! -x "$ADB" ]; then
    echo "دا انزّل ادوات اندرويد..."
    curl -sSLo "$DIR/pt.zip" https://dl.google.com/android/repository/platform-tools-latest-darwin.zip
    unzip -qo "$DIR/pt.zip" -d "$DIR" && rm "$DIR/pt.zip"
  fi
  # نحفظ الملف على سطح المكتب حتى بعدين بس تدبل كلك عليه
  curl -sSLo "$HOME/Desktop/تسريع التلفزيون.command" "$RAW/tv-fast-mac.sh?t=$(date +%s)" && chmod +x "$HOME/Desktop/تسريع التلفزيون.command"
}

connect() {
  "$ADB" connect "$TV:5555" </dev/null | grep -q connected || {
    echo "ما گدرت أوصل للتلفزيون. تأكد التلفزيون شغال وعلى نفس الوايفاي، وإذا طلعت رسالة بالتلفزيون اضغط سماح."
    exit 1; }
}

# فحص مشكلة الصوت والشاشة الخضرة: يجمع سجل التلفزيون بملف على سطح المكتب
report() {
  OUT="$HOME/Desktop/تقرير-التلفزيون.txt"
  echo "دا أجمع معلومات التلفزيون..."
  {
    echo "== الجهاز =="
    for k in ro.product.manufacturer ro.product.model ro.build.version.release ro.build.fingerprint; do echo "$k=$(S getprop $k)"; done
    echo "== إعدادات الصوت =="
    for k in encoded_surround_output hdmi_control_enabled hdmi_system_audio_control_enabled; do echo "$k=$(S settings get global $k)"; done
    echo "== أجهزة الصوت =="
    S dumpsys audio | grep -iE "devices|output|hdmi|arc|a2dp|bluetooth|spdif|usb" | head -60
    echo "== HDMI =="
    S dumpsys hdmi_control 2>/dev/null | head -80
    echo "== بلوتوث =="
    S dumpsys bluetooth_manager 2>/dev/null | grep -iE "name|state|connected|a2dp|codec" | head -40
    echo "== أخطاء الصوت والصورة =="
    S logcat -d -b main,system,crash 2>/dev/null | grep -iE "hdmi|cec|arc|audio|underrun|codec|hwc|hdcp|a2dp|bluetooth|display|vsync|panel|crash|fatal" | tail -600
  } > "$OUT" 2>&1
  echo "خلص ✅ الملف: تقرير-التلفزيون.txt على سطح المكتب. دزه بالمحادثة."
}

undo() {
  for p in $EXTRA; do S pm enable "$p" >/dev/null 2>&1; done
  for p in $NOBG; do S cmd appops set "$p" RUN_ANY_IN_BACKGROUND allow >/dev/null 2>&1; done
  for k in window_animation_scale transition_animation_scale animator_duration_scale; do S settings put global $k 1; done
  S settings put global wifi_scan_always_enabled 1
  S settings put global encoded_surround_output 0
  for p in $NOBG $NONET; do
    U=$(S pm list packages -U "$p" 2>/dev/null | tr -d '\r' | grep "package:$p " | sed 's/.*uid://')
    [ -n "$U" ] && S cmd netpolicy remove restrict-background-blacklist "$U" >/dev/null 2>&1
  done
  echo "رجّعت كلشي مثل ما چان."
}

main() {
  setup_mac
  connect
  [ "$1" = "undo" ] && { undo; return; }
  [ "$1" = "report" ] && { report; return; }

  echo "١) دا أحدّث شاشة عبود لآخر نسخة..."
  curl -sSLo "$DIR/AboodTV.apk" "$RAW/release/AboodTV.apk?t=$(date +%s)" && "$ADB" -s "$TV:5555" install -r "$DIR/AboodTV.apk" </dev/null >/dev/null && echo "   تمام"

  # نسمح لشاشة عبود تنصب تحديثاتها بنفسها (بعد ما توافق بالتلفزيون)
  S appops set com.aboodi.tvhome REQUEST_INSTALL_PACKAGES allow >/dev/null 2>&1

  # زر الريستارت بالشاشة يحتاج خدمة صغيرة تفتح قائمة الطاقة. نشغلها (ونخلي أي خدمة ثانية مثل ما هي)
  SVC=com.aboodi.tvhome/com.aboodi.tvhome.PowerService
  CUR=$(S settings get secure enabled_accessibility_services | tr -d '\r')
  case "$CUR" in *"$SVC"*) ;; ""|null) S settings put secure enabled_accessibility_services "$SVC" ;; *) S settings put secure enabled_accessibility_services "$CUR:$SVC" ;; esac
  S settings put secure accessibility_enabled 1

  # صورك الخاصة: إذا نزّلت ملف AboodTV-my-walls.zip بالتنزيلات، ننقلها للتلفزيون
  if [ -f "$HOME/Downloads/AboodTV-my-walls.zip" ]; then
    echo "   دا أنقل صورك للتلفزيون..."
    rm -rf "$DIR/mywalls" && mkdir -p "$DIR/mywalls" && unzip -qo "$HOME/Downloads/AboodTV-my-walls.zip" -d "$DIR/mywalls"
    W=/sdcard/Android/data/com.aboodi.tvhome/files/mywalls
    S mkdir -p "$W"
    for f in "$DIR"/mywalls/*; do "$ADB" -s "$TV:5555" push "$f" "$W/" </dev/null >/dev/null; done
    echo "   تمام"
  fi

  echo "٢) دا أوقف تطبيقات النظام الزايدة (ما تنحذف)..."
  for p in $EXTRA; do
    S pm path "$p" 2>/dev/null | grep -q package && S pm disable-user --user 0 "$p" >/dev/null 2>&1 && echo "   وگّفت $p"
  done

  echo "٣) دا أمنع التطبيقات تشتغل بالخلفية بعد ما تطلع منها..."
  for p in $NOBG; do S cmd appops set "$p" RUN_ANY_IN_BACKGROUND ignore >/dev/null 2>&1; done
  S am kill-all

  echo "   وأمنعها تسحب نت بالخلفية، حتى وقت المباراة كل النت يروح للي مفتوح قدامك..."
  for p in $NOBG $NONET; do
    U=$(S pm list packages -U "$p" 2>/dev/null | tr -d '\r' | grep "package:$p " | sed 's/.*uid://')
    [ -n "$U" ] && S cmd netpolicy add restrict-background-blacklist "$U" >/dev/null 2>&1
  done

  echo "٤) دا أسرّع الحركات..."
  # فتح وسكر التطبيقات بدون حركة (فوري)، وحركات داخل التطبيقات بنص الوكت
  S settings put global window_animation_scale 0
  S settings put global transition_animation_scale 0
  S settings put global animator_duration_scale 0.5
  # تجميد التطبيقات رجعناه للأصل: ممكن يوقف جزء من مشغل دار ويقطع البث
  S settings delete global cached_apps_freezer >/dev/null 2>&1

  # دار: نخليه دائماً مسموح يشتغل وياخذ نت بدون أي تقييد من النظام، حتى البث ما يقطع
  DAR=com.mbm_soft.darplayer
  if S pm path $DAR 2>/dev/null | grep -q package; then
    S cmd appops set $DAR RUN_ANY_IN_BACKGROUND allow >/dev/null 2>&1
    S cmd appops set $DAR RUN_IN_BACKGROUND allow >/dev/null 2>&1
    S dumpsys deviceidle whitelist +$DAR >/dev/null 2>&1
    S am set-standby-bucket $DAR active >/dev/null 2>&1
    U=$(S pm list packages -U $DAR 2>/dev/null | tr -d '\r' | grep "package:$DAR " | sed 's/.*uid://')
    [ -n "$U" ] && { S cmd netpolicy remove restrict-background-blacklist "$U"; S cmd netpolicy add restrict-background-whitelist "$U"; } >/dev/null 2>&1
    echo "   دار صار له أولوية بالنت والتشغيل"
  fi

  echo "٥) دا أثبّت الوايفاي حتى ما يقطع..."
  S settings put global wifi_scan_always_enabled 0
  S settings put global ble_scan_always_enabled 0
  S settings put global wifi_sleep_policy 2
  S settings put global network_recommendations_enabled 0

  echo "   ودا أثبّت الصوت: الصوت يطلع للسماعة بشكل عادي (PCM) بدل الصيغ المضغوطة الي تسبب انقطاع ووشة"
  S settings put global encoded_surround_output 1

  echo "٦) دا أفضّي الذاكرة من الملفات المؤقتة..."
  S pm trim-caches 999G

  echo "٧) دا أخلي التطبيقات تفتح أسرع (أول مرة ياخذ دقايق، لا تطفي التلفزيون)..."
  for p in $FASTAPPS; do
    S pm path "$p" 2>/dev/null | grep -q package && { echo "   $p"; S cmd package compile -m speed "$p" >/dev/null 2>&1; }
  done

  S am start -n com.aboodi.tvhome/.MainActivity >/dev/null
  echo
  echo "الذاكرة الفاضية: $(S cat /proc/meminfo | awk '/MemAvailable/{printf "%d ميگا", $2/1024}')"
  echo "المساحة: $(S df -h /data | tail -1 | awk '{print $4" فاضية من "$2}')"
  echo
  echo "خلص ✅ شغّل هذا الملف كل ما تحس التلفزيون ثقل، أو بعد ما تحدّث تطبيقات."
}
main "$@"; exit
