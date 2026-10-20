#!/bin/bash
# ينصب شاشة عبود على التلفزيون من ماك على نفس الوايفاي
set -e
TV="${TV:-192.168.1.154}"
DIR="$HOME/AboodTV"
mkdir -p "$DIR" && cd "$DIR"
if [ ! -x platform-tools/adb ]; then
  echo "دا انزّل ادوات اندرويد..."
  curl -sSLo pt.zip https://dl.google.com/android/repository/platform-tools-latest-darwin.zip
  unzip -qo pt.zip && rm pt.zip
fi
ADB="$DIR/platform-tools/adb"
echo "دا انزّل الواجهة..."
curl -sSLo AboodTV.apk "https://github.com/Aboodkhalid23/Aboodi23/raw/claude/project-thread-4ztr10/tv-launcher/release/AboodTV.apk?t=$(date +%s)"
"$ADB" connect "$TV:5555" || true
echo
echo "اذا طلعت رسالة بالتلفزيون: اضغط سماح ودائما. وبعدها اضغط Enter هنا."
read -r < /dev/tty
"$ADB" connect "$TV:5555"
"$ADB" -s "$TV:5555" install -r AboodTV.apk </dev/null
"$ADB" -s "$TV:5555" shell cmd package set-home-activity com.aboodi.tvhome/.MainActivity </dev/null || true
"$ADB" -s "$TV:5555" shell am start -n com.aboodi.tvhome/.MainActivity </dev/null
echo
echo "خلص. شوف التلفزيون."
