"""简笔画素材库：火柴人、山、水瓶、小摊、太阳、对话气泡……

统一风格：圆头线条、少量强调色，颜色全部取自 theme.py，抽象但一眼能认出来，帮助记忆。
所有函数返回 VGroup，默认以原点为中心，用 .move_to() / .scale() 摆放。
新画法加在这里，各集分镜直接复用，不在分镜里各画各的。
"""
from manim import *
from theme import T

INK = T.ink
STROKE = 5


def _line(a, b, color=INK, w=STROKE):
    return Line(a, b, color=color, stroke_width=w).set_cap_style(CapStyleType.ROUND)


def face(center, r, mood="neutral", color=INK):
    """mood: neutral / happy / sad / surprised"""
    eyes = VGroup(*[Dot(center + [dx * r * 0.4, r * 0.15, 0], radius=r * 0.1, color=color) for dx in (-1, 1)])
    m = center + DOWN * r * 0.35
    if mood == "happy":
        mouth = ArcBetweenPoints(m + LEFT * r * 0.35, m + RIGHT * r * 0.35, angle=PI / 2)
    elif mood == "sad":
        mouth = ArcBetweenPoints(m + LEFT * r * 0.3 + DOWN * r * 0.1, m + RIGHT * r * 0.3 + DOWN * r * 0.1, angle=-PI / 2)
    elif mood == "surprised":
        mouth = Circle(radius=r * 0.13).move_to(m)
    else:
        mouth = _line(m + LEFT * r * 0.25, m + RIGHT * r * 0.25)
    mouth.set_stroke(color, width=3)
    return VGroup(eyes, mouth)


def stick_figure(pose="stand", mood="neutral", color=INK, height=2.0):
    """火柴人。pose: stand / walk / wave / carry（双手举过头扛东西）/ shrug（摊手）/ think（手托下巴）"""
    s = height / 2.0
    r = 0.22 * s
    head_c = UP * 0.78 * s
    neck, hip = UP * 0.55 * s, DOWN * 0.15 * s
    head = Circle(radius=r, color=color, stroke_width=STROKE).move_to(head_c)
    body = _line(neck, hip, color)
    sh = UP * 0.4 * s
    # 每条手臂：肩 → 肘 → 手（相对肩膀的偏移，按身高缩放）；折线避免手臂穿过脸
    arms = {
        "stand": [[(-0.15, -0.22), (-0.3, -0.45)], [(0.15, -0.22), (0.3, -0.45)]],
        "walk": [[(-0.2, -0.18), (-0.35, -0.35)], [(0.12, -0.25), (0.3, -0.4)]],
        "wave": [[(-0.15, -0.22), (-0.3, -0.45)], [(0.3, 0.05), (0.42, 0.42)]],
        "carry": [[(-0.38, 0.05), (-0.32, 0.6)], [(0.38, 0.05), (0.32, 0.6)]],
        "shrug": [[(-0.3, -0.1), (-0.5, 0.08)], [(0.3, -0.1), (0.5, 0.08)]],
        "think": [[(-0.15, -0.22), (-0.3, -0.45)], [(0.32, -0.12), (0.12, 0.12)]],
    }[pose]
    legs = [[(-0.28, -0.6)], [(0.28, -0.6)]] if pose != "walk" else [[(-0.35, -0.55)], [(0.2, -0.6)]]
    def limb(start, pts):
        verts = [start] + [start + np.array([x, y, 0]) * s for x, y in pts]
        return VMobject(color=color, stroke_width=STROKE).set_points_as_corners(verts).set_cap_style(CapStyleType.ROUND)
    limbs = VGroup(*[limb(sh, a) for a in arms], *[limb(hip, l) for l in legs])
    g = VGroup(head, face(head_c, r, mood, color), body, limbs)
    return g.move_to(ORIGIN)


def mountain(width=5, height=3.2, snow=True, color=INK):
    base_l, base_r, peak = [-width / 2, -height / 2, 0], [width / 2, -height / 2, 0], [0, height / 2, 0]
    m = Polygon(base_l, peak, base_r, color=color, stroke_width=STROKE, fill_color=T.fill, fill_opacity=0.7)
    g = VGroup(m)
    if snow:
        k = 0.28
        cap = Polygon(peak, [-width / 2 * k, height / 2 - height * k, 0], [-width * 0.05, height / 2 - height * k * 0.8, 0],
                      [width * 0.06, height / 2 - height * k, 0], [width / 2 * k, height / 2 - height * k, 0],
                      color=INK, stroke_width=2, fill_color=WHITE, fill_opacity=0.95)
        g.add(cap)
    return g


def bottle(color=None, height=0.9):
    color = color or T.c1
    w = height * 0.42
    bodyr = RoundedRectangle(width=w, height=height * 0.72, corner_radius=w * 0.25, color=INK, stroke_width=4,
                             fill_color=color, fill_opacity=0.75)
    neck_ = Rectangle(width=w * 0.45, height=height * 0.16, color=INK, stroke_width=4).next_to(bodyr, UP, buff=0)
    cap = Rectangle(width=w * 0.55, height=height * 0.1, color=INK, stroke_width=3, fill_color=INK,
                    fill_opacity=1).next_to(neck_, UP, buff=0)
    wave = FunctionGraph(lambda x: 0.04 * np.sin(x * 18), x_range=[-w * 0.4, w * 0.4], color=WHITE, stroke_width=2)
    wave.move_to(bodyr.get_center() + UP * height * 0.1)
    return VGroup(bodyr, neck_, cap, wave)


def price_tag(text, color=None, size=30):
    color = color or T.key
    t = Text(text, font=T.font, font_size=size, color=color, weight=getattr(T, "weight", "NORMAL"))
    box = RoundedRectangle(width=t.width + 0.3, height=t.height + 0.2, corner_radius=0.08, color=color, stroke_width=3)
    return VGroup(box, t.move_to(box))


def stall(width=1.8, color=INK):
    """小摊：木色台面 + 两根支杆 + 往下垂的条纹遮阳棚"""
    table = Rectangle(width=width, height=0.6, color=color, stroke_width=STROKE, fill_color="#8d6e63", fill_opacity=0.8)
    top = table.get_top()
    poles = VGroup(_line(table.get_corner(UL), table.get_corner(UL) + UP * 1.1),
                   _line(table.get_corner(UR), table.get_corner(UR) + UP * 1.1))
    bar_y = UP * 1.1
    bar = _line(table.get_corner(UL) + bar_y + LEFT * 0.15, table.get_corner(UR) + bar_y + RIGHT * 0.15)
    n, w0 = 5, width + 0.3
    x0 = table.get_corner(UL) + bar_y + LEFT * 0.15
    flaps = VGroup(*[Polygon(x0 + RIGHT * w0 * i / n, x0 + RIGHT * w0 * (i + 1) / n,
                             x0 + RIGHT * w0 * (i + 0.5) / n + DOWN * 0.3, color=color, stroke_width=3,
                             fill_color=(T.accent if i % 2 == 0 else T.bg), fill_opacity=0.9) for i in range(n)])
    return VGroup(poles, table, bar, flaps)


def sun(r=0.45):
    core = Circle(radius=r, color="#f4b400", fill_opacity=0.9, stroke_width=3)
    rays = VGroup(*[_line(rotate_vector(RIGHT * r * 1.3, a), rotate_vector(RIGHT * r * 1.7, a), "#f4b400", 4)
                    for a in np.linspace(0, TAU, 9)[:-1]])
    return VGroup(core, rays)


def sweat(n=3, color=None):
    color = color or T.c1
    """头边的汗滴/辛苦符号"""
    return VGroup(*[Line(ORIGIN, DOWN * 0.18, color=color, stroke_width=4).shift(RIGHT * 0.15 * i + UP * 0.08 * (i % 2))
                    for i in range(n)])


def bubble(text, size=28, color=INK):
    t = Text(text, font=T.font, font_size=size, color=color, weight=getattr(T, "weight", "NORMAL"))
    box = RoundedRectangle(width=t.width + 0.4, height=t.height + 0.3, corner_radius=0.2, color=color, stroke_width=3)
    tail = Polygon(box.get_bottom() + LEFT * 0.15, box.get_bottom() + RIGHT * 0.05, box.get_bottom() + DOWN * 0.3 + LEFT * 0.3,
                   color=color, stroke_width=3, fill_color=T.bg, fill_opacity=1)
    return VGroup(tail, box, t.move_to(box))


def crate(n=3, size=0.32):
    """一箱水：几只小瓶并排"""
    return VGroup(*[bottle(height=size * 2.2) for _ in range(n)]).arrange(RIGHT, buff=0.05)


def monitor(content="", color=None, width=2.4, size=26):
    """电脑屏幕：方框屏 + 支架底座，屏里可写一行字（如 code / GAME）"""
    color = color or T.c1
    h = width * 0.62
    scr = RoundedRectangle(width=width, height=h, corner_radius=0.08, color=INK, stroke_width=STROKE,
                           fill_color=T.bg, fill_opacity=1)
    stand_ = _line(scr.get_bottom(), scr.get_bottom() + DOWN * 0.3)
    foot = _line(scr.get_bottom() + DOWN * 0.3 + LEFT * width * 0.18, scr.get_bottom() + DOWN * 0.3 + RIGHT * width * 0.18)
    g = VGroup(scr, stand_, foot)
    if content:
        t = Text(content, font=T.font, font_size=size, color=color, weight=getattr(T, "weight", "NORMAL"))
        g.add(t.scale_to_fit_width(min(t.width, width * 0.8)).move_to(scr))
    return g


def gamepad(color=None, width=1.0):
    """游戏手柄：圆角机身 + 左十字键 + 右两颗按钮"""
    color = color or T.c2
    body = RoundedRectangle(width=width, height=width * 0.5, corner_radius=width * 0.22, color=INK, stroke_width=4,
                            fill_color=color, fill_opacity=0.8)
    c = body.get_center() + LEFT * width * 0.25
    cross = VGroup(_line(c + LEFT * 0.09 * width, c + RIGHT * 0.09 * width, INK, 4),
                   _line(c + UP * 0.09 * width, c + DOWN * 0.09 * width, INK, 4))
    btns = VGroup(*[Dot(body.get_center() + RIGHT * width * dx + UP * width * dy, radius=width * 0.045, color=INK)
                    for dx, dy in ((0.2, 0.05), (0.3, -0.05))])
    return VGroup(body, cross, btns)


def rice_cooker(height=1.4):
    """电饭锅：锅身 + 圆盖 + 把手 + 一个小灯，可配蒸汽"""
    w = height * 1.1
    pot = RoundedRectangle(width=w, height=height * 0.62, corner_radius=0.15, color=INK, stroke_width=STROKE,
                           fill_color=T.fill, fill_opacity=0.8)
    lid = ArcBetweenPoints(pot.get_corner(UL), pot.get_corner(UR), angle=-PI / 2.4, color=INK, stroke_width=STROKE)
    knob = _line(lid.point_from_proportion(0.5), lid.point_from_proportion(0.5) + UP * 0.12)
    light = Dot(pot.get_center() + DOWN * height * 0.12, radius=0.07, color=T.accent)
    return VGroup(pot, lid, knob, light)


def steam(n=3, color=None):
    """往上飘的几缕蒸汽"""
    color = color or T.muted
    return VGroup(*[FunctionGraph(lambda y: 0.06 * np.sin(y * 9), x_range=[0, 0.5], color=color, stroke_width=3)
                    .rotate(PI / 2).shift(RIGHT * 0.18 * i) for i in range(n)])


def anger_mark(size=0.4, color=None):
    """生气符号：四个小弧角组成的「井」字形青筋"""
    color = color or T.accent
    s = size / 2
    arcs = VGroup(*[ArcBetweenPoints(rotate_vector(np.array([s * 0.25, s, 0]), a), rotate_vector(np.array([s, s * 0.25, 0]), a),
                                     angle=PI / 2, color=color, stroke_width=5) for a in (0, PI / 2, PI, -PI / 2)])
    return arcs
