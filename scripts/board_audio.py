"""白板风：按分镜里的旁白顺序补齐配音，量出每句时长，写 audio.json 给 board/render.js 排时间。

用法：python3 board_audio.py says.json 音频缓存目录 audio.json
"""
import json
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from audio_key import key  # noqa: E402
from prepare_audio import generate  # noqa: E402

says, cache, out = json.load(open(sys.argv[1], encoding="utf-8")), Path(sys.argv[2]).resolve(), sys.argv[3]
generate(says, cache)
rows = []
for t in says:
    f = cache / key(t)
    d = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(f)],
                       capture_output=True, text=True, check=True).stdout
    rows.append({"text": t, "file": str(f), "dur": float(d)})
json.dump(rows, open(out, "w", encoding="utf-8"), ensure_ascii=False)
