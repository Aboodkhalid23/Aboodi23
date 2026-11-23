#!/usr/bin/env bash
# يبني ملف التنصيب (APK) بدون Gradle وبدون أي مكتبة من برّه.
# الاستخدام: ANDROID_HOME=/مسار/الـSDK ./build.sh
set -euo pipefail
cd "$(dirname "$0")"
SDK="${ANDROID_HOME:-/opt/android-sdk}"
BT="$SDK/build-tools/35.0.0"
JAR="$SDK/platforms/android-34/android.jar"
OUT=build
rm -rf "$OUT" && mkdir -p "$OUT/classes" "$OUT/dex"

"$BT/aapt2" compile --dir res -o "$OUT/res.zip"
"$BT/aapt2" link -o "$OUT/base.apk" -I "$JAR" --manifest AndroidManifest.xml \
  --java "$OUT/gen" "$OUT/res.zip" --min-sdk-version 21 --target-sdk-version 34
javac --release 8 -nowarn -encoding UTF-8 \
  -cp "$JAR" -d "$OUT/classes" $(find src "$OUT/gen" -name '*.java')
"$BT/d8" --release --min-api 21 --lib "$JAR" --output "$OUT/dex" $(find "$OUT/classes" -name '*.class')
cp "$OUT/base.apk" "$OUT/unsigned.apk"
(cd "$OUT/dex" && zip -q -j ../unsigned.apk classes.dex)
"$BT/zipalign" -f -p 4 "$OUT/unsigned.apk" "$OUT/aligned.apk"
# مفتاح تجريبي عام (مو سر): نفس المفتاح كل مرة حتى التحديث ينصب فوگ النسخة القديمة
"$BT/apksigner" sign --ks debug.keystore --ks-pass pass:android --key-pass pass:android \
  --ks-key-alias androiddebugkey --out "$OUT/AboodTV.apk" "$OUT/aligned.apk"
echo "تم: $OUT/AboodTV.apk ($(du -h "$OUT/AboodTV.apk" | cut -f1))"
