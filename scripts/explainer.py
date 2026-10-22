"""花伦解释视频底座（Manim）。

每集分镜继承 NarratedScene，用 self.say("旁白", 动画...) 推进：
- 旁白音频：edge=免费 edge-tts（零配置默认，渲染时现生成）；clone=本地配音 Skill 的克隆声音（可选，由 render.sh 预生成）
- 量出音频时长，让动画和停顿刚好填满这句话
- 屏幕底部同步显示这句字幕
简笔画素材从 doodles 导入，不在分镜里各画各的。
"""
import json
import os
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from manim import *  # noqa: E402
from audio_key import ENGINE, key  # noqa: E402
from tts_edge import speak  # noqa: E402
from doodles import *  # noqa: E402,F401
from theme import T, tex_preamble  # noqa: E402

CACHE = Path(os.environ.get("EXPLAINER_AUDIO_CACHE", "audio_cache"))
FONT = T.font
GAP = 0.15  # 每句话后的留白（秒）

config.background_color = T.bg
for _cls in (MathTex, Tex):
    _cls.set_default(color=T.ink)
if tex_preamble():  # 公式字体跟随主题（xelatex + fontspec + mathastext）
    config.tex_template = TexTemplate(tex_compiler="xelatex", output_format=".xdv", preamble=tex_preamble())


def tts(text: str) -> Path:
    CACHE.mkdir(exist_ok=True)
    out = CACHE / key(text)
    if out.exists():
        return out
    if ENGINE != "edge":
        raise RuntimeError(f"缺少 {ENGINE} 音频，请用 render.sh 渲染（会先批量预生成）：{text}")
    if speak(text, str(out)):
        return out
    raise RuntimeError(f"配音失败：{text}")


def duration(path: Path) -> float:
    r = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(path)],
                       capture_output=True, text=True, check=True)
    return float(r.stdout.strip())


def zh(text, size=36, color=None, **kw):
    kw.setdefault("weight", getattr(T, "weight", "NORMAL"))  # 主题可指定字重（如复古风用特黑）
    return Text(text, font=FONT, font_size=size, color=color or T.ink, **kw)


def subtitle(text, size=30):
    """字幕一行放不下（手写字体偏宽）时，在最靠近中间的标点处折成两行。"""
    one = zh(text, size)
    if one.width <= config.frame_width - 1.2:
        return one
    marks = [i + 1 for i, ch in enumerate(text[:-1]) if ch in "，。；：、？！,"]
    cut = min(marks, key=lambda i: abs(i - len(text) / 2)) if marks else len(text) // 2
    return VGroup(zh(text[:cut], size), zh(text[cut:], size)).arrange(DOWN, buff=0.12)


class NarratedScene(Scene):
    """旁白不交给 Manim 混音（实测会偶发整句丢声），而是记下每句开始的秒数，
    渲染完由 mux_audio.py 用 ffmpeg 按时间贴回去，并逐句核对。"""

    def setup(self):
        self.timeline = []
        self.hud = None
        if getattr(T, "hud", False):
            self._build_hud()

    # ---------- 游戏状态栏（主题 hud=True 时才有）----------
    def _build_hud(self):
        def heart():
            px = [(1, 0), (2, 0), (4, 0), (5, 0), (0, 1), (1, 1), (2, 1), (3, 1), (4, 1), (5, 1), (6, 1),
                  (0, 2), (1, 2), (2, 2), (3, 2), (4, 2), (5, 2), (6, 2), (1, 3), (2, 3), (3, 3), (4, 3), (5, 3),
                  (2, 4), (3, 4), (4, 4), (3, 5)]
            return VGroup(*[Square(0.07, fill_color=T.c1, fill_opacity=1, stroke_width=0).move_to([x * 0.07, -y * 0.07, 0])
                            for x, y in px])
        hearts = VGroup(*[heart() for _ in range(3)]).arrange(RIGHT, buff=0.12)
        lv = zh("Lv.1", 22, T.ink)
        frame = Rectangle(width=1.8, height=0.22, stroke_color=T.ink, stroke_width=4, fill_color=T.sub_bg, fill_opacity=1)
        self._xp_w = frame.width - 0.08
        fill = Rectangle(width=0.001, height=0.14, stroke_width=0, fill_color=T.good, fill_opacity=1)
        fill.align_to(frame, LEFT).shift(RIGHT * 0.04)
        bar = VGroup(frame, fill)
        # 横排一行贴顶（爱心 · Lv.1 · 经验条），避免压到图表左上角的坐标轴标签
        self.hud = VGroup(hearts, lv, bar).arrange(RIGHT, buff=0.2).to_corner(UL, buff=0.2)
        self._xp_fill, self._xp_frame = fill, frame
        self.add_foreground_mobjects(self.hud)

    def gain_xp(self, ratio):
        """经验条涨到 ratio（0–1），头顶弹「+1 XP」金币。无 hud 的主题什么都不做。"""
        if not self.hud:
            return
        new = Rectangle(width=max(0.001, self._xp_w * ratio), height=0.14, stroke_width=0, fill_color=T.good, fill_opacity=1)
        new.move_to(self._xp_frame).align_to(self._xp_frame, LEFT).shift(RIGHT * 0.04)
        coin = Circle(radius=0.13, fill_color=T.highlight, fill_opacity=1, stroke_color=T.ink, stroke_width=3)
        pop = VGroup(coin, zh("+1 XP", 24, T.ink)).arrange(RIGHT, buff=0.1).next_to(self._xp_frame, RIGHT, buff=0.25)
        self.play(Transform(self._xp_fill, new), FadeIn(pop, shift=UP * 0.2), run_time=0.5)
        self.play(FadeOut(pop, shift=UP * 0.2), run_time=0.3)

    def clear_stage(self, run_time=0.4):
        """清空画面但保留状态栏和右上角板块标签（分镜里统一用它，不要直接 FadeOut 全部）。"""
        keep = {id(m) for m in (self.hud, getattr(self, "_tag", None)) if m is not None}
        gone = [m for m in self.mobjects if id(m) not in keep]
        if gone:
            self.play(FadeOut(Group(*gone)), run_time=run_time)

    def tear_down(self):
        out = Path(os.environ.get("EXPLAINER_TIMELINE", "timeline.json"))
        out.write_text(json.dumps({"duration": round(self.time, 3), "clips": self.timeline}, ensure_ascii=False))

    def say(self, text, *anims, anim_ratio=0.7):
        """读一句旁白；anims 在这句话的前 anim_ratio 时间里播完，剩下的时间停住让人看。
        旁白必须是字符串字面量（render.sh 靠静态扫描预生成克隆音频）。"""
        audio = tts(text)
        total = duration(audio) + GAP
        sub = subtitle(text).to_edge(DOWN, buff=0.4)
        if getattr(T, "panel", False):  # 像素对话框：米白底 + 粗黑直角描边
            bg = Rectangle(width=sub.width + 0.5, height=sub.height + 0.35, fill_color=T.sub_bg, fill_opacity=1,
                           stroke_color=T.ink, stroke_width=6).move_to(sub)
        else:
            bg = BackgroundRectangle(sub, color=T.sub_bg, fill_opacity=0.85, buff=0.14)
        self.timeline.append({"t": round(self.time, 3), "file": str(audio.resolve())})
        self.add_foreground_mobjects(bg, sub)
        used = 0
        if anims:
            used = max(0.4, total * anim_ratio)
            self.play(*anims, run_time=used)
        self.wait(max(0.05, total - used))
        self.remove_foreground_mobjects(bg, sub)
        self.remove(bg, sub)

    def title_card(self, text, topic, sections=None, lines=None):
        """开场，像老师上课一样不赶：
        text：先报题，如「这节课我们来讲供需，也就是价格是怎么定出来的。」
        只讲一个知识点：不传 sections，报完题直接进入。
        分板块：sections 是屏幕上的目录名，lines 是逐条口语旁白（与 sections 一一对应），
        如「我们分三点来讲。第一点，先讲买的人，也就是需求。」每说一条亮一条，说完停一下再开讲。
        所有旁白都必须是字符串字面量（预生成配音靠静态扫描）。"""
        title = zh(topic, 72, T.ink)
        line = Line(LEFT * 2.5, RIGHT * 2.5, color=T.accent, stroke_width=4).next_to(title, DOWN, buff=0.25)
        head = VGroup(title, line)
        if not sections:
            self.say(text, Write(title), Create(line))
        else:
            items = VGroup(*[zh(f"{i}. {s}", 34, T.ink) for i, s in enumerate(sections, 1)]) \
                .arrange(DOWN, aligned_edge=LEFT, buff=0.3)
            VGroup(head, items).arrange(DOWN, buff=0.6)
            self.say(text, Write(title), Create(line))
            for it, ln in zip(items, lines or [""] * len(items)):
                if ln:
                    self.say(ln, FadeIn(it, shift=RIGHT * 0.3), anim_ratio=0.4)
                else:
                    self.play(FadeIn(it, shift=RIGHT * 0.3), run_time=0.6)
        self.wait(0.8)
        self._n_sections = len(sections or [])
        self.clear_stage(0.5)

    def _section_tag(self, index, name):
        num = zh(f"{index}", 26, T.bg)
        dot = Circle(radius=0.22, color=T.accent, fill_opacity=1, stroke_width=0).move_to(num)
        return VGroup(VGroup(dot, num), zh(name, 26, T.ink)).arrange(RIGHT, buff=0.15).to_corner(UR, buff=0.35)

    def section(self, text, index, name, *anims, inline=False):
        """板块过场，之后右上角一直挂着当前板块标签。
        默认整屏「第 N 部分 + 板块名」；inline=True 不清屏（图表要接着用），只换右上角标签，anims 与旁白同播。"""
        tag = self._section_tag(index, name)
        old = getattr(self, "_tag", None)
        swap = [FadeOut(old, shift=UP * 0.2)] if old and old in self.mobjects else []
        if inline:
            self.say(text, *swap, FadeIn(tag, shift=DOWN * 0.2), *anims)
        else:
            num = zh(f"第 {index} 部分", 32, T.muted)
            nm = zh(name, 56, T.ink)
            g = VGroup(num, nm).arrange(DOWN, buff=0.3)
            self.say(text, *swap, FadeIn(num, shift=DOWN * 0.2), Write(nm), *anims)
            self.play(FadeOut(g), FadeIn(tag, shift=DOWN * 0.2), run_time=0.4)
        self._tag = tag
        n = getattr(self, "_n_sections", 0)
        if n and index > 1:  # 讲完上一点，经验条 +1
            self.gain_xp((index - 1) / n)
