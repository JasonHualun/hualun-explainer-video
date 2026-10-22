"""edge 模式下合成一句旁白：有本地配音 Skill 用它的 speak.sh，否则直接调 edge-tts（pip install edge-tts）。"""
import shutil
import subprocess
import sys

from audio_key import EDGE_VOICE, RATE, TTS_SKILL


def speak(text: str, out: str) -> bool:
    for _ in range(2):  # 网络偶发失败重试一次
        if TTS_SKILL:
            cmd = ["bash", str(TTS_SKILL / "speak.sh"), text, out, "--rate", RATE]
        else:
            exe = shutil.which("edge-tts")
            base = [exe] if exe else [sys.executable, "-m", "edge_tts"]
            cmd = base + ["--voice", EDGE_VOICE, f"--rate={RATE}", "--text", text, "--write-media", out]
        try:
            if subprocess.run(cmd).returncode == 0:
                return True
        except FileNotFoundError:
            break
    if not TTS_SKILL and not shutil.which("edge-tts"):
        print("找不到 edge-tts：请先 pip install edge-tts", file=sys.stderr)
    return False
