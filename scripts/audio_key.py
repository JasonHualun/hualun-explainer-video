"""旁白音频的缓存命名与配音引擎选择（无第三方依赖，渲染端和预生成端共用，保证同一句话对得上同一个文件）。

配音引擎（EXPLAINER_TTS）：
- edge  = 免费 edge-tts（需联网，零配置默认）；有本地配音 Skill 时优先用它的 speak.sh
- clone = 本地克隆声音（需本地配音 Skill + VoxCPM2，可选升级）
不设置时：检测到本地配音 Skill 和 VoxCPM2 就用 clone，否则用 edge。
"""
import hashlib
import os
from pathlib import Path


def _tts_skill():
    """本地配音 Skill 的 scripts 目录；找不到返回 None。可用 EXPLAINER_TTS_SKILL 指定。"""
    env = os.environ.get("EXPLAINER_TTS_SKILL")
    cands = [Path(env).expanduser()] if env else [
        Path.home() / d / "skills/hualun-local-tts/scripts" for d in (".hermes", ".claude", ".codex", ".cursor", ".agents")]
    for c in cands:
        if (c / "speak.sh").exists():
            return c
    return None


TTS_SKILL = _tts_skill()
VOXCPM = Path(os.environ.get("VOXCPM_DIR", Path.home() / "Tools/apps/voxcpm2")).expanduser()
_HAS_CLONE = TTS_SKILL is not None and (TTS_SKILL / "clone_batch.py").exists() and (VOXCPM / ".venv/bin/python").exists()
ENGINE = os.environ.get("EXPLAINER_TTS") or ("clone" if _HAS_CLONE else "edge")
RATE = os.environ.get("EXPLAINER_RATE", "+0%")       # 语速，edge 直接用；clone 换算成 atempo
PROFILE = os.environ.get("EXPLAINER_VOICE_PROFILE", "explainer-profile.json")  # clone 用的声音档案
EDGE_VOICE = os.environ.get("EXPLAINER_EDGE_VOICE", "zh-CN-XiaoxiaoNeural")   # edge-tts 音色（如童声 zh-CN-XiaoyiNeural）
EDGE_DIRECT = TTS_SKILL is None or "EXPLAINER_EDGE_VOICE" in os.environ    # 指定了音色就直接用 edge-tts


def key(text: str) -> str:
    if ENGINE == "clone":
        voice = f"clone:{PROFILE}"
    else:
        voice = f"edge:{EDGE_VOICE}" if EDGE_DIRECT else "edge:skill"
    return hashlib.md5(f"{voice}|{RATE}|{text}".encode()).hexdigest()[:12] + ".mp3"


def atempo() -> float:
    return 1 + float(RATE.rstrip("%")) / 100
