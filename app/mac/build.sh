#!/bin/bash
# يبني تطبيق URU للماك (يشتغل على جهاز ماك بالسحابة: .github/workflows/mac-app.yml).
#   app/mac/build.sh [النسخة]   →   app/mac/build/URU.dmg
# One binary for both chips (Apple and Intel), signed ad hoc (free; the owner opens it once from Settings).
set -euo pipefail
cd "$(dirname "$0")"
VERSION="${1:-2.1.0}"
OUT=build; APP="$OUT/URU.app"
rm -rf "$OUT"; mkdir -p "$APP/Contents/MacOS" "$APP/Contents/Resources"

for arch in arm64 x86_64; do
  swiftc -O -target "$arch-apple-macos12" App.swift -o "$OUT/URU-$arch" -framework Cocoa -framework WebKit
done
lipo -create -output "$APP/Contents/MacOS/URU" "$OUT/URU-arm64" "$OUT/URU-x86_64"
rm -f "$OUT"/URU-*

cp Info.plist "$APP/Contents/Info.plist"
/usr/libexec/PlistBuddy -c "Set :CFBundleShortVersionString $VERSION" -c "Set :CFBundleVersion $VERSION" "$APP/Contents/Info.plist"
cp setup.html ../../editor/app/ui/logo.png "$APP/Contents/Resources/"
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
hdiutil create -volname "URU" -srcfolder "$DMG_DIR" -ov -format UDZO "$OUT/URU.dmg" >/dev/null
echo "$VERSION" > "$OUT/app-version.txt"
rm -rf "$DMG_DIR"
echo "✅ $OUT/URU.dmg ($(du -h "$OUT/URU.dmg" | cut -f1))"
