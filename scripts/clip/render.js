// 片段路线：按 plan.json 逐段打开花叔引擎的 clip.html，逐帧画 → 叠字幕 → ffmpeg，最后无损拼成无声画面。
// 用法：node render.js 工作目录
// 复用白板路线已装的 playwright-core + 无头 Chromium；引擎原件在 ~/Tools/apps/花伦动画引擎（不改它）。
const fs = require("fs"), path = require("path"), os = require("os"), http = require("http");
const { spawn } = require("child_process");

const ENGINE = process.env.HUASHU_ENGINE || path.join(os.homedir(), "Tools/apps/花伦动画引擎/scripts/engine");
const DEPS = process.env.WHITEBOARD_DEPS || path.join(os.homedir(), "Tools/envs/whiteboard-video");
const WORKERS = Number(process.env.CLIP_WORKERS || 3);
const MIME = { ".js": "text/javascript", ".html": "text/html", ".json": "application/json", ".woff": "font/woff",
  ".png": "image/png", ".jpg": "image/jpeg", ".jpeg": "image/jpeg", ".webp": "image/webp", ".svg": "image/svg+xml" };

function serve(allowed) {
  // 只服务引擎目录 + spec 里点名的图片（同 render.py 的做法）
  const srv = http.createServer((req, res) => {
    const u = decodeURIComponent(req.url.split("?")[0]);
    const f = u.startsWith("/__file__/") ? u.slice(9) : path.join(ENGINE, u);
    if ((u.startsWith("/__file__/") && !allowed.has(f)) || !f.startsWith(u.startsWith("/__file__/") ? "/" : ENGINE) || !fs.existsSync(f)) {
      res.writeHead(404); return res.end();
    }
    res.writeHead(200, { "Content-Type": MIME[path.extname(f)] || "application/octet-stream" });
    fs.createReadStream(f).pipe(res);
  });
  return new Promise(r => srv.listen(0, "127.0.0.1", () => r(srv)));
}

// 字幕：白字、黑描边、整句切入切出、不做动画（storytime 卡片的中文平台规矩），画在 safe.bottom 让出来的带子里
const SUB = `(c, text, W, H) => {
  if (!text) return;
  const ctx = c.getContext('2d'), size = Math.round(H * 0.044);
  ctx.save(); ctx.font = '700 ' + size + 'px "NotoSansSC-700", "PingFang SC", sans-serif';
  ctx.textAlign = 'center'; ctx.textBaseline = 'middle'; ctx.lineJoin = 'round';
  const maxW = W * 0.86, lines = [];
  let cur = '';
  for (const ch of text) { if (ctx.measureText(cur + ch).width > maxW) { lines.push(cur); cur = ch; } else cur += ch; }
  lines.push(cur);
  const y0 = H - H * 0.075 - (lines.length - 1) * size * 0.6;
  lines.forEach((l, i) => { const y = y0 + i * size * 1.2;
    ctx.lineWidth = size * 0.2; ctx.strokeStyle = 'rgba(0,0,0,0.85)'; ctx.strokeText(l, W / 2, y);
    ctx.fillStyle = '#fff'; ctx.fillText(l, W / 2, y); });
  ctx.restore();
}`;

async function renderSeg(browserExe, seg, k, plan, work) {
  const { chromium } = require(path.join(DEPS, "node_modules/playwright-core"));
  const spec = JSON.parse(fs.readFileSync(seg.spec, "utf8"));
  const allowed = new Set();
  for (const q of spec.cues || []) if (q.image && !/^(data:|https?:)/.test(q.image)) {
    const f = path.resolve(path.dirname(plan.sb || seg.spec), q.image);
    if (!fs.existsSync(f)) throw new Error("分镜里的图片不存在：" + q.image);
    allowed.add(f); q.image = "/__file__" + f;
  }
  const srv = await serve(allowed);
  const browser = await chromium.launch({ executablePath: browserExe, args: ["--disable-web-security", "--ignore-gpu-blocklist"] });
  const page = await browser.newPage({ viewport: { width: spec.width, height: spec.height }, deviceScaleFactor: 1 });
  const errors = [];
  page.on("console", m => { if (m.type() === "error") errors.push(m.text()); if (m.type() === "warning") console.log("  [引擎提示]", m.text()); });
  page.on("pageerror", e => errors.push(String(e)));
  await page.addInitScript(([s, env]) => { window.CLIP_SPEC = s; if (env) window.VO_ENV = env; }, [spec, seg.env]);
  await page.goto(`http://127.0.0.1:${srv.address().port}/clip.html?render=1`);
  await page.waitForFunction("window.__ready === true || !!window.__bootFailed", null, { timeout: 120000 });
  const bf = await page.evaluate("window.__bootFailed || null");
  if (bf) throw new Error(`第 ${k + 1} 段（${spec.grammar}）加载失败：\n${bf}`);
  const out = path.join(work, `seg${String(k).padStart(2, "0")}.mp4`);
  const ff = spawn("ffmpeg", ["-y", "-v", "error", "-f", "image2pipe", "-framerate", String(spec.fps), "-c:v", "png", "-i", "-",
    "-c:v", "libx264", "-pix_fmt", "yuv420p", "-crf", plan.fps === 15 ? "24" : "16", "-r", String(spec.fps), out], { stdio: ["pipe", "inherit", "inherit"] });
  const n = Math.round(spec.duration * spec.fps);
  for (let i = 0; i < n; i++) {
    const t = i / spec.fps, g = seg.t0 + t;
    const sub = (plan.subs.find(s => g >= s.t0 && g < s.t1 + 0.12) || {}).text || "";
    const b64 = await page.evaluate(async ([t, sub, W, H, SUB]) => {
      await window.prepare(t); window.renderFrame(t);
      (0, eval)(SUB)(window.__canvas, sub, W, H);
      return window.__canvas.toDataURL("image/png").split(",")[1];
    }, [t, sub, spec.width, spec.height, SUB]);
    if (!ff.stdin.write(Buffer.from(b64, "base64"))) await new Promise(r => ff.stdin.once("drain", r));
  }
  ff.stdin.end();
  await new Promise(r => ff.on("close", r));
  await browser.close(); srv.close();
  if (errors.length) throw new Error(`第 ${k + 1} 段（${spec.grammar}）页面报错：\n` + errors.join("\n"));
  console.log(`  第 ${k + 1} 段 ${spec.grammar} ${spec.duration}s ✓`);
  return out;
}

(async () => {
  const work = path.resolve(process.argv[2]);
  const plan = JSON.parse(fs.readFileSync(path.join(work, "plan.json"), "utf8"));
  plan.sb = process.env.CLIP_STORYBOARD;
  const cache = path.join(os.homedir(), "Library/Caches/ms-playwright");
  const exe = fs.readdirSync(cache).filter(d => d.startsWith("chromium_headless_shell")).sort().at(-1);
  const browserExe = path.join(cache, exe, "chrome-headless-shell-mac-arm64/chrome-headless-shell");
  const outs = new Array(plan.segments.length);
  let next = 0;
  await Promise.all([...Array(Math.min(WORKERS, plan.segments.length))].map(async () => {
    while (next < plan.segments.length) { const k = next++; outs[k] = await renderSeg(browserExe, plan.segments[k], k, plan, work); }
  }));
  const list = path.join(work, "segs.txt");
  fs.writeFileSync(list, outs.map(f => `file '${f}'`).join("\n"));
  await new Promise((res, rej) => spawn("ffmpeg", ["-y", "-v", "error", "-f", "concat", "-safe", "0", "-i", list, "-c", "copy",
    path.join(work, "silent.mp4")], { stdio: "inherit" }).on("close", c => (c ? rej(new Error("拼接失败")) : res())));
  outs.forEach(f => fs.unlinkSync(f));
})().catch(e => { console.error(e.message || e); process.exit(1); });
