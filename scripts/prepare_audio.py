"""扫描分镜里所有 self.say / title_card / section 的旁白，批量预生成缺失的音频（clone 模式必需；edge 模式渲染时现生成即可）。

用法：python3 prepare_audio.py 分镜.py 音频缓存目录
"""
import ast
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from audio_key import ENGINE, PROFILE, RATE, atempo, key  # noqa: E402

TTS_SKILL = Path.home() / ".hermes/skills/hualun-local-tts/scripts"
VOXCPM = Path(os.environ.get("VOXCPM_DIR", Path.home() / "Tools/apps/voxcpm2"))


def lines(scene_file):
    tree = ast.parse(Path(scene_file).read_text(encoding="utf-8"))
    for n in ast.walk(tree):
        if isinstance(n, ast.Call) and getattr(n.func, "attr", "") in ("say", "title_card", "section") and n.args \
                and isinstance(n.args[0], ast.Constant) and isinstance(n.args[0].value, str):
            yield n.args[0].value
        if isinstance(n, ast.Call) and getattr(n.func, "attr", "") == "title_card":
            for kw in n.keywords:
                if kw.arg == "lines" and isinstance(kw.value, (ast.List, ast.Tuple)):
                    yield from (e.value for e in kw.value.elts if isinstance(e, ast.Constant) and isinstance(e.value, str))


def generate(texts, cache):
    """把缺的旁白音频补齐（edge 逐句调共享配音；clone 模型只加载一次批量生成）。"""
    cache = Path(cache).resolve()
    cache.mkdir(parents=True, exist_ok=True)
    todo = [{"text": t, "out": str(cache / key(t))} for t in dict.fromkeys(texts) if not (cache / key(t)).exists()]
    print(f"旁白共 {len(texts)} 句，需新生成 {len(todo)} 句（{ENGINE}）")
    if not todo:
        return
    if ENGINE == "edge":
        for j in todo:
            for _ in range(2):  # 网络偶发失败重试一次
                if subprocess.run(["bash", str(TTS_SKILL / "speak.sh"), j["text"], j["out"], "--rate", RATE]).returncode == 0:
                    break
            else:
                sys.exit(f"配音失败：{j['text']}")
        return
    raw = [{"text": j["text"], "out": j["out"] + ".raw.wav"} for j in todo]
    with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False) as f:
        json.dump(raw, f, ensure_ascii=False)
    subprocess.run([str(VOXCPM / ".venv/bin/python"), str(TTS_SKILL / "clone_batch.py"), f.name, "--profile", PROFILE], check=True)
    for j in todo:
        subprocess.run(["ffmpeg", "-loglevel", "error", "-y", "-i", j["out"] + ".raw.wav",
                        "-filter:a", f"atempo={atempo()}", j["out"]], check=True)
        os.remove(j["out"] + ".raw.wav")


if __name__ == "__main__":
    scene, cache = sys.argv[1], sys.argv[2]
    texts = list(lines(scene))
    if ENGINE == "edge":  # Manim 路线：edge 在渲染时现生成，这里只报数
        n = sum(not (Path(cache) / key(t)).exists() for t in dict.fromkeys(texts))
        print(f"旁白共 {len(texts)} 句，需新生成 {n} 句（edge）")
        sys.exit(0)
    generate(texts, cache)
