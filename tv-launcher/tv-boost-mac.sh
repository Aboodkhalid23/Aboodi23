#!/bin/bash
# يسرّع التلفزيون من الماك. كل شي هنا ينرجع (ما يحذف تطبيقات ولا يمسح حسابات).
TV="${TV:-192.168.1.154}"
ADB="$HOME/AboodTV/platform-tools/adb"
[ -x "$ADB" ] || { echo "شغّل سطر التنصيب أول مرة وحدة."; exit 1; }
"$ADB" connect "$TV:5555" >/dev/null
# </dev/null: حتى adb ما ياكل باقي السكربت من curl
S() { "$ADB" -s "$TV:5555" shell "$@" </dev/null; }
main() {

echo "١) دا أخلي الحركات أسرع..."
S settings put global window_animation_scale 0.5
S settings put global transition_animation_scale 0.5
S settings put global animator_duration_scale 0.5

echo "٢) دا أوقف بحث الوايفاي والبلوتوث بالخلفية حتى النت ما يقطع..."
S settings put global wifi_scan_always_enabled 0
S settings put global ble_scan_always_enabled 0
S settings put global wifi_sleep_policy 2
S settings put global network_recommendations_enabled 0

echo "٣) دا أطفي التطبيقات الشغالة بالخلفية وأفضّي الكاش..."
S am kill-all
S pm trim-caches 999G

echo "٤) دا أترجم يوتيوب ونتفلكس ودار وسبوتيفاي لكود سريع (ياخذ دقايق، لا تطفي التلفزيون)..."
for p in com.google.android.youtube.tv com.netflix.ninja com.mbm_soft.darplayer com.spotify.tv.android com.aboodi.tvhome; do
  S pm path "$p" >/dev/null 2>&1 && { echo "   $p"; S cmd package compile -m speed -f "$p" >/dev/null; }
done

echo
echo "===== معلومات التلفزيون (انسخها ودزها لـ Claude) ====="
echo "الموديل: $(S getprop ro.product.manufacturer) $(S getprop ro.product.model)"
echo "أندرويد: $(S getprop ro.build.version.release)"
S cat /proc/meminfo | head -3
S df -h /data | tail -1
S cmd media_session volume --stream 3 --get 2>/dev/null | tail -1
echo "--- تطبيقات النظام المفعّلة ---"
S pm list packages -s -e | sed 's/package://' | sort | tr '\n' ' '
echo
echo "--- تطبيقاتك ---"
S pm list packages -3 | sed 's/package://' | sort | tr '\n' ' '
echo
echo "======================================================"

echo "٥) دا أفتحلك سبوتيفاي بالمتجر، اضغط تثبيت..."
S am start -a android.intent.action.VIEW -d "market://details?id=com.spotify.tv.android" >/dev/null
echo "٦) دا أفتحلك صفحة تحديث النظام، اضغط فحص التحديثات..."
S am start -a android.settings.SYSTEM_UPDATE_SETTINGS >/dev/null 2>&1
echo "خلص."
}
main
