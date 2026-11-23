#!/bin/bash
# يخلي زر البيت يفتح شاشة عبود: يوقف الواجهة القديمة (ما يحذفها، وترجع بسطر الإرجاع).
TV="${TV:-192.168.1.154}"
ADB="$HOME/AboodTV/platform-tools/adb"
main() {
  "$ADB" connect "$TV:5555" >/dev/null </dev/null
  if [ "$1" = "undo" ]; then
    "$ADB" -s "$TV:5555" shell pm enable com.google.android.tvlauncher </dev/null
    echo "رجعت الواجهة القديمة."
    return
  fi
  "$ADB" -s "$TV:5555" shell pm path com.aboodi.tvhome </dev/null | grep -q package || { echo "شاشة عبود مو منصبة، شغّل سطر التنصيب أول."; return 1; }
  "$ADB" -s "$TV:5555" shell pm disable-user --user 0 com.google.android.tvlauncher </dev/null
  "$ADB" -s "$TV:5555" shell input keyevent KEYCODE_HOME </dev/null
  echo "خلص. اضغط زر البيت بالريموت."
}
main "$@"
