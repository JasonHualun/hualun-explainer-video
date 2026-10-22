"""示范分镜：供需（通用知识讲解，非逐页原文蒸馏）。
教序：困惑 → 类比 → 定义 → 例子 → 公式 → 回扣。左边画图讲原理，右边简笔画讲故事。
渲染：复制到集目录改名 分镜.py 后，bash ../scripts/render.sh <集目录>/分镜.py SupplyDemand --draft
"""
from explainer import *

# 颜色只用 theme 的语义色：需求=c1，供给=c2，关键点=key，警示=accent，正向=good
BLUE_D, ORANGE_S, GOLD_E, RED_E = T.c1, T.c2, T.key, T.accent
RIGHT_SPOT = RIGHT * 4.5 + UP * 0.6  # 右侧简笔画小剧场的位置


class SupplyDemand(NarratedScene):
    def construct(self):
        # ⓪ 开场：主题 + 这期分几块
        self.title_card("这节课我们来讲供需，也就是，价格到底是怎么定出来的。",
                        "供需：价格怎么定", ["买的人：需求", "卖的人：供给", "价格怎么定：均衡"],
                        lines=["我们分三点来讲。第一点，先讲买的人，也就是需求。",
                               "第二点，讲卖的人，也就是供给。",
                               "第三点，把两边放在一起，看价格是怎么定下来的。"])

        # ① 制造困惑：同一瓶水，山脚 2 元，山顶 10 元
        mt = mountain(7, 4.2).shift(DOWN * 0.6)
        base = mt.get_corner(DL) + RIGHT * 0.2
        st_low = stall(1.3).scale(0.7).next_to(base, LEFT, buff=-0.2).align_to(mt, DOWN)
        tag_low = price_tag("¥2").next_to(st_low, UP, buff=0.15)
        hiker = stick_figure("walk", "happy", height=1.2).next_to(st_low, RIGHT, buff=0.1).align_to(mt, DOWN)
        self.say("暑假去爬山，山脚下一瓶水，卖两块钱。",
                 FadeIn(mt), FadeIn(st_low, shift=UP), FadeIn(tag_low), FadeIn(hiker))
        peak = mt[0].get_top()
        st_top = stall(1.3).scale(0.7).next_to(peak, RIGHT, buff=0.1).shift(DOWN * 0.3)
        tag_top = price_tag("¥10", RED_E).next_to(st_top, UP, buff=0.15)
        path = Line(hiker.get_center(), peak + UP * 0.55)
        self.say("爬到山顶，同样一瓶水，卖十块。",
                 MoveAlongPath(hiker, path), FadeIn(st_top), FadeIn(tag_top, scale=1.5))
        shock = stick_figure("shrug", "surprised", height=1.2).move_to(hiker)
        q = zh("为什么差了五倍？", 40, GOLD_E).to_edge(UP)
        self.say("水还是那瓶水，价格为什么差了五倍？", Transform(hiker, shock), Write(q))
        self.clear_stage()

        # ② 需求：价格越高，买的人越少（右边：买的人手里的瓶数跟着变）
        self.section("好，我们先来看第一点，买的人。", 1, "买的人：需求")
        ax = Axes(x_range=[0, 10, 2], y_range=[0, 10, 2], x_length=6, y_length=4.6,
                  axis_config={"include_tip": True, "color": T.muted}).shift(LEFT * 2.0 + UP * 0.3)
        xl = zh("数量", 26).next_to(ax.x_axis, RIGHT)
        yl = zh("价格", 26).next_to(ax.y_axis, UP)
        buyer = stick_figure("stand", "happy", height=1.6).move_to(RIGHT_SPOT + LEFT * 0.8)
        b_lab = zh("买的人", 24).next_to(buyer, DOWN)
        self.say("价格越高，愿意买的就越少。", Create(ax), FadeIn(xl, yl), FadeIn(buyer, b_lab))
        demand = ax.plot(lambda x: 10 - x, x_range=[0.5, 9.5], color=BLUE_D)
        d_lab = zh("需求", 28, BLUE_D).next_to(ax.c2p(8.8, 1.2), UR, buff=0.1)
        t = ValueTracker(7.5)
        dot = always_redraw(lambda: Dot(ax.c2p(t.get_value(), 10 - t.get_value()), color=BLUE_D))
        bottles = always_redraw(lambda: VGroup(*[bottle(height=0.5) for _ in range(max(1, round(t.get_value() / 1.5)))])
                                .arrange(RIGHT, buff=0.04).next_to(buyer, RIGHT, buff=0.15))
        tag = always_redraw(lambda: price_tag(f"¥{10 - t.get_value():.0f}", size=26).next_to(buyer, UP, buff=0.2))
        self.say("画出来，就是一条往下走的线，叫需求曲线。", Create(demand), FadeIn(d_lab))
        self.add(dot, bottles, tag)
        sad = stick_figure("stand", "sad", height=1.6).move_to(buyer)
        self.say("价格往上抬，这个点往左滑，手里的水就越买越少。", t.animate.set_value(1.5), Transform(buyer, sad))
        self.play(FadeOut(VGroup(dot, bottles, tag, buyer, b_lab)), run_time=0.4)
        self.remove(dot, bottles, tag)

        # ③ 供给：价格越高，卖的人越多（右边：摊位上的货跟着变多）
        seller = stick_figure("stand", "neutral", height=1.6).move_to(RIGHT_SPOT + LEFT * 1.1)
        shop = stall(1.6).scale(0.8).next_to(seller, RIGHT, buff=0.1).align_to(seller, DOWN)
        s_who = zh("卖的人", 24).next_to(seller, DOWN)
        supply = ax.plot(lambda x: x, x_range=[0.3, 9.5], color=ORANGE_S)
        s_lab = zh("供给", 28, ORANGE_S).next_to(supply.get_end(), RIGHT)
        u = ValueTracker(1.5)
        goods = always_redraw(lambda: VGroup(*[bottle(height=0.45) for _ in range(max(1, round(u.get_value() / 1.3)))])
                              .arrange(RIGHT, buff=0.03).next_to(shop[1], UP, buff=0.02))
        self.section("第二点，卖的人。价格越高，愿意卖的就越多。", 2, "卖的人：供给",
                     FadeIn(seller, shop, s_who), Create(supply), FadeIn(s_lab), inline=True)
        self.add(goods)
        happy = stick_figure("wave", "happy", height=1.6).move_to(seller)
        self.say("这是一条往上走的线，叫供给曲线。", u.animate.set_value(7.5), Transform(seller, happy))
        self.play(FadeOut(VGroup(seller, shop, s_who, goods)), run_time=0.4)
        self.remove(goods)

        # ④ 均衡：交点；高了过剩、低了短缺
        e = ax.c2p(5, 5)
        eq = Dot(e, color=GOLD_E, radius=0.1)
        guides = VGroup(DashedLine(ax.c2p(0, 5), e, color=GOLD_E), DashedLine(ax.c2p(5, 0), e, color=GOLD_E))
        p_lab = zh("均衡价格", 24, GOLD_E).next_to(ax.c2p(0, 5), LEFT)
        hands = VGroup(stick_figure("stand", "happy", height=1.4), stick_figure("stand", "happy", height=1.4)) \
            .arrange(RIGHT, buff=0.3).move_to(RIGHT_SPOT)
        deal = zh("成交！", 30, GOLD_E).next_to(hands, UP)
        self.section("第三点，价格怎么定。两条线相交处，想买的和想卖的正好一样多。", 3, "价格怎么定：均衡",
                     FadeIn(eq, scale=2), Create(guides), FadeIn(hands), Write(deal), inline=True)
        self.say("这一点的价格，就叫均衡价格。", Write(p_lab))
        self.play(FadeOut(VGroup(hands, deal)), run_time=0.3)
        high = DashedLine(ax.c2p(0, 7.4), ax.c2p(9, 7.4), color=RED_E)
        surplus = zh("卖不掉 → 降价", 26, RED_E).next_to(ax.c2p(9, 7.4), RIGHT, buff=0.3)
        self.say("价格定高了，东西卖不掉，商家只好降价。", Create(high), FadeIn(surplus))
        low = DashedLine(ax.c2p(0, 2.6), ax.c2p(9, 2.6), color=T.good)
        shortage = zh("不够卖 → 涨价", 26, T.good).next_to(ax.c2p(9, 2.6), RIGHT, buff=0.3)
        self.say("价格定低了，东西不够卖，价格就会涨。", Create(low), FadeIn(shortage))
        self.say("所以价格总会被拉回到这个交点附近。",
                 FadeOut(VGroup(high, surplus, low, shortage)), Flash(eq, color=GOLD_E))

        # ⑤ 回到山顶：背水上山很辛苦 → 供给减少 → 曲线左移 → 价格上升
        mini_mt = mountain(3, 2.2).move_to(RIGHT_SPOT + DOWN * 0.3)
        porter = VGroup(stick_figure("carry", "sad", height=1.0), ).move_to(mini_mt[0].get_left() + RIGHT * 0.6 + UP * 0.3)
        load = crate(3, 0.18).next_to(porter, UP, buff=0.0)
        drops = sweat().next_to(porter, RIGHT, buff=0.05).shift(UP * 0.3)
        climber = VGroup(porter, load, drops)
        self.say("回到山顶。水要人一箱箱背上去，愿意卖的人少了。",
                 FadeIn(mini_mt), FadeIn(climber), supply.animate.set_stroke(opacity=0.3))
        supply2 = ax.plot(lambda x: x + 3, x_range=[0, 6.5], color=ORANGE_S)
        e2 = ax.c2p(3.5, 6.5)
        eq2 = Dot(e2, color=RED_E, radius=0.1)
        self.say("供给曲线整体往左上方移，新的交点更高。",
                 TransformFromCopy(supply, supply2), s_lab.animate.next_to(supply2.get_end(), UP),
                 FadeIn(eq2), climber.animate.move_to(mini_mt[0].get_top() + UP * 0.6))
        p2 = zh("山顶价格", 24, RED_E).next_to(ax.c2p(0, 6.5), LEFT)
        self.say("所以山顶的水贵，主要不是商家黑心，而是供给变少了。",
                 Create(DashedLine(ax.c2p(0, 6.5), e2, color=RED_E)), Write(p2))
        self.clear_stage()

        # ⑥ 公式（LaTeX 排版）：逐个符号标注它在山顶卖水这个例子里代表什么、单位是什么
        def note(tex, idx, text, color, direction=DOWN, dx=0.0):
            """给公式第 idx 段加箭头标注；dx 让箭头斜着从左/右指过来，避免相邻标注挤在一起"""
            part = tex[idx]
            arrow = Arrow(part.get_edge_center(direction) + direction * 0.75 + RIGHT * dx, part.get_edge_center(direction),
                          buff=0.05, color=color, stroke_width=3, max_tip_length_to_length_ratio=0.25)
            label = zh(text, 22, color).next_to(arrow, direction, buff=0.08)
            return VGroup(arrow, label)

        fd = MathTex("Q_d", "=", "a", "-", "b", r"\cdot", "P", font_size=64, color=BLUE_D).shift(UP * 1.5)
        self.say("用公式写，也是同一件事。先看需求这一行。", Write(fd))
        n_q = note(fd, 0, "想买几瓶", BLUE_D)
        n_p = note(fd, 6, "每瓶价格（元）", GOLD_E)
        self.say("Q是想买的瓶数，P是每瓶的价格，单位是元。", FadeIn(n_q), FadeIn(n_p))
        n_a = note(fd, 2, "白送时最多要10瓶", BLUE_D, UP, dx=-1.2)
        self.say("a是价格为零时最多想要几瓶，这里是十瓶。", FadeIn(n_a))
        n_b = note(fd, 4, "每贵1元少买1瓶", BLUE_D, UP, dx=1.2)
        self.say("b是每贵一块钱，少买几瓶，这里是一瓶。", FadeIn(n_b))
        fd_num = MathTex("Q_d", "=", "10", "-", "1", r"\cdot", "P", font_size=64, color=BLUE_D).move_to(fd)
        self.say("代进数字，需求就是：Q等于十减P。",
                 FadeOut(VGroup(n_a, n_b)), TransformMatchingTex(fd, fd_num))
        self.play(FadeOut(VGroup(n_q, n_p)), run_time=0.3)

        fs = MathTex("Q_s", "=", "c", "+", "d", r"\cdot", "P", font_size=64, color=ORANGE_S).shift(DOWN * 0.6)
        n_c = note(fs, 2, "白送时肯卖0瓶", ORANGE_S, DOWN, dx=-1.2)
        n_d = note(fs, 4, "每贵1元多卖1瓶", ORANGE_S, DOWN, dx=1.2)
        self.say("供给同理：c是起步量，d是每贵一块钱，多卖几瓶。", Write(fs), FadeIn(n_c), FadeIn(n_d))
        fs_num = MathTex("Q_s", "=", "0", "+", "1", r"\cdot", "P", font_size=64, color=ORANGE_S).move_to(fs)
        self.say("代进数字，供给就是：Q等于P。", FadeOut(VGroup(n_c, n_d)), TransformMatchingTex(fs, fs_num))

        solve = MathTex(r"10 - P = P", r"\;\Rightarrow\;", r"P^{*} = 5", font_size=64, color=GOLD_E).shift(DOWN * 2.3)
        self.say("让想买的等于想卖的：十减P，等于P。", Write(solve[0]))
        unit = zh("元 / 瓶", 30, GOLD_E).next_to(solve, RIGHT, buff=0.2)
        self.say("解出来P等于五，就是图上那个五块钱的交点。", Write(solve[1:]), FadeIn(unit))
        self.play(FadeOut(VGroup(fd_num, fs_num, solve, unit)), run_time=0.4)

        # ⑦ 回扣 + 学后追问
        self.gain_xp(1.0)  # 三点讲完，经验条满（无状态栏的风格自动跳过）
        pair = VGroup(stick_figure("wave", "happy", height=1.4), bottle(height=0.8),
                      stick_figure("wave", "happy", height=1.4)).arrange(RIGHT, buff=0.5).shift(UP * 1.6)
        end = zh("价格，是买卖双方拉扯出来的", 44, GOLD_E).shift(DOWN * 0.3)
        self.say("一句话：价格，是买的人和卖的人一起拉扯出来的。", FadeIn(pair), Write(end))
        ask = zh("哪一个画面，你最不确定？", 34).next_to(end, DOWN, buff=0.6)
        self.say("看完想一想：哪一个画面，你最不确定？", FadeIn(ask, shift=UP))
        self.wait(0.8)
