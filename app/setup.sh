#!/bin/bash
# ينصّب URU (المونتير) على الماك (وعلى لينكس للاختبار) بدون صلاحيات مدير وبدون فلوس، وآمن تعيد تشغيله.
#   app/setup.sh            أول تنصيب (التطبيق يشغله لحاله)
#   app/setup.sh --update   يجيب آخر نسخة من الكود وينصب الجديد بس
#   app/setup.sh --app <pid التطبيق القديم> <pid المحرك> <مسار التطبيق القديم>   يبدّل التطبيق نفسه (الاسم والشعار) بآخر نسخة
#   app/setup.sh --app quiet                يبدّل التطبيق بصمت (وقت ما يتسكّر) بلا ما يفتحه
#   app/setup.sh --stage                    يجهّز آخر نسخة من الكود بصمت بـ code.next (تتبدّل وقت ما يتسكّر التطبيق)
# كل شي يروح لمجلد واحد ($MONTIER_HOME): الأدوات، والكود. الحلقات بمجلد ثاني وما تنمس.
# للاختبار: MONTIER_CODE_SRC=<مسار ريبو محلي>  MONTIER_SKIP_CLAUDE=1  MONTIER_SKIP_MODEL=1
# Written for the bash 3.2 that ships with macOS: no associative arrays, no ${x,,}.
set -euo pipefail

REPO="aboodkhalid23/aboodi23"
BRANCH="${MONTIER_BRANCH:-claude/video-editing-skills-vd37x3}"
PY_VERSION="3.11"
NODE_VERSION="22.22.2"
FFMPEG_ARM="https://ffmpeg.martin-riedl.de/download/macos/arm64/1789931890_9.0.2"
FFMPEG_INTEL="https://ffmpeg.martin-riedl.de/download/macos/amd64/1789931006_9.0.2"

OS="$(uname -s)"; ARCH="$(uname -m)"
if [ "$OS" = "Darwin" ]; then
  HOME_DIR="${MONTIER_HOME:-$HOME/Library/Application Support/Montier}"
else
  HOME_DIR="${MONTIER_HOME:-$HOME/.local/share/montier}"
fi
TOOLS="$HOME_DIR/tools"; CODE="$HOME_DIR/code"; TMP="$HOME_DIR/tmp"
UPDATE=0; [ "${1:-}" = "--update" ] && UPDATE=1
TOTAL=8; N=0
mkdir -p "$TOOLS/bin" "$HOME_DIR/logs" "$TMP"
export PATH="$TOOLS/venv/bin:$TOOLS/node/bin:$TOOLS/bin:$HOME/.local/bin:$PATH"
export UV_PYTHON_INSTALL_DIR="$TOOLS/python" UV_CACHE_DIR="$TOOLS/uv-cache" UV_PYTHON_PREFERENCE=only-managed

step() { N=$((N + 1)); echo "@@ $N $TOTAL $1"; }
say()  { echo "   $1"; }
fail() { echo "❌ $1"; exit 1; }
get()  { curl -fL --retry 4 --retry-delay 3 --connect-timeout 20 -sS -o "$2" "$1" || fail "ما گدرت أنزّل: $(basename "$1"). تأكد من النت وعيد"; }

# ---------- the app itself (name, logo, window): the newest URU.app from the release page ----------
if [ "${1:-}" = "--app" ]; then
  OLD_PID="${2:-}"; SERVER_PID="${3:-}"; OLD_APP="${4:-}"
  [ "$OS" = "Darwin" ] || fail "هاي للماك بس"
  echo "📦 أنزّل التطبيق الجديد…"
  get "https://github.com/$REPO/releases/download/mac-app/URU.dmg" "$TMP/URU.dmg"
  MNT="$(mktemp -d)"
  hdiutil attach -nobrowse -readonly -mountpoint "$MNT" "$TMP/URU.dmg" >/dev/null || fail "ما گدرت أفتح ملف التطبيق"
  DEST=/Applications; [ -w "$DEST" ] || { DEST="$HOME/Applications"; mkdir -p "$DEST"; }
  rm -rf "$DEST/URU.app.new"
  cp -R "$MNT/URU.app" "$DEST/URU.app.new" || { hdiutil detach "$MNT" >/dev/null; fail "ما گدرت أنسخ التطبيق"; }
  hdiutil detach "$MNT" >/dev/null || true
  rm -rf "$DEST/URU.app"; mv "$DEST/URU.app.new" "$DEST/URU.app"
  xattr -cr "$DEST/URU.app" 2>/dev/null || true
  # the old one (its old name) goes, wherever it was; never a reason to stop (it may run from the read-only
  # install window, /Volumes/…: that window is closed after the old app quits)
  EJECT=""
  case "$OLD_APP" in
    /Volumes/*) EJECT="$(dirname "$OLD_APP")" ;;
    */المونتير.app) rm -rf "$OLD_APP" 2>/dev/null || true ;;
  esac
  for old in "/Applications/المونتير.app" "$HOME/Applications/المونتير.app"; do
    [ -d "$old" ] && { rm -rf "$old" 2>/dev/null || true; }
  done
  rm -f "$TMP/URU.dmg"
  [ "$OLD_PID" = "quiet" ] && { echo "✅ انصّب URU (ينفتح الجديد المرة الجاية)"; exit 0; }
  echo "✅ انصّب URU. يفتح هسة…"
  # after this script and the old window are gone: close them, then open the new app
  nohup /bin/bash -c "sleep 2; ${OLD_PID:+kill $OLD_PID;} ${SERVER_PID:+kill $SERVER_PID;} sleep 1.5; open \"$DEST/URU.app\"; ${EJECT:+sleep 3; hdiutil detach \"$EJECT\" -force;}" >/dev/null 2>&1 &
  exit 0
fi

# ---------- silent update: the newest code ready beside the running one (owner, 2026-10-25: "أفوت ألگاه محدّث") ----------
if [ "${1:-}" = "--stage" ]; then
  api="https://api.github.com/repos/$REPO"
  COMMIT=$(curl -fsS --connect-timeout 15 "$api/commits/$BRANCH" 2>/dev/null | sed -n 's/^  "sha": "\([0-9a-f]*\)".*/\1/p' | head -1 || true)
  [ -n "$COMMIT" ] || { echo "ماكو نت أو ما وصلت للكود"; exit 0; }
  grep -q "$COMMIT" "$HOME_DIR/version.json" 2>/dev/null && { echo "محدّث"; exit 0; }
  grep -q "$COMMIT" "$CODE.next/.uru_version.json" 2>/dev/null && { echo "جاهز من قبل"; exit 0; }
  NEXT="$CODE.next.tmp"; rm -rf "$NEXT"; mkdir -p "$NEXT"
  get "https://codeload.github.com/$REPO/tar.gz/$COMMIT" "$TMP/next.tar.gz"
  tar -xzf "$TMP/next.tar.gz" -C "$NEXT" --strip-components 1; rm -f "$TMP/next.tar.gz"
  if ! cmp -s "$CODE/editor/remotion/package-lock.json" "$NEXT/editor/remotion/package-lock.json"; then
    (cd "$NEXT/editor/remotion" && npm ci --silent --no-audit --no-fund) || { rm -rf "$NEXT"; fail "ما گدرت أجهّز أدوات الرسم الجديدة"; }
  fi
  "$TOOLS/uv" pip install -q --python "$TOOLS/venv/bin/python" -r "$NEXT/editor/requirements.txt" || { rm -rf "$NEXT"; fail "ما گدرت أنصّب مكتبات بايثون"; }
  printf '{"commit": "%s", "branch": "%s", "date": "%s"}\n' "$COMMIT" "$BRANCH" "$(date +%Y-%m-%d)" > "$NEXT/.uru_version.json"
  rm -rf "$CODE.next"; mv "$NEXT" "$CODE.next"
  echo "✅ النسخة ${COMMIT:0:7} جاهزة، تتبدّل وقت ما يتسكّر التطبيق"
  exit 0
fi

# ---------- 1. المكان ----------
step "أتأكد من المساحة والنت"
free_gb=$(df -Pk "$HOME_DIR" | awk 'NR==2 {print int($4 / 1048576)}')
if [ "$UPDATE" = 0 ] && [ "$free_gb" -lt 12 ]; then
  fail "المساحة الفاضية ${free_gb} گيگا بس. التطبيق يحتاج تقريباً 15 گيگا. فضّي شوية وعيد"
fi
say "المساحة الفاضية: ${free_gb} گيگا"
curl -sS --connect-timeout 15 -o /dev/null https://api.github.com || fail "ماكو نت، أو النت ضعيف. تأكد منه وعيد"

# ---------- 2. الكود ----------
step "أجيب آخر نسخة"
rm -rf "$CODE.new"; mkdir -p "$CODE.new"
if [ -n "${MONTIER_CODE_SRC:-}" ]; then
  (cd "$MONTIER_CODE_SRC" && tar --exclude=.git --exclude=node_modules --exclude='episodes/*/edit' -cf - .) | (cd "$CODE.new" && tar -xf -)
  COMMIT="local"
else
  api="https://api.github.com/repos/$REPO"
  COMMIT=$(curl -fsS "$api/commits/$BRANCH" 2>/dev/null | sed -n 's/^  "sha": "\([0-9a-f]*\)".*/\1/p' | head -1 || true)
  if [ -z "$COMMIT" ]; then     # the branch was merged and removed: take the main branch
    BRANCH=$(curl -fsS "$api" | sed -n 's/.*"default_branch": "\([^"]*\)".*/\1/p' | head -1)
    COMMIT=$(curl -fsS "$api/commits/$BRANCH" | sed -n 's/^  "sha": "\([0-9a-f]*\)".*/\1/p' | head -1)
  fi
  [ -n "$COMMIT" ] || fail "ما گدرت أوصل لمكان الكود. عيد بعد شوية"
  get "https://codeload.github.com/$REPO/tar.gz/$COMMIT" "$TMP/code.tar.gz"
  tar -xzf "$TMP/code.tar.gz" -C "$CODE.new" --strip-components 1
  rm -f "$TMP/code.tar.gz"
fi
# keep the 1 GB of scene packages when they did not change
if [ -d "$CODE/editor/remotion/node_modules" ] && cmp -s "$CODE/editor/remotion/package-lock.json" "$CODE.new/editor/remotion/package-lock.json"; then
  mv "$CODE/editor/remotion/node_modules" "$CODE.new/editor/remotion/node_modules"
fi
rm -rf "$CODE.old"; [ -d "$CODE" ] && mv "$CODE" "$CODE.old"
mv "$CODE.new" "$CODE"; rm -rf "$CODE.old"
say "النسخة: ${COMMIT:0:7}"

# ---------- 3. بايثون ----------
step "أنصّب بايثون ومكتباته (أطول خطوة بأول مرة)"
if [ ! -x "$TOOLS/uv" ]; then
  if [ "$OS" = "Darwin" ]; then
    [ "$ARCH" = "arm64" ] && t="aarch64-apple-darwin" || t="x86_64-apple-darwin"
  else
    [ "$ARCH" = "aarch64" ] && t="aarch64-unknown-linux-gnu" || t="x86_64-unknown-linux-gnu"
  fi
  get "https://github.com/astral-sh/uv/releases/latest/download/uv-$t.tar.gz" "$TMP/uv.tar.gz"
  tar -xzf "$TMP/uv.tar.gz" -C "$TMP"; mv "$TMP/uv-$t/uv" "$TOOLS/uv"; rm -rf "$TMP/uv.tar.gz" "$TMP/uv-$t"
fi
if [ ! -x "$TOOLS/venv/bin/python" ]; then
  "$TOOLS/uv" python install "$PY_VERSION" -q
  "$TOOLS/uv" venv --seed --python "$PY_VERSION" "$TOOLS/venv" -q
fi
"$TOOLS/uv" pip install -q --python "$TOOLS/venv/bin/python" -r "$CODE/editor/requirements.txt" || fail "ما گدرت أنصّب مكتبات بايثون"
if [ "$OS" = "Darwin" ] && [ "$ARCH" = "arm64" ]; then   # the Mac chip's own speech model: transcribes many times faster
  "$TOOLS/uv" pip install -q --python "$TOOLS/venv/bin/python" "mlx-whisper>=0.4" || say "التفريغ السريع ما انصّب، يشتغل العادي"
fi
say "بايثون جاهز"

# ---------- 4. برنامج الفيديو ----------
step "أنصّب برنامج الفيديو"
if [ ! -x "$TOOLS/bin/ffmpeg" ] || [ ! -x "$TOOLS/bin/ffprobe" ]; then
  if [ "$OS" = "Darwin" ]; then
    [ "$ARCH" = "arm64" ] && base="$FFMPEG_ARM" || base="$FFMPEG_INTEL"
    for b in ffmpeg ffprobe; do
      get "$base/$b.zip" "$TMP/$b.zip"
      unzip -o -q "$TMP/$b.zip" -d "$TOOLS/bin"; rm -f "$TMP/$b.zip"
      chmod +x "$TOOLS/bin/$b"; xattr -d com.apple.quarantine "$TOOLS/bin/$b" 2>/dev/null || true
    done
  else
    command -v ffmpeg >/dev/null || fail "برنامج الفيديو مو موجود"
    ln -sf "$(command -v ffmpeg)" "$TOOLS/bin/ffmpeg"; ln -sf "$(command -v ffprobe)" "$TOOLS/bin/ffprobe"
  fi
fi
"$TOOLS/bin/ffmpeg" -hide_banner -version >/dev/null 2>&1 || fail "برنامج الفيديو ما يشتغل"
say "برنامج الفيديو جاهز"

# ---------- 5. الرسم (نود وريموشن) ----------
step "أنصّب أدوات الرسم والموشن"
if [ ! -x "$TOOLS/node/bin/node" ] || [ "$("$TOOLS/node/bin/node" --version)" != "v$NODE_VERSION" ]; then
  if [ "$OS" = "Darwin" ]; then
    [ "$ARCH" = "arm64" ] && t="darwin-arm64" || t="darwin-x64"
  else
    [ "$ARCH" = "aarch64" ] && t="linux-arm64" || t="linux-x64"
  fi
  get "https://nodejs.org/dist/v$NODE_VERSION/node-v$NODE_VERSION-$t.tar.gz" "$TMP/node.tar.gz"
  rm -rf "$TOOLS/node"; mkdir -p "$TOOLS/node"
  tar -xzf "$TMP/node.tar.gz" -C "$TOOLS/node" --strip-components 1; rm -f "$TMP/node.tar.gz"
fi
if [ ! -d "$CODE/editor/remotion/node_modules" ]; then
  (cd "$CODE/editor/remotion" && npm ci --silent --no-audit --no-fund) || fail "ما گدرت أنصّب أدوات الرسم"
fi
(cd "$CODE/editor/remotion" && node -e "require('@remotion/renderer').ensureBrowser().then(()=>process.exit(0),e=>{console.error(e.message);process.exit(1)})") \
  || fail "ما گدرت أنزّل متصفح الرسم"
say "أدوات الرسم جاهزة"

# ---------- 6. كلود ----------
step "أنصّب كلود (عقل المساعد)"
if [ -n "${MONTIER_SKIP_CLAUDE:-}" ]; then
  say "تخطيت (اختبار)"
elif command -v claude >/dev/null 2>&1; then
  say "موجود من قبل"
else
  curl -fsSL https://claude.ai/install.sh | bash >/dev/null 2>&1 || fail "ما گدرت أنصّب كلود"
  say "انصّب. تحتاج تسجل دخول مرة وحدة من الإعدادات"
fi

# ---------- 7. موديل التفريغ ----------
step "أنزّل موديل التفريغ (تقريباً گيگا ونص، مرة وحدة)"
if [ -n "${MONTIER_SKIP_MODEL:-}" ]; then
  say "تخطيت (اختبار)"
elif [ "$UPDATE" = 1 ] && [ -f "$HOME_DIR/ready" ]; then
  say "موجود من قبل"   # an update never re-checks the 1.5 GB model (a missing one downloads on first use)
else
  (cd "$CODE" && "$TOOLS/venv/bin/python" -c "from faster_whisper import WhisperModel; from editor.pipeline.transcribe import WHISPER_MODEL; WhisperModel(WHISPER_MODEL, device='cpu', compute_type='int8')") \
    || fail "ما گدرت أنزّل موديل التفريغ"
  say "الموديل جاهز"
fi

# ---------- 8. فحص ----------
step "أفحص كل شي"
(cd "$CODE" && MONTIER_APP=1 "$TOOLS/venv/bin/python" -m editor.pipeline.doctor --quiet) || true
printf '{"commit": "%s", "branch": "%s", "date": "%s"}\n' "$COMMIT" "$BRANCH" "$(date +%Y-%m-%d)" > "$HOME_DIR/version.json"
touch "$HOME_DIR/ready"
rm -rf "$TMP"
echo "✅ URU جاهز"
