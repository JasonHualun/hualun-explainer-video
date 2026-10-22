// 白板马克笔风的「板书引擎」：把分镜里的 text / line / stick … 变成一笔一笔的单线笔画。
// 中文用开源汉字笔画数据（hanzi-writer-data，按真实笔顺），英文数字标点用单线手写字体（Hershey · EMS Felix）。
// 坐标单位是像素，画面 1280×720；白板区域约 x 30–1250、y 20–622，下面那条深色条放字幕。
const fs = require("fs");
const path = require("path");

const DEPS = process.env.WHITEBOARD_DEPS || path.join(require("os").homedir(), "Tools/envs/whiteboard-video");
const HANZI = path.join(DEPS, "node_modules/hanzi-writer-data");
const FELIX = require(path.join(DEPS, "node_modules/hersheytext")).getFontData("ems_felix");

// 板面主题：WHITEBOARD_THEME=chalkboard 为黑板粉笔风（默认 whiteboard 白板马克笔风）。分镜里的颜色名不变，只换实际色值
const THEME = process.env.WHITEBOARD_THEME || "whiteboard";
const COLORS = THEME === "chalkboard"
  ? { ink: "#f2f0e6", blue: "#a9d3ec", red: "#f2b3b0", green: "#c2e3a8", gray: "#b8c4bc", orange: "#f3d496" }
  : { ink: "#1f2328", blue: "#2456c9", red: "#d23a3a", green: "#2e8b57", gray: "#6b7179", orange: "#e07a1f" };
const BOARD = { x0: 30, y0: 20, x1: 1250, y1: 622 };
const PUNCT = { "：": ":", "，": ",", "。": ".", "？": "?", "！": "!", "（": "(", "）": ")", "；": ";", "、": ",",
  "−": "-", "–": "-", "—": "-", "×": "x", "·": ".", "“": '"', "”": '"', "‘": "'", "’": "'" };

let seed = 7;
const rnd = () => (seed = (seed * 16807) % 2147483647) / 2147483647 - 0.5;
const col = c => COLORS[c] || c || COLORS.ink;
const f1 = v => Math.round(v * 10) / 10;

function smooth(pts) {  // 折线 → 经过各段中点的平滑曲线
  if (pts.length < 3) return "M" + pts.map(p => `${f1(p[0])} ${f1(p[1])}`).join(" L");
  let d = `M${f1(pts[0][0])} ${f1(pts[0][1])}`;
  for (let i = 1; i < pts.length - 1; i++)
    d += ` Q${f1(pts[i][0])} ${f1(pts[i][1])} ${f1((pts[i][0] + pts[i + 1][0]) / 2)} ${f1((pts[i][1] + pts[i + 1][1]) / 2)}`;
  const l = pts.at(-1);
  return d + ` L${f1(l[0])} ${f1(l[1])}`;
}

const cache = {};
function hanzi(ch) {
  if (!(ch in cache)) {
    const f = path.join(HANZI, ch + ".json");
    cache[ch] = fs.existsSync(f) ? JSON.parse(fs.readFileSync(f, "utf8")) : null;
  }
  return cache[ch];
}

// 一个「画出来的东西」：若干笔画 + 外框，能 .at() 取位置、能 .w/.h 取尺寸
class Drawn {
  constructor(strokes) {
    this.strokes = strokes;
    const xs = [], ys = [];
    for (const s of strokes) for (const [x, y] of s.pts || []) { xs.push(x); ys.push(y); }
    this.box = xs.length ? { x0: Math.min(...xs), y0: Math.min(...ys), x1: Math.max(...xs), y1: Math.max(...ys) } : { x0: 0, y0: 0, x1: 0, y1: 0 };
  }
  get w() { return this.box.x1 - this.box.x0; }
  get h() { return this.box.y1 - this.box.y0; }
  get left() { return this.box.x0; } get right() { return this.box.x1; }
  get top() { return this.box.y0; } get bottom() { return this.box.y1; }
  get cx() { return (this.box.x0 + this.box.x1) / 2; } get cy() { return (this.box.y0 + this.box.y1) / 2; }
}
const stroke = (pts, color, w, speed = 800, kind = "line") =>
  ({ d: smooth(pts), pts, color: col(color), w, speed, kind });

// ---------- 基本笔画 ----------
function text(str, x, y, o = {}) {
  // y 是这行字的顶边；支持 "Q_{d}" 下标、"x^{2}" 上标
  const size = o.size || 32, color = o.color || "ink", out = [];
  let cx = x;
  const runs = [];
  str.replace(/([_^])\{([^}]*)\}|([^_^]+|[_^])/g, (m, k, inner, plain) => runs.push(k ? { s: inner, k } : { s: plain }));
  for (const run of runs) {
    const sz = run.k ? size * 0.6 : size;
    const dy = run.k === "_" ? size * 0.45 : run.k === "^" ? -size * 0.1 : 0;
    for (const raw of run.s) {
      const ch = PUNCT[raw] || raw;
      const g = /[㐀-鿿]/.test(ch) && hanzi(ch);
      if (g) {
        const s = sz / 1024;
        for (const med of g.medians) {
          const pts = med.map(([px, py]) => [cx + px * s + rnd() * sz * 0.012, y + dy + (900 - py) * s + rnd() * sz * 0.012]);
          out.push(stroke(pts, color, sz * 0.085, 1100, "write"));
        }
        cx += sz * 1.02;
      } else if (ch === " ") {
        cx += sz * 0.35;
      } else {
        const g2 = FELIX.getChar ? FELIX.getChar(ch) : null;
        const s = sz / 1000 * 1.1, base = y + dy + sz * 0.86;
        if (g2 && g2.d) {
          for (const part of g2.d.split("M").filter(p => p.trim())) {
            const nums = part.replace(/L/g, " ").trim().split(/\s+/).map(Number);
            const pts = [];
            for (let i = 0; i + 1 < nums.length; i += 2) pts.push([cx + nums[i] * s, base - nums[i + 1] * s]);
            if (pts.length === 1) pts.push([pts[0][0] + 0.8, pts[0][1] + 0.8]);
            out.push({ d: "M" + pts.map(p => `${f1(p[0])} ${f1(p[1])}`).join(" L"), pts, color: col(color), w: sz * 0.075, speed: 1100, kind: "write" });
          }
          cx += (g2.width || 400) * s;
        } else {
          out.push({ font: raw, x: cx, y: y + dy, size: sz, color: col(color), pts: [[cx, y + dy], [cx + sz, y + dy + sz]], kind: "font" });
          cx += sz;
        }
      }
    }
  }
  const d = new Drawn(out);
  d.box = { x0: x, y0: y, x1: Math.max(cx, x), y1: y + size };  // 文字按行框计算，方便排版
  return d;
}

function line(x1, y1, x2, y2, o = {}) {
  const n = 6, pts = [];
  const bow = (o.bow ?? 1) * Math.min(6, Math.hypot(x2 - x1, y2 - y1) * 0.012) * (rnd() > 0 ? 1 : -1);
  const nx = -(y2 - y1), ny = x2 - x1, L = Math.hypot(nx, ny) || 1;
  for (let i = 0; i <= n; i++) {
    const t = i / n, b = Math.sin(t * Math.PI) * bow;
    pts.push([x1 + (x2 - x1) * t + nx / L * b + rnd() * 1.2, y1 + (y2 - y1) * t + ny / L * b + rnd() * 1.2]);
  }
  const out = [stroke(pts, o.color || "ink", o.w || 3)];
  if (o.arrow) out.push(...arrowHead(x2, y2, Math.atan2(y2 - y1, x2 - x1), o));
  return new Drawn(out);
}
function arrowHead(x, y, a, o) {
  const k = o.head || 14;
  return [stroke([[x - k * Math.cos(a - 0.45), y - k * Math.sin(a - 0.45)], [x, y], [x - k * Math.cos(a + 0.45), y - k * Math.sin(a + 0.45)]],
    o.color || "ink", o.w || 3, 500)];
}
const arrow = (x1, y1, x2, y2, o = {}) => line(x1, y1, x2, y2, { ...o, arrow: true });

function dash(x1, y1, x2, y2, o = {}) {
  const L = Math.hypot(x2 - x1, y2 - y1), n = Math.max(2, Math.round(L / 18)), out = [];
  for (let i = 0; i < n; i++) {
    const a = i / n, b = (i + 0.55) / n;
    out.push(stroke([[x1 + (x2 - x1) * a, y1 + (y2 - y1) * a], [x1 + (x2 - x1) * b, y1 + (y2 - y1) * b]], o.color || "ink", o.w || 2.5, 1600));
  }
  return new Drawn(out);
}

function curve(pts, o = {}) {  // 过一串点的手画曲线
  return new Drawn([stroke(pts.map(([x, y]) => [x + rnd() * 1.5, y + rnd() * 1.5]), o.color || "ink", o.w || 3.5, o.speed || 800)]);
}

function ellipse(cx, cy, rx, ry = rx, o = {}) {  // 手画圈：首尾略微交叠，不完全闭合
  const pts = [], a0 = -2.2 + rnd(), n = 28;
  for (let i = 0; i <= n + 2; i++) {
    const a = a0 + (i / n) * Math.PI * 2, r = 1 + rnd() * 0.04 + i * 0.002;
    pts.push([cx + rx * r * Math.cos(a), cy + ry * r * Math.sin(a)]);
  }
  return new Drawn([stroke(pts, o.color || "ink", o.w || 3, 900)]);
}
const circleAround = (d, o = {}) => ellipse(d.cx, d.cy, d.w / 2 + (o.pad ?? 14), d.h / 2 + (o.pad ?? 10), o);
const underline = (d, o = {}) => line(d.left - 4, d.bottom + (o.gap ?? 8), d.right + 8, d.bottom + (o.gap ?? 8) + 2, o);
function box(x, y, w, h, o = {}) {
  return new Drawn([...line(x, y, x + w, y, o).strokes, ...line(x + w, y, x + w, y + h, o).strokes,
    ...line(x + w, y + h, x, y + h, o).strokes, ...line(x, y + h, x, y, o).strokes]);
}
const group = (...ds) => new Drawn(ds.flatMap(d => d.strokes));

// ---------- 简笔画 ----------
function stick(x, y, h = 120, o = {}) {
  // (x, y) 是脚底中点；mood: happy / sad / surprised / neutral；pose: stand / cheer / shrug / carry
  const c = o.color || "ink", r = h * 0.13, hy = y - h + r, neck = hy + r, hip = y - h * 0.38;
  const out = [...ellipse(x, hy, r, r, { color: c, w: 3 }).strokes,
    ...line(x, neck, x, hip, { color: c, bow: 0.3 }).strokes];
  const pose = o.pose || "stand", ay = neck + h * 0.12, aw = h * 0.28;
  const arms = { stand: [[-aw, ay + h * 0.2], [aw, ay + h * 0.2]], cheer: [[-aw, ay - h * 0.25], [aw, ay - h * 0.25]],
    shrug: [[-aw, ay - h * 0.08], [aw, ay - h * 0.08]], carry: [[-aw * 0.6, ay - h * 0.2], [aw * 0.6, ay - h * 0.2]] }[pose];
  for (const [dx, yy] of arms) out.push(...line(x, ay, x + dx, yy, { color: c, bow: 0.3 }).strokes);
  out.push(...line(x, hip, x - h * 0.16, y, { color: c, bow: 0.3 }).strokes, ...line(x, hip, x + h * 0.16, y, { color: c, bow: 0.3 }).strokes);
  out.push(stroke([[x - r * 0.38, hy - r * 0.15], [x - r * 0.36, hy - r * 0.05]], c, 3, 400),
    stroke([[x + r * 0.38, hy - r * 0.15], [x + r * 0.36, hy - r * 0.05]], c, 3, 400));
  const m = o.mood || "happy", my = hy + r * 0.38, mw = r * 0.4;
  const mouth = { happy: [[x - mw, my - 2], [x, my + r * 0.18], [x + mw, my - 2]], sad: [[x - mw, my + 4], [x, my - r * 0.1], [x + mw, my + 4]],
    neutral: [[x - mw, my], [x + mw, my]], surprised: null }[m];
  out.push(...(mouth ? [stroke(mouth, c, 3, 400)] : ellipse(x, my, r * 0.14, r * 0.18, { color: c, w: 2.5 }).strokes));
  return new Drawn(out);
}
function bottle(x, y, h = 60, o = {}) {  // (x, y) 底部中点
  const w = h * 0.36, c = o.color || "blue";
  return group(line(x - w / 2, y, x - w / 2, y - h * 0.62, { color: c, bow: 0.2 }), line(x - w / 2, y - h * 0.62, x - w * 0.2, y - h * 0.82, { color: c }),
    line(x - w * 0.2, y - h * 0.82, x - w * 0.2, y - h, { color: c }), line(x - w * 0.2, y - h, x + w * 0.2, y - h, { color: c }),
    line(x + w * 0.2, y - h, x + w * 0.2, y - h * 0.82, { color: c }), line(x + w * 0.2, y - h * 0.82, x + w / 2, y - h * 0.62, { color: c }),
    line(x + w / 2, y - h * 0.62, x + w / 2, y, { color: c, bow: 0.2 }), line(x + w / 2, y, x - w / 2, y, { color: c }));
}
function mountain(x, y, w, h, o = {}) {  // (x, y) 底边中点
  const c = o.color || "ink";
  return group(curve([[x - w / 2, y], [x - w * 0.2, y - h * 0.55], [x, y - h]], { color: c }),
    curve([[x, y - h], [x + w * 0.22, y - h * 0.5], [x + w / 2, y]], { color: c }),
    curve([[x - w * 0.12, y - h * 0.76], [x - w * 0.04, y - h * 0.7], [x + w * 0.03, y - h * 0.78], [x + w * 0.12, y - h * 0.74]], { color: c, w: 2.5 }));
}
function axes(x0, y0, w, h, o = {}) {
  // 原点 (x0, y0)；返回的对象带 .p(x, y) 把 0–10 的数值换成画面坐标
  const c = o.color || "gray";
  const d = group(arrow(x0, y0, x0, y0 - h, { color: c, bow: 0.3 }), arrow(x0, y0, x0 + w, y0, { color: c, bow: 0.3 }),
    ...(o.ylabel ? [text(o.ylabel, x0 - 20, y0 - h - 44, { size: 26, color: c })] : []),
    ...(o.xlabel ? [text(o.xlabel, x0 + w + 12, y0 - 14, { size: 26, color: c })] : []));
  const max = o.max || 10;
  d.p = (vx, vy) => [x0 + (vx / max) * (w - 20), y0 - (vy / max) * (h - 20)];
  return d;
}

module.exports = { text, line, arrow, dash, curve, ellipse, circleAround, underline, box, group, stick, bottle, mountain, axes,
  COLORS, BOARD, Drawn };
