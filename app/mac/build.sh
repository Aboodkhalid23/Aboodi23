#!/bin/bash
# يبني تطبيق المونتير للماك (يشتغل على جهاز ماك بالسحابة: .github/workflows/mac-app.yml).
#   app/mac/build.sh [النسخة]   →   app/mac/build/Montier.dmg
# One binary for both chips (Apple and Intel), signed ad hoc (free; the owner opens it once from Settings).
set -euo pipefail
cd "$(dirname "$0")"
VERSION="${1:-1.0}"
OUT=build; APP="$OUT/المونتير.app"
rm -rf "$OUT"; mkdir -p "$APP/Contents/MacOS" "$APP/Contents/Resources"

for arch in arm64 x86_64; do
  swiftc -O -target "$arch-apple-macos12" App.swift -o "$OUT/Montier-$arch" -framework Cocoa -framework WebKit
done
lipo -create -output "$APP/Contents/MacOS/Montier" "$OUT/Montier-arm64" "$OUT/Montier-x86_64"
rm -f "$OUT"/Montier-*

cp Info.plist "$APP/Contents/Info.plist"
/usr/libexec/PlistBuddy -c "Set :CFBundleShortVersionString $VERSION" -c "Set :CFBundleVersion $VERSION" "$APP/Contents/Info.plist"
cp setup.html "$APP/Contents/Resources/"
cp ../setup.sh "$APP/Contents/Resources/"

ICONSET="$OUT/AppIcon.iconset"; mkdir -p "$ICONSET"
for s in 16 32 128 256 512; do
  sips -z $s $s icon.png --out "$ICONSET/icon_${s}x${s}.png" >/dev/null
  sips -z $((s * 2)) $((s * 2)) icon.png --out "$ICONSET/icon_${s}x${s}@2x.png" >/dev/null
done
iconutil -c icns "$ICONSET" -o "$APP/Contents/Resources/AppIcon.icns"
rm -rf "$ICONSET"

codesign --force --deep --sign - "$APP"
codesign --verify --verbose "$APP"

DMG_DIR="$OUT/dmg"; mkdir -p "$DMG_DIR"
cp -R "$APP" "$DMG_DIR/"
ln -s /Applications "$DMG_DIR/Applications"
hdiutil create -volname "المونتير" -srcfolder "$DMG_DIR" -ov -format UDZO "$OUT/Montier.dmg" >/dev/null
rm -rf "$DMG_DIR"
echo "✅ $OUT/Montier.dmg ($(du -h "$OUT/Montier.dmg" | cut -f1))"
