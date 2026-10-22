#!/bin/bash
# 一键渲染解释视频：预生成旁白 → Manim 渲染无声画面 → ffmpeg 按时间轴贴配音并逐句核对 → 成片。
#
# 用法：render.sh <集目录>/分镜.py 场景类名 [--draft] [--final] [--tts clone|edge] [--rate +5%]
#   集目录按「YYYY-MM-DD-主题」命名（见 SKILL.md 的存放规则）
#   --draft  低清快速预览（480p15），输出 <集目录>/草稿.mp4
#   默认     1080p60，输出 <集目录>/<主题>.mp4
#   --final  成片核对通过后删除中间文件（.work/）和草稿，只留 分镜.py + 成片
set -euo pipefail
HERE="$(cd "$(dirname "$0")" && pwd)"
VENV="${EXPLAINER_VENV:-$HOME/Tools/envs/learning-video}"
TEX="$HOME/Library/TinyTeX/bin/universal-darwin"

EP="$(cd "$(dirname "$1")" && pwd)"; SCENE_FILE="$EP/$(basename "$1")"; SCENE="$2"; shift 2
Q="-qh"; QDIR="1080p60"; FINAL=0
TOPIC="$(basename "$EP" | sed -E 's/^[0-9]{4}-[0-9]{2}-[0-9]{2}-//')"
OUT="$EP/$TOPIC.mp4"
while [ $# -gt 0 ]; do
  case "$1" in
    --draft) Q="-ql"; QDIR="480p15"; OUT="$EP/草稿.mp4"; shift ;;
    --final) FINAL=1; shift ;;
    --tts)   export EXPLAINER_TTS="$2"; shift 2 ;;
    --rate)  export EXPLAINER_RATE="$2"; shift 2 ;;
    *) echo "未知参数: $1" >&2; exit 1 ;;
  esac
done

WORK="$EP/.work"; mkdir -p "$WORK"
export EXPLAINER_AUDIO_CACHE="$WORK/audio_cache"
export EXPLAINER_TIMELINE="$WORK/timeline.json"
export PATH="$TEX:$PATH"
export PYTHONPATH="$HERE${PYTHONPATH:+:$PYTHONPATH}"

python3 "$HERE/prepare_audio.py" "$SCENE_FILE" "$EXPLAINER_AUDIO_CACHE"
cd "$WORK"
"$VENV/bin/python" -m manim "$Q" --disable_caching --media_dir "$WORK/media" "$SCENE_FILE" "$SCENE" 2>&1 \
  | grep -E "Rendered|Error|Exception" || true
SRC="$WORK/media/videos/$(basename "$SCENE_FILE" .py)/$QDIR/$SCENE.mp4"
[ -f "$SRC" ] || { echo "渲染失败，去掉 grep 重跑看完整报错" >&2; exit 1; }
python3 "$HERE/mux_audio.py" "$SRC" "$EXPLAINER_TIMELINE" "$OUT"
echo "完成：$OUT（$(ffprobe -v error -show_entries format=duration -of csv=p=0 "$OUT" | cut -d. -f1) 秒）"

if [ "$FINAL" = 1 ]; then
  rm -rf "$WORK" "$EP/草稿.mp4"
  echo "已清理中间文件，集目录只留：$(ls "$EP" | tr '\n' ' ')"
fi
