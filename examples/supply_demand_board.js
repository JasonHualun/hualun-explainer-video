// 示范分镜（白板马克笔风）：供需（通用知识讲解，非逐页原文蒸馏）。
// 板书式：标题在左上角；左边 graph() 画图讲原理，右边 note() 一行行记笔记；同一张图跨板块接着用。
// 位置尽量交给自动排版（graph / note / formula / note_on / center），只有简笔画小剧场才写坐标。
// 渲染：复制到集目录改名 分镜.js，bash scripts/render_board.sh <集目录>/分镜.js --draft
module.exports = (b) => {
  const { text, line, arrow, dash, curve, ellipse, circleAround, stick, bottle, mountain, graph, note, formula, note_on, center } = b;

  // ⓪ 开场
  b.title("这节课我们来讲供需，也就是，价格到底是怎么定出来的。", "供需：价格怎么定",
    ["买的人：需求", "卖的人：供给", "价格怎么定：均衡"],
    ["我们分三点来讲。第一点，先讲买的人，也就是需求。", "第二点，讲卖的人，也就是供给。",
      "第三点，把两边放在一起，看价格是怎么定下来的。"]);

  // ① 困惑：同一瓶水，山脚 2 元，山顶 10 元（小剧场，手写坐标）
  b.say("暑假去爬山，山脚下一瓶水，卖两块钱。", mountain(640, 590, 640, 420), bottle(300, 590, 60),
    text("2 元", 270, 470, { size: 32, color: "red" }));
  b.say("爬到山顶，同样一瓶水，卖十块。", bottle(700, 200, 50), text("10 元", 740, 130, { size: 36, color: "red" }),
    stick(560, 300, 90, { mood: "surprised", pose: "shrug" }));
  const q = text("为什么差了五倍？", 860, 300, { size: 40, color: "red" });
  b.say("水还是那瓶水，价格为什么差了五倍？", q, circleAround(q, { color: "red" }));

  // ② 需求
  const ax = graph();
  b.section("好，我们先来看第一点，买的人。", 1, "买的人：需求", ax);
  const bottles = n => (x, y) => b.group(...[...Array(n)].map((_, i) => bottle(x + 20 + i * 36, y + 56, 46)));
  b.say("先看买的人。东西越贵，想买的人就越少。", note("便宜 → 买 3 瓶", { color: "blue" }),
    note("", { doodle: bottles(3) }));
  b.say("贵了，只买一瓶，甚至干脆不买。", note("贵了 → 只买 1 瓶", { color: "red" }),
    note("", { doodle: (x, y) => stick(x + 40, y + 110, 110, { mood: "sad" }) }));
  b.say("画出来，就是一条往下走的线，叫需求曲线。",
    curve([ax.p(1, 9.2), ax.p(4, 6.1), ax.p(7, 3), ax.p(9.3, 0.8)], { color: "blue", w: 4 }),
    text("需求", ...ax.p(8.4, 2.4), { size: 28, color: "blue" }));

  // ③ 供给（图留着，只擦右边笔记）
  b.eraseNotes();
  b.section("第二点，卖的人。", 2, "卖的人：供给", { keep: true });
  b.say("卖的人正好反过来，价格越高，愿意卖的就越多。",
    note("", { doodle: (x, y) => stick(x + 40, y + 110, 110, { pose: "cheer" }) }),
    note("贵 → 多卖", { color: "red" }), note("便宜 → 少卖", { color: "gray" }));
  b.say("画出来，是一条往上走的线，叫供给曲线。",
    curve([ax.p(0.8, 0.8), ax.p(4, 4.1), ax.p(7, 7), ax.p(9.3, 9.2)], { color: "red", w: 4 }),
    text("供给", ...ax.p(8.6, 9.6), { size: 28, color: "red" }));

  // ④ 均衡
  b.eraseNotes();
  b.section("第三点，把两条线放在一起。", 3, "价格怎么定：均衡", { keep: true });
  const [ex, ey] = ax.p(5, 5), [ox, oy] = ax.p(0, 0), [, hy] = ax.p(0, 8), [, ly] = ax.p(0, 2), [rx] = ax.p(10, 0);
  b.say("两条线相交的地方，想买的和想卖的正好一样多。", ellipse(ex, ey, 16, 16, { color: "red" }),
    dash(ex, ey, ex, oy, { color: "red" }), dash(ex, ey, ox, ey, { color: "red" }));
  b.say("这一点的价格，就叫均衡价格。", note("均衡价格：两条线的交点", { color: "red" }));
  b.say("价格定高了，东西卖不掉，价格就会降。", dash(ox, hy, rx, hy, { color: "gray" }),
    note("定高了 → 卖不掉 → 降价", { color: "gray" }));
  b.say("价格定低了，东西不够卖，价格就会涨。", dash(ox, ly, rx, ly, { color: "green" }),
    note("定低了 → 不够卖 → 涨价", { color: "green" }));

  // ⑤ 回到山顶：供给变少，供给线左移
  b.eraseNotes();
  b.say("回到山顶。水要人一箱箱背上去，愿意卖的人少了。",
    note("", { doodle: (x, y) => b.group(mountain(x + 200, y + 260, 360, 250), stick(x + 140, y + 130, 80, { pose: "carry", mood: "sad" })) }),
    note("背上山 → 卖的人少"));
  const [nx, ny] = ax.p(3.5, 6.5);
  b.say("供给线整体往左挪，交点就跟着升高了。", curve([ax.p(0.3, 3.2), ax.p(3.5, 6.5), ax.p(6.3, 9.4)], { color: "red", w: 4 }),
    ellipse(nx, ny, 16, 16, { color: "red" }), arrow(ex - 6, ey - 20, nx + 8, ny + 22, { color: "red" }));
  b.say("所以山顶的水贵，主要不是商家黑心，而是供给变少了。", note("供给少 → 价格高", { size: 34, color: "red" }));

  // ⑥ 公式：每个字母都标清楚代表什么
  b.erase();
  const fd = formula("Q_{d} = [a] - [b] · P", 160, 140, { color: "blue" });
  b.say("用公式写，也是同一件事。先看需求这一行。", fd);
  b.say("a是价格为零时，最多想要几瓶，这里是十瓶。", note_on(fd.parts.a, "价格为 0 时最多要几瓶：10", { color: "blue" }));
  b.say("b是每贵一块钱，少买几瓶，这里是一瓶。", note_on(fd.parts.b, "每贵 1 元少买几瓶：1", { color: "blue", dx: 160, dy: 60 }));
  b.erase({ x0: 30, y0: 205, x1: 1250, y1: 470 });
  b.say("代进数字，需求就是：Q等于十减P。", formula("Q_{d} = 10 - P", 160, 300, { size: 52, color: "blue" }));
  b.say("供给同理，这里简单点：Q等于P。", formula("Q_{s} = P", 160, 400, { size: 52, color: "red" }));
  b.say("让想买的等于想卖的：十减P，等于P。", arrow(520, 380, 610, 370, { color: "gray" }), formula("10 - P = P", 640, 340, { size: 52 }));
  const ans = formula("P = 5", 700, 460, { color: "red" });
  b.say("所以P等于五，正好是图上那个交点。", ans, circleAround(ans, { color: "red" }));

  // ⑦ 回扣
  b.erase("all");
  b.say("一句话：价格，是买的人和卖的人一起拉扯出来的。", stick(430, 420, 130, { pose: "cheer" }), stick(850, 420, 130, { pose: "cheer" }),
    line(470, 330, 810, 330, { w: 4, color: "gray" }), bottle(640, 320, 50), center("价格 = 买卖双方拉扯出来的", 480, { size: 44, color: "red" }));
  b.say("看完想一想：哪一个画面，你最不确定？", center("哪一个画面，你最不确定？", 560, { size: 32, color: "gray" }));
};
