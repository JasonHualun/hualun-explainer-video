"""旁白音频的缓存命名（无第三方依赖，渲染端和预生成端共用，保证同一句话对得上同一个文件）。"""
import hashlib
import os

ENGINE = os.environ.get("EXPLAINER_TTS", "clone")     # clone = 本人克隆声音（VoxCPM2，默认）；edge = Hermes 云夏
RATE = os.environ.get("EXPLAINER_RATE", "+0%")       # 语速，edge 直接用；clone 换算成 atempo
PROFILE = os.environ.get("EXPLAINER_VOICE_PROFILE", "explainer-profile.json")  # clone 用的声音档案


def key(text: str) -> str:
    voice = f"{ENGINE}:{PROFILE}" if ENGINE == "clone" else ENGINE
    return hashlib.md5(f"{voice}|{RATE}|{text}".encode()).hexdigest()[:12] + ".mp3"


def atempo() -> float:
    return 1 + float(RATE.rstrip("%")) / 100
