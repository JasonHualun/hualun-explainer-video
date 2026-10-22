"""片段路线：分镜.json + 每句配音时长 → 每段一份花叔引擎 spec、整片配音时间轴、字幕表、口型包络。

用法：
  plan.py says   分镜.json says.json            # 列出全部旁白（给 board_audio.py 配音）
  plan.py build  分镜.json audio.json 工作目录 [--draft]

分镜.json 格式见 SKILL.md「片段路线怎么做一集」。时间规则：
  每句旁白占「配音时长 + GAP」；cue 默认在这句开口后 LEAD 秒揭开；
  cue 写 "word": "某词" → 按字数比例落在这个词开始的时刻（number 类是落定时刻）；
  "hold": 秒 → 这句之后留白（反应镜头、包袱后的定住就靠它）；没有 say 的行 = 纯画面停顿。
"""
import json
import subprocess
import sys
from pathlib import Path

import numpy as np

GAP, LEAD, ENV_FPS = 0.15, 0.08, 60


def load(sb):
    return json.load(open(sb, encoding="utf-8"))


def says(sb):
    return [ln["say"] for seg in load(sb)["segments"] for ln in seg["lines"] if ln.get("say")]


def envelope(wav_pcm, sr=16000):
    """60fps 的 RMS 包络，归一到 0..1（storytime 口型读它）。"""
    hop = sr // ENV_FPS
    n = len(wav_pcm) // hop
    if n == 0:
        return []
    rms = np.sqrt((wav_pcm[: n * hop].reshape(n, hop) ** 2).mean(axis=1))
    peak = np.percentile(rms, 98) or 1.0
    return np.clip(rms / peak, 0, 1).round(3).tolist()


def pcm(path, sr=16000):
    raw = subprocess.run(["ffmpeg", "-v", "error", "-i", path, "-ac", "1", "-ar", str(sr), "-f", "f32le", "-"],
                         capture_output=True, check=True).stdout
    return np.frombuffer(raw, dtype=np.float32)


def build(sb, audio_json, work, draft):
    plan, audio = load(sb), {a["text"]: a for a in json.load(open(audio_json, encoding="utf-8"))}
    W, H = (1280, 720) if draft else (1920, 1080)
    fps = 15 if draft else 30
    work = Path(work)
    (work / "specs").mkdir(parents=True, exist_ok=True)
    clips, subs, segs, t_global = [], [], [], 0.0
    for i, seg in enumerate(plan["segments"]):
        t, cues, env_parts = 0.0, [], []
        for ln in seg["lines"]:
            text = ln.get("say")
            dur = audio[text]["dur"] + GAP if text else 0.0
            for c in ([ln["cue"]] if isinstance(ln.get("cue"), dict) else ln.get("cue", [])):
                c = dict(c)
                word = c.pop("word", None)
                if word and text and word in text:
                    at = t + LEAD + (audio[text]["dur"]) * text.index(word) / max(1, len(text))
                    if c.get("kind") == "number":
                        at += audio[text]["dur"] * len(word) / max(1, len(text))
                else:
                    at = t + c.pop("offset", LEAD)
                c["at"] = round(at, 3)
                if seg["grammar"] == "y4_storytime" and c.get("kind") in ("point", "title") and text:
                    c.setdefault("text", text)      # 口播原文定张嘴时长；气泡显示 sub
                cues.append(c)
            if text:
                clips.append({"t": round(t_global + t, 3), "file": audio[text]["file"]})
                subs.append({"t0": round(t_global + t, 3), "t1": round(t_global + t + audio[text]["dur"], 3), "text": text})
                env_parts.append((t, audio[text]["file"]))
            t += dur + ln.get("hold", 0.0)
        t = round(t + seg.get("tail", 0.3), 3)
        spec = {"grammar": seg["grammar"], "duration": t, "fps": fps, "width": W, "height": H,
                "safe": {"bottom": round(H * 0.15)}, "data": seg.get("data", {}), "cues": cues}
        sp = work / "specs" / f"seg{i:02d}.json"
        sp.write_text(json.dumps(spec, ensure_ascii=False, indent=1), encoding="utf-8")
        env = None
        if seg["grammar"] == "y4_storytime":
            a = np.zeros(int(t * ENV_FPS) + 1)
            for t0, f in env_parts:
                e = envelope(pcm(f))
                k = int(t0 * ENV_FPS)
                a[k: k + len(e)] = e[: len(a) - k]
            env = {"fps": ENV_FPS, "a": a.round(3).tolist()}
        segs.append({"spec": str(sp), "t0": round(t_global, 3), "duration": t, "env": env})
        t_global = round(t_global + t, 3)
    json.dump({"duration": t_global, "fps": fps, "width": W, "height": H, "segments": segs, "subs": subs},
              open(work / "plan.json", "w", encoding="utf-8"), ensure_ascii=False)
    json.dump({"duration": t_global, "clips": clips}, open(work / "timeline.json", "w", encoding="utf-8"), ensure_ascii=False)
    print(f"排好：{len(segs)} 段，{len(subs)} 句旁白，共 {t_global:.1f} 秒")


if __name__ == "__main__":
    if sys.argv[1] == "says":
        json.dump(says(sys.argv[2]), open(sys.argv[3], "w", encoding="utf-8"), ensure_ascii=False)
    else:
        build(sys.argv[2], sys.argv[3], sys.argv[4], "--draft" in sys.argv)
