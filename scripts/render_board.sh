#!/bin/bash
# 白板马克笔风一键渲染（不走 Manim）：分镜.js → 配音 → 网页逐帧画 → 贴配音并逐句核对 → 成片。
#
# 用法：render_board.sh <集目录>/分镜.js [--draft] [--final] [--tts clone|edge] [--rate +5%]
#   --draft  低清快速预览（960×540，15 帧），输出 <集目录>/草稿.mp4
#   默认     1920×1080，30 帧，输出 <集目录>/<主题>.mp4
#   --final  核对通过后删除 .work/ 和草稿，只留 分镜.js + 成片
set -euo pipefail
HERE="$(cd "$(dirname "$0")" && pwd)"
EP="$(cd "$(dirname "$1")" && pwd)"; SB="$EP/$(basename "$1")"; shift
TOPIC="$(basename "$EP" | sed -E 's/^[0-9]{4}-[0-9]{2}-[0-9]{2}-//')"
OUT="$EP/$TOPIC.mp4"; DRAFT=""; FINAL=0
while [ $# -gt 0 ]; do
  case "$1" in
    --draft) DRAFT="--draft"; OUT="$EP/草稿.mp4"; shift ;;
    --final) FINAL=1; shift ;;
    --tts)   export EXPLAINER_TTS="$2"; shift 2 ;;
    --rate)  export EXPLAINER_RATE="$2"; shift 2 ;;
    *) echo "未知参数: $1" >&2; exit 1 ;;
  esac
done
[ -d "${WHITEBOARD_DEPS:-$HOME/Tools/envs/whiteboard-video}/node_modules/hanzi-writer-data" ] \
  || { echo "缺依赖：~/Tools/envs/whiteboard-video（playwright-core、hanzi-writer-data、hersheytext），先问用户再装" >&2; exit 1; }

WORK="$EP/.work"; mkdir -p "$WORK"
node "$HERE/board/render.js" says "$SB" "$WORK/says.json"
python3 "$HERE/board_audio.py" "$WORK/says.json" "$WORK/audio_cache" "$WORK/audio.json"
node "$HERE/board/render.js" render "$SB" "$WORK/audio.json" "$WORK" $DRAFT
python3 "$HERE/mux_audio.py" "$WORK/silent.mp4" "$WORK/timeline.json" "$OUT"
echo "完成：${OUT}（$(ffprobe -v error -show_entries format=duration -of csv=p=0 "$OUT" | cut -d. -f1) 秒）"

if [ "$FINAL" = 1 ]; then
  rm -rf "$WORK" "$EP/草稿.mp4"
  echo "已清理中间文件，集目录只留：$(ls "$EP" | tr '\n' ' ')"
fi
