// 白板风渲染：读分镜.js → 排时间（每句旁白的长度说了算）→ 无头浏览器逐帧截图 → 无声 mp4 + timeline.json
// 用法：node render.js says   <分镜.js> <输出 says.json>
//       node render.js render <分镜.js> <audio.json> <工作目录> [--draft]
const fs = require("fs");
const path = require("path");
const os = require("os");
const { spawn } = require("child_process");
const E = require("./engine");

const DEPS = process.env.WHITEBOARD_DEPS || path.join(os.homedir(), "Tools/envs/whiteboard-video");
const GAP = 0.15, ERASE = 0.7;
const HEAD = { x: 64, y: 34, size: 34 };

// ---------- 分镜接口：b.title / b.section / b.say / b.erase ----------
function storyboard(file) {
  const beats = [];
  let pendingErase = [];
  const flat = ds => ds.flat(Infinity).filter(Boolean).flatMap(d => d.strokes);
  const heading = (str) => {
    const t = E.text(str, HEAD.x, HEAD.y, { size: HEAD.size });
    return E.group(t, E.underline(t, { w: 3 })).strokes.map(s => ({ ...s, heading: true }));
  };
  const b = {
    ...E,
    say(text, ...ds) {
      beats.push({ say: text, strokes: flat(ds), erase: pendingErase });
      pendingErase = [];
    },
    // 下一句开头先擦：不传=擦正文留标题；"all"=全擦；{x0,y0,x1,y1}=只擦这一块
    erase(spec = "content") { pendingErase.push(spec); },
    title(text, topic, sections = [], lines = []) {
      beats.push({ say: text, strokes: heading(topic), erase: pendingErase }); pendingErase = [];
      let y = 140;
      sections.forEach((s, i) => {
        const strokes = E.text(`${i + 1}. ${s}`, 110, y, { size: 30 }).strokes;
        if (lines[i]) beats.push({ say: lines[i], strokes });
        else beats.at(-1).strokes.push(...strokes);
        y += 56;
      });
      pendingErase = ["all"];
    },
    // 换板块：默认全擦后在左上角写新标题；{ keep: true } 只换标题、正文（如图表）留着接着用
    section(text, index, name, ...ds) {
      const opt = ds.length && !(ds[0] instanceof E.Drawn) && !Array.isArray(ds[0]) ? ds.shift() : {};
      beats.push({ say: text, strokes: [...heading(`${index}. ${name}`), ...flat(ds)],
        erase: [...pendingErase, opt.keep ? "heading" : "all"] });
      pendingErase = [];
    },
    headingBottom: HEAD.y + HEAD.size + 20,   // 正文从这条线以下开始写
    ...layout(),
  };
  delete require.cache[require.resolve(path.resolve(file))];
  require(path.resolve(file))(b);
  return beats;
}

// ---------- 自动排版：分镜只说「画什么」，位置由这里定 ----------
// 版面：左边 LEFT 画图讲原理，右边 RIGHT 写笔记、画简笔画
const LEFT = { x0: 60, y0: 100, x1: 740, y1: 600 }, RIGHT = { x0: 775, y0: 100, x1: 1240, y1: 600 };
function layout() {
  let ny = RIGHT.y0 + 10;
  const L = {
    LEFT, RIGHT,
    // 标准坐标图：占满左区，带 .p(x, y)（0–10）
    graph: (o = {}) => E.axes(LEFT.x0 + 90, LEFT.y1 - 40, LEFT.x1 - LEFT.x0 - 150, LEFT.y1 - LEFT.y0 - 80,
      { ylabel: "价格", xlabel: "数量", ...o }),
    // 右侧笔记：一行行往下记，不用算 y；可以带一个小图（{ doodle: (x, y) => … }，x/y 为这一行左上角）
    note(str, o = {}) {
      const size = o.size || 30, x = RIGHT.x0 + (o.indent || 0);
      const parts = [];
      let h = size;
      if (o.doodle) { const d = o.doodle(x, ny); parts.push(d); h = Math.max(h, d.bottom - ny); }
      if (str) parts.push(E.text(str, o.doodle ? x + (o.doodleW || 90) : x, ny + (h - size) / 2, { size, color: o.color }));
      ny += h + (o.gap ?? 26);
      return E.group(...parts);
    },
    noteSpace: (h = 30) => { ny += h; },
    // 擦右侧笔记区（下一句开头执行），笔记从头记
    eraseNotes() { this.erase(RIGHT); ny = RIGHT.y0 + 10; },
    // 公式：方括号里的部分单独拿出来，好标注，如 formula("Q_{d} = [a] - [b] · P") → f.parts.a
    formula(src, x, y, o = {}) {
      const size = o.size || 56, parts = {}, ds = [];
      let cx = x;
      for (const seg of src.split(/(\[[^\]]+\])/).filter(Boolean)) {
        const key = seg.startsWith("[") ? seg.slice(1, -1) : null;
        const t = E.text(key || seg, cx, y, { size, color: o.color });
        if (key) parts[key] = t;
        ds.push(t); cx = t.right;
      }
      const f = E.group(...ds); f.box = { x0: x, y0: y, x1: cx, y1: y + size }; f.parts = parts;
      return f;
    },
    // 给某一部分加注释：箭头从注释指过去，注释自动放在下方（或上方）错开
    note_on(part, str, o = {}) {
      const up = o.dir === "up", dx = o.dx || 0, size = o.size || 26;
      const ty = up ? part.top - 90 - size : part.bottom + 70 + (o.dy || 0);
      const t = E.text(str, part.cx - 40 + dx, ty, { size, color: o.color });
      const a = E.arrow(t.left + 40, up ? t.bottom + 6 : t.top - 6, part.cx, up ? part.top - 6 : part.bottom + 6, { color: o.color });
      return E.group(a, t);
    },
    // 一行字在白板上水平居中
    center: (str, y, o = {}) => { const t = E.text(str, 0, y, o); return E.text(str, 640 - t.w / 2, y, o); },
  };
  return L;
}

const plen = pts => pts.slice(1).reduce((a, p, i) => a + Math.hypot(p[0] - pts[i][0], p[1] - pts[i][1]), 0);

function schedule(beats, audio) {
  const strokes = [], subs = [], erases = [], clips = [];
  let T = 0.3, alive = [];
  beats.forEach((bt, i) => {
    const a = audio[i];
    const D = a.dur + GAP;
    let t = T;
    for (const spec of bt.erase || []) {
      const R = typeof spec === "object" ? spec
        : spec === "heading" ? { x0: 30, y0: 20, x1: 1250, y1: HEAD.y + HEAD.size + 24 } : { x0: 30, y0: 20, x1: 1250, y1: 622 };
      const hit = s => {
        if (spec === "all") return true;
        if (spec === "heading") return s.heading;
        if (spec === "content") return !s.heading;
        const x = (Math.min(...s.pts.map(p => p[0])) + Math.max(...s.pts.map(p => p[0]))) / 2;
        const y = (Math.min(...s.pts.map(p => p[1])) + Math.max(...s.pts.map(p => p[1]))) / 2;
        return x >= R.x0 && x <= R.x1 && y >= R.y0 && y <= R.y1;
      };
      const dur = ERASE * Math.max(0.5, (R.x1 - R.x0) / 1220);
      erases.push({ t, dur, ...R });
      alive = alive.filter(s => {
        if (!hit(s)) return true;
        const x = Math.min(...s.pts.map(p => p[0]));
        s.eraseAt = t + dur * Math.min(Math.max((x - R.x0) / Math.max(R.x1 - R.x0, 1), 0), 1);
        return false;
      });
      t += dur;
    }
    // 写字速度固定；赶不上这句话就整体加速（最多 2.5 倍），还不够才把这一拍拉长
    const cost = bt.strokes.map((s, j) => {
      const prev = bt.strokes[j - 1];
      const travel = prev ? Math.hypot(s.pts[0][0] - prev.pts.at(-1)[0], s.pts[0][1] - prev.pts.at(-1)[1]) : 0;
      const draw = s.font ? 0.25 : Math.max(0.03, plen(s.pts) / s.speed);
      const lift = j === 0 ? 0.35 : (s.kind === "write" && travel < 60 ? 0.025 : 0.06 + travel / 3000);
      return { draw, lift };
    });
    const natural = cost.reduce((x, c) => x + c.draw + c.lift, 0);
    const avail = Math.max(0.4, D * 0.88 - (t - T));
    const k = Math.min(2.5, Math.max(1, natural / avail));
    bt.strokes.forEach((s, j) => {
      t += cost[j].lift / k;
      s.t0 = t; t += cost[j].draw / k; s.t1 = t;
      strokes.push(s); alive.push(s);
    });
    const end = Math.max(T + D, t + 0.35);
    subs.push({ t: T, dur: end - T, text: bt.say });
    clips.push({ t: Math.round(T * 1000) / 1000, file: a.file });
    T = end;
  });
  return { strokes: strokes.map(({ pts, ...s }) => ({ ...s, pts: undefined, eraseAt: s.eraseAt ?? null })), subs, erases, clips,
    duration: T + 0.8 };
}

async function render(file, audioFile, work, draft) {
  const beats = storyboard(file);
  const audio = JSON.parse(fs.readFileSync(audioFile, "utf8"));
  const plan = schedule(beats, audio);
  const { chromium } = require(path.join(DEPS, "node_modules/playwright-core"));
  const cacheDir = path.join(os.homedir(), "Library/Caches/ms-playwright");
  const exe = fs.readdirSync(cacheDir).filter(d => d.startsWith("chromium_headless_shell")).sort().at(-1);
  const FPS = draft ? 15 : 30, n = Math.ceil(plan.duration * FPS);
  // 同时开几个浏览器分段截图，最后无损拼接（画面只由时间决定，分段互不影响）
  const W = Math.max(1, Math.min(Number(process.env.WHITEBOARD_WORKERS || 4), Math.ceil(n / FPS / 5)));
  const per = Math.ceil(n / W);
  let done = 0;
  const seg = async (k) => {
    const browser = await chromium.launch({ executablePath: path.join(cacheDir, exe, "chrome-headless-shell-mac-arm64/chrome-headless-shell") });
    const page = await browser.newPage({ viewport: { width: 1280, height: 720 }, deviceScaleFactor: draft ? 0.75 : 1.5 });
    await page.goto("file://" + path.join(__dirname, "page.html"));
    await page.evaluate(p => window.boot(p), plan);
    const out = path.join(work, `seg${k}.mp4`);
    const ff = spawn("ffmpeg", ["-y", "-v", "error", "-f", "image2pipe", "-framerate", String(FPS), "-i", "-",
      "-c:v", "libx264", "-pix_fmt", "yuv420p", "-crf", draft ? "26" : "18", "-r", String(FPS), out], { stdio: ["pipe", "inherit", "inherit"] });
    for (let i = k * per; i < Math.min(n, (k + 1) * per); i++) {
      await page.evaluate(t => window.render(t), i / FPS);
      const buf = await page.screenshot({ type: "jpeg", quality: draft ? 80 : 92 });
      if (!ff.stdin.write(buf)) await new Promise(r => ff.stdin.once("drain", r));
      if (++done % (FPS * 20) === 0) process.stdout.write(`  画面 ${Math.round(done / FPS)}/${Math.round(plan.duration)} 秒\r`);
    }
    ff.stdin.end();
    await new Promise(r => ff.on("close", r));
    await browser.close();
    return out;
  };
  const segs = await Promise.all([...Array(W).keys()].map(seg));
  const list = path.join(work, "segs.txt");
  fs.writeFileSync(list, segs.map(f => `file '${f}'`).join("\n"));
  await new Promise((res, rej) => spawn("ffmpeg", ["-y", "-v", "error", "-f", "concat", "-safe", "0", "-i", list, "-c", "copy",
    path.join(work, "silent.mp4")], { stdio: "inherit" }).on("close", c => (c ? rej(new Error("拼接失败")) : res())));
  segs.forEach(f => fs.unlinkSync(f));
  fs.writeFileSync(path.join(work, "timeline.json"), JSON.stringify({ duration: plan.duration, clips: plan.clips }));
}

const [mode, file, a2, a3, flag] = process.argv.slice(2);
if (mode === "says") fs.writeFileSync(a2, JSON.stringify(storyboard(file).map(b => b.say), null, 0));
else render(file, a2, a3, flag === "--draft").catch(e => { console.error(e); process.exit(1); });
