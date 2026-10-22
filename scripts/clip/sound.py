"""片段路线：给已贴好配音的成片加音效和背景音乐。

用法：sound.py 工作目录 分镜.json 有配音的成片.mp4 输出.mp4

素材与音量来自外部素材库目录（环境变量 HUALUN_VIDEO_PROJECT 指定，本仓库不附带）：
  音效库 library/音效/<类>/（嗖 咚 砰 嘀 哒 扫 乱码，重音时刻缓存 .分析.json）
  音乐库 library/音乐/<情绪>/（温和 科技 紧张 轻快）
  音量  config.json「声音」
音效按 cue 自动配，重音对准画面揭开/落定那一帧；音乐按 分镜.json 的 "music"（情绪名，"无" = 不要），
说话时用侧链压缩自动压低，开头淡入、结尾淡出，不够长就从头接着放。
"""
import hashlib
import json
import os
import subprocess
import sys
from pathlib import Path

PROJ = Path(os.environ.get("HUALUN_VIDEO_PROJECT", Path.home() / "hualun-sound-library")).expanduser()
LIB = PROJ / "library"
CFG = json.load(open(PROJ / "config.json", encoding="utf-8"))["声音"]
PEAK = json.load(open(LIB / "音效/.分析.json", encoding="utf-8")) if (LIB / "音效/.分析.json").exists() else {}


def pick(folder, seed):
    files = sorted(p for p in folder.iterdir() if p.suffix.lower() in (".wav", ".mp3", ".m4a", ".ogg"))
    return files[int(hashlib.md5(seed.encode()).hexdigest(), 16) % len(files)] if files else None


def peak_of(f, kind):
    """音效最响那一下离开头几秒：先查项目缓存，没有就现量。"""
    hit = PEAK.get(f"{kind}/{f.name}")
    if hit:
        return hit.get("peak", 0)
    import numpy as np
    raw = subprocess.run(["ffmpeg", "-v", "error", "-i", str(f), "-ac", "1", "-ar", "8000", "-f", "f32le", "-"], capture_output=True).stdout
    a = np.abs(np.frombuffer(raw, dtype=np.float32))
    return float(a.argmax() / 8000) if len(a) else 0


def sfx_events(plan, funny=False):
    """[(类, 落点秒, 音量倍数)]：按语法和 cue 类型配音效（规矩见 references/动画方法论.md 与原件语法卡）。
    funny=True（搞笑片）：气泡「啵」、问号「弹」、反应镜头「蟋蟀」尴尬沉默、大字「拳」、动态文字主词「啵」，
    开场一声「喵」，全片最后一个 ？！ 换成包袱鼓点「鼓点」，紧跟一声失败长号「笑点」。"""
    ev = []
    last_hl = None
    for k, seg in enumerate(plan["segments"]):
        spec, t0 = json.load(open(seg["spec"], encoding="utf-8")), seg["t0"]
        g = spec["grammar"]
        if k > 0:
            ev.append(("嗖", t0 + 0.02, 0.8))                      # 段与段之间硬切
        firsts = True
        for q in sorted(spec["cues"], key=lambda q: q["at"]):
            at, kind = t0 + q["at"], q["kind"]
            if g == "y4_storytime":
                if kind == "highlight":
                    ev.append(("弹" if funny else "嘀", at, 1.0))  # ？！弹出
                    last_hl = len(ev) - 1
                elif kind == "react":
                    ev.append(("蟋蟀", at + 0.15, 1.0) if funny else ("咚", at, 0.9))   # 尴尬沉默 / 砸镜
                elif kind == "insert":
                    d = q.get("data", {})
                    hit = t0 + d["hit"] if "hit" in d else at + (1.3 if q.get("sub") else 0.4)
                    t = at + 0.25
                    while t < hit - 0.25:                            # 打字
                        ev.append(("哒", t, 0.8)); t += 0.11
                    ev.append(("拳" if funny else "砰", hit, 0.9))   # 大字砸出
                elif kind in ("point", "title"):
                    ev.append(("啵" if funny else "嘀", at, 0.45))  # 气泡弹出（轻）
            elif g == "y7_paper":
                if kind == "move":
                    ev.append(("嗖", at, 0.5))
                elif kind == "mark":
                    ev.append(("弹" if funny else "嘀", at, 1.0))
                    last_hl = len(ev) - 1
                elif kind == "think":
                    ev.append(("啵" if funny else "嘀", at + 0.24, 0.9))
                elif kind == "word":
                    ev.append(("拳" if funny else "咚", at, 1.0))
                elif kind == "close":
                    ev.append(("嗖", at, 0.4))
            elif g == "y5_kinetic_type":
                if kind in ("title", "point", "number"):
                    if not firsts:
                        ev.append(("嗖", at - 0.3, 0.6))            # 色带换页
                    ev.append(("啵" if funny else "咚", at, 1.0))   # 主词砸进来
                    firsts = False
                elif kind == "highlight":
                    ev.append(("嘀", at, 0.8))
            else:
                if kind == "number":
                    ev.append(("咚", at, 1.0))
                elif kind in ("image", "clip"):
                    ev.append(("扫", at, 0.8))
                elif kind == "enter":
                    ev.append(("嗖", at, 0.8))
                elif kind in ("card", "step", "point", "draw", "highlight"):
                    ev.append(("嘀", at, 0.6))
    if funny:
        ev.insert(0, ("喵", 0.25, 0.7))                             # 主角暹罗猫登场
        if last_hl is not None:                                       # 包袱：鼓点 + 失败长号
            _, at, _ = ev[last_hl + 1]
            ev[last_hl + 1] = ("鼓点", at, 1.0)
            ev.append(("笑点", at + 0.9, 0.9))
    return ev


def main(work, sb, video, out):
    plan = json.load(open(Path(work) / "plan.json", encoding="utf-8"))
    board = json.load(open(sb, encoding="utf-8"))
    mood = board.get("music", CFG.get("默认情绪", "科技"))
    funny = board.get("sfx", "搞笑" if mood == "搞笑" else "") == "搞笑"
    dur = plan["duration"]
    inputs, filt, mix = ["-i", video], [], ["[0:a]"]
    if CFG.get("音效", True):
        base = CFG.get("音效总音量", 0.6)
        for i, (kind, at, gain) in enumerate(sfx_events(plan, funny)):
            f = pick(LIB / "音效" / kind, f"{kind}{i}")
            if not f:
                continue
            peak = peak_of(f, kind)
            ms = max(0, int((at - peak) * 1000))
            vol = base * CFG.get("各类音量", {}).get(kind, 0.5) * gain
            inputs += ["-i", str(f)]
            n = sum(a == "-i" for a in inputs) - 1
            filt.append(f"[{n}:a]aresample=48000,aformat=channel_layouts=stereo,volume={vol:.3f},adelay={ms}|{ms}[s{n}]")
            mix.append(f"[s{n}]")
    music = None
    if CFG.get("音乐", True) and mood != "无" and (LIB / "音乐" / mood).is_dir():
        music = pick(LIB / "音乐" / mood, Path(sb).parent.name)
    if music:
        inputs += ["-stream_loop", "-1", "-i", str(music)]
        n = sum(a == "-i" for a in inputs) - 1
        fi, fo = CFG.get("音乐_淡入秒", 1.0), CFG.get("音乐_淡出秒", 2.5)
        hi, lo = CFG.get("音乐_停顿时", 0.24), CFG.get("音乐_说话时", 0.12)
        filt.append(f"[0:a]asplit=2[v0][vk]")
        mix[0] = "[v0]"
        filt.append(f"[{n}:a]aresample=48000,aformat=channel_layouts=stereo,atrim=0:{dur},volume={hi},"
                    f"afade=t=in:d={fi},afade=t=out:st={max(0, dur - fo)}:d={fo}[m0]")
        # 说话时压低：人声当侧链，压到约 说话时/停顿时 的比例
        ratio = max(2, hi / lo * 2)
        filt.append(f"[m0][vk]sidechaincompress=threshold=0.02:ratio={ratio:.1f}:attack=20:release={int(CFG.get('音乐_压低过渡秒', 0.3) * 1000)}[m]")
        mix.append("[m]")
    if len(mix) == 1:
        subprocess.run(["cp", video, out], check=True); print("没有音效和音乐可加"); return
    filt.append(f"{''.join(mix)}amix=inputs={len(mix)}:normalize=0:dropout_transition=0,alimiter=limit=0.95[a]")
    subprocess.run(["ffmpeg", "-loglevel", "error", "-y", *inputs, "-filter_complex", ";".join(filt),
                    "-map", "0:v", "-map", "[a]", "-c:v", "copy", "-c:a", "aac", "-b:a", "192k", "-t", str(dur), out], check=True)
    print(f"声音：音效 {len(mix) - 1 - (1 if music else 0)} 个，音乐 {music.relative_to(LIB) if music else '无'}")


if __name__ == "__main__":
    main(*sys.argv[1:5])
