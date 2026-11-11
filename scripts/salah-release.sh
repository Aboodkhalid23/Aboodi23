#!/usr/bin/env bash
# يرفع رقم نسخة تطبيق مواقيت الصلاة، حتى كل الأجهزة تحدّث نفسها تلقائياً من تنفتح.
# التشغيل قبل كل نشر: bash scripts/salah-release.sh
set -euo pipefail
cd "$(dirname "$0")/../links/salah"
old=$(tr -d '[:space:]' < version.txt); new=$((old + 1))
echo "$new" > version.txt
sed -i "s/var VERSION='$old';/var VERSION='$new';/" index.html
sed -i "s/salah-v$old'/salah-v$new'/" sw.js
grep -q "var VERSION='$new';" index.html && grep -q "salah-v$new'" sw.js || { echo "فشل تبديل رقم النسخة"; exit 1; }
echo "النسخة صارت $new"
