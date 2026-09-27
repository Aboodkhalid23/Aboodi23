#!/usr/bin/env bash
# يجهز أدوات المونتير (ffmpeg، مكتبات بايثون، Remotion). آمن تعيد تشغيله.
set -e
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
if ! command -v ffmpeg >/dev/null; then
  apt-get update -qq || true
  apt-get install -y -qq ffmpeg
fi
pip install -q -r "$ROOT/editor/requirements.txt"
if [ -f "$ROOT/editor/remotion/package-lock.json" ] && [ ! -d "$ROOT/editor/remotion/node_modules" ]; then
  npm ci --prefix "$ROOT/editor/remotion" --silent
fi
