#!/bin/bash
# 片段路线一键渲染（花叔 huashu-art-motion 的 8 种解说语法）：分镜.json → 配音 → 排时间 → 引擎逐帧画 + 字幕 → 贴配音并逐句核对 → 加音效和背景音乐 → 成片。
#
# 用法：render_clip.sh <集目录>/分镜.json [--draft] [--final] [--tts clone|edge] [--rate +5%]
#   --draft  低清快速预览（1280×720，15 帧），输出 <集目录>/草稿.mp4
#   默认     1920×1080，30 帧，输出 <集目录>/<主题>.mp4
#   --final  核对通过后删除 .work/ 和草稿，只留 分镜.json + 成片
set -euo pipefail
HERE="$(cd "$(dirname "$0")" && pwd)"
VENV="${EXPLAINER_VENV:-$HOME/Tools/envs/learning-video}"
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
[ -f "${HUASHU_ENGINE:-$HOME/Tools/apps/花伦动画引擎/scripts/engine}/clip.html" ] \
  || { echo "缺引擎：~/Tools/apps/花伦动画引擎，先问用户再放（源自花叔 huashu-art-motion）" >&2; exit 1; }

WORK="$EP/.work"; mkdir -p "$WORK"
"$VENV/bin/python" "$HERE/clip/plan.py" says "$SB" "$WORK/says.json"
python3 "$HERE/board_audio.py" "$WORK/says.json" "$WORK/audio_cache" "$WORK/audio.json"
"$VENV/bin/python" "$HERE/clip/plan.py" build "$SB" "$WORK/audio.json" "$WORK" $DRAFT
CLIP_STORYBOARD="$SB" node "$HERE/clip/render.js" "$WORK"
python3 "$HERE/mux_audio.py" "$WORK/silent.mp4" "$WORK/timeline.json" "$WORK/voice.mp4"
"$VENV/bin/python" "$HERE/clip/sound.py" "$WORK" "$SB" "$WORK/voice.mp4" "$OUT"
echo "完成：${OUT}（$(ffprobe -v error -show_entries format=duration -of csv=p=0 "$OUT" | cut -d. -f1) 秒）"

if [ "$FINAL" = 1 ]; then
  rm -rf "$WORK" "$EP/草稿.mp4"
  echo "已清理中间文件，集目录只留：$(ls "$EP" | tr '\n' ' ')"
fi
