#!/usr/bin/env bash
# يقص مقطع ريل من فيديو طويل: عمودي 9:16، 1080x1920، صوت مضبوط، وترجمة اختيارية.
# الاستخدام:
#   scripts/make-reel.sh <الفيديو> <البداية> <النهاية> <الناتج.mp4> [ترجمة.srt]
# مثال:
#   scripts/make-reel.sh episode.mp4 00:03:10 00:03:52 reel.mp4 subs.srt
set -euo pipefail

if [[ $# -lt 4 ]]; then
  sed -n 2,6p "$0"; exit 1
fi
IN="$1"; START="$2"; END="$3"; OUT="$4"; SRT="${5:-}"

# قص من الوسط لـ 9:16 إذا الفيديو عرضي، وإذا عمودي أصلاً يكبّر/يصغّر بس
VF="scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,setsar=1"
if [[ -n "$SRT" ]]; then
  # ترجمة كبيرة بالثلث السفلي، خط عريض وحدود سودة (تنقرأ بدون صوت)
  # ملاحظة: مقاسات الترجمة نسبة لارتفاع 288 (مو 1920)، فـ MarginV=55 يعني تقريباً 365 بكسل من الأسفل
  STYLE="FontName=DejaVu Sans,FontSize=16,Bold=1,PrimaryColour=&H00FFFFFF,OutlineColour=&H00000000,BorderStyle=1,Outline=3,Shadow=0,Alignment=2,MarginV=55"
  VF="$VF,subtitles='${SRT//\'/\\\'}':force_style='$STYLE'"
fi

ffmpeg -hide_banner -loglevel error -y \
  -ss "$START" -to "$END" -i "$IN" \
  -vf "$VF" -r 30 \
  -c:v libx264 -preset medium -crf 20 -pix_fmt yuv420p -profile:v high \
  -af "loudnorm=I=-14:TP=-1.5:LRA=11" -c:a aac -b:a 160k -ar 48000 \
  -movflags +faststart "$OUT"

DUR=$(ffprobe -v error -show_entries format=duration -of csv=p=0 "$OUT")
echo "✅ $OUT جاهز — المدة: ${DUR%.*} ثانية، 1080x1920"
if (( ${DUR%.*} > 60 )); then echo "⚠️ أطول من 60 ثانية: لقصص الاكتشاف الأفضل 30-60 ثانية."; fi
