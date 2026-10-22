"""视觉风格唯一真源：字体、背景、墨水色、强调色、公式字体都只在这里定义。

换风格 = 加一个主题 / 设 EXPLAINER_THEME，分镜和简笔画只用下面的语义色名，不写死颜色。
语义色：ink 正文与线条 · muted 坐标轴等次要线 · c1 第一主角（如需求）· c2 第二主角（如供给）
        accent 结论/警示 · good 正向 · key 关键点（交点、答案）· fill 大面积填充 · sub_bg 字幕底
"""
import os

THEMES = {
    # 王虹手写风（默认）：取自花伦原创共享 Skill z-wanghong-handwritten-ppt 的默认 cream 主题
    # （灵感来自王虹获奖演讲的手写 PPT）——HanziPen SC 手写字体、暖白纸 #f7f5ed、深蓝墨水 #18224d、蓝/玫红强调；
    # 该调色板没有橙色，c2 橙、填充色、字幕底色为本 Skill 补充，绿色压深以便在浅底上看清
    "wanghong": dict(
        label="王虹手写风",
        font="HanziPen SC", math_font="HanziPen SC",
        bg="#f7f5ed", ink="#18224d", muted="#6a718f",
        c1="#2f6cf6", c2="#e07a1f", accent="#ec3f79", good="#2e9e3e", key="#ec3f79",
        fill="#dcd8c8", sub_bg="#ebe6d3", highlight="#fff04f",
    ),
    # 3B1B 深色风：仿 3Blue1Brown 的深灰底 + 亮色线条（试做 v1–v3 的样子）
    "3b1b": dict(
        label="3B1B 深色风",
        font="PingFang SC", math_font=None,
        bg="#14161a", ink="#f2f2f2", muted="#9aa0a6",
        c1="#4da3ff", c2="#ff9f43", accent="#ff6b6b", good="#5cd65c", key="#ffd166",
        fill="#3a4150", sub_bg="#000000", highlight="#ffd166",
    ),
    # 美式复古风：用户提供的「美式复古配色」参考图——近黑底 + 复古黄 #FBC359 / 草绿 #73A642 / 灰蓝绿 #4B848A，
    # 中文用粗壮的兰亭特黑贴近复古招牌字，公式字母数字用 Futura Bold；红橙 key 与奶油色 ink 取自参考海报
    "retro": dict(
        label="美式复古风",
        font="Lantinghei SC", weight="HEAVY", math_font="Futura Bold",
        bg="#1b1b1b", ink="#f3e6c4", muted="#8c8a7e",
        c1="#FBC359", c2="#73A642", accent="#e4572e", good="#73A642", key="#e4572e",
        fill="#4B848A", sub_bg="#000000", highlight="#FBC359",
    ),
    # 像素游戏风：用户提供的像素 RPG 海报参考（Small progress still gives you XP）——天空蓝底、米白粗黑描边对话框、
    # 爱心红 / 草地绿 / 金币橙；中英文与公式统一用开源「缝合像素字体」（Fusion Pixel，OFL，装在 ~/Library/Fonts）
    # panel=字幕用像素对话框；hud=左上角爱心 + 经验条，每进入一个板块 +1 XP
    "pixel": dict(
        label="像素游戏风",
        font="Fusion Pixel 12px Prop zh-Hans", math_font="Fusion Pixel 12px Prop zh-Hans",
        bg="#9fd6f2", ink="#2a1f1a", muted="#4f6272",
        c1="#d94a3a", c2="#3c8d3f", accent="#d94a3a", good="#3c8d3f", key="#e8761c",
        fill="#6c8fbf", sub_bg="#fdf3dc", highlight="#f2b632",
        panel=True, hud=True,
    ),
}

NAME = os.environ.get("EXPLAINER_THEME", "wanghong")
T = type("Theme", (), THEMES[NAME])  # 用法：T.ink、T.c1 ……


def tex_preamble():
    """公式字体跟随主题：math_font 为空时用 LaTeX 默认教科书字体。
    用 unicode-math 按范围换字体：字母、数字、+ − = * 用主题字体，其余符号（箭头、分数线等）用 Latin Modern Math 兜底。
    （旧做法 mathastext 只能换字母、换不了数字，已弃用）"""
    if not T.math_font:
        return None
    rng = r'range={up/num,up/{Latin,latin},it/{Latin,latin},"002B,"2212,"003D,"002A}'
    return (r"\usepackage{amsmath}\usepackage{unicode-math}\setmathfont{latinmodern-math.otf}"
            r"\setmathfont[" + rng + "]{" + T.math_font + "}")
