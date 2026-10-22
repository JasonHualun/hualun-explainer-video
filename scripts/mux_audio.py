"""按 timeline.json 把每句旁白贴到它开始的秒数上，再和无声画面合成成片，并逐句核对没有丢声。

用法：python3 mux_audio.py 无声画面.mp4 timeline.json 输出.mp4
"""
import json
import re
import subprocess
import sys


def mean_db(path, start=None, dur=None):
    cmd = ["ffmpeg", "-hide_banner"]
    if start is not None:
        cmd += ["-ss", str(start), "-t", str(dur)]
    cmd += ["-i", path, "-af", "volumedetect", "-f", "null", "-"]
    m = re.search(r"mean_volume: (-?[\d.]+|-inf)", subprocess.run(cmd, capture_output=True, text=True).stderr)
    return float(m.group(1)) if m and m.group(1) != "-inf" else -99.0


if __name__ == "__main__":
    video, tl_path, out = sys.argv[1:4]
    tl = json.load(open(tl_path, encoding="utf-8"))
    clips = tl["clips"]
    inputs, filters = [], []
    for i, c in enumerate(clips):
        inputs += ["-i", c["file"]]
        ms = int(c["t"] * 1000)
        filters.append(f"[{i + 1}:a]aresample=48000,aformat=channel_layouts=stereo,adelay={ms}|{ms}[a{i}]")
    mix = "".join(f"[a{i}]" for i in range(len(clips)))
    filters.append(f"{mix}amix=inputs={len(clips)}:normalize=0:dropout_transition=0,apad[aout]")
    subprocess.run(["ffmpeg", "-loglevel", "error", "-y", "-i", video, *inputs,
                    "-filter_complex", ";".join(filters), "-map", "0:v", "-map", "[aout]",
                    "-c:v", "copy", "-c:a", "aac", "-b:a", "192k", "-shortest", out], check=True)

    # 逐句核对：成片里每句话所在的时间段必须有声音
    silent = []
    for c in clips:
        d = float(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0",
                                  c["file"]], capture_output=True, text=True).stdout)
        if mean_db(out, c["t"] + 0.1, max(0.5, d - 0.3)) < -45:
            silent.append(c["t"])
    if silent:
        sys.exit(f"有 {len(silent)} 句在成片里没声音，开始秒数：{silent}")
    print(f"配音核对通过：{len(clips)} 句全部有声音")
