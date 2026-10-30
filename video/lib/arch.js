// ============================================================
// arch.js — 再現できる解説動画のための、小さな SVG アニメーション部品。
//
// tools/render.mjs との約束: ページは `window.ARCH = { ready, duration, fps, posterTime, phases, render(t) }` を出す。
// `render(t)` は時刻 t（秒）のコマを毎回ゼロから描き、t 以外を使わない（Math.random() や Date.now() を使わない）。
// それが「同じコード + 同じデータ → 同じコマ」を保証し、後から直せる理由になる。
//
// このファイルは `window.Arch` に、部品（el, txt, pill, box, arrow, bar, dot, note）、イージング、
// 場面の一覧から ARCH を組み立てる `defineShow(spec)`、データ読み込み `loadData()` を置く。
// ============================================================
(() => {
  const NS = 'http://www.w3.org/2000/svg';
  const W = 1600, H = 900;
  const FONT = "'Noto Sans JP', 'Noto Sans', 'Segoe UI', 'Helvetica Neue', Arial, sans-serif";
  const MONO = "'JetBrains Mono', 'SFMono-Regular', Menlo, Consolas, monospace";
  const THEME = {
    bg: '#0b0d12', fg: '#e6edf3', dim: '#7d8590', grey: '#3a4452', panel: '#11161f', line: '#2b3442',
    gold: '#f5c242', silver: '#c0c7d1', bronze: '#d08a4b', none: '#5b6573', unknown: '#5b6573',
    ours: '#f472b6', accent: '#22d3ee', good: '#34d399', bad: '#f87171', warn: '#f59e0b', violet: '#a78bfa',
  };

  // ---- イージングと時間 ----
  const clamp = (x, a = 0, b = 1) => Math.min(b, Math.max(a, x));
  const seg = (t, a, b) => clamp((t - a) / (b - a));           // 時刻 a〜b の間を 0〜1 に
  const easeOut = (x) => 1 - Math.pow(1 - x, 3);
  const easeInOut = (x) => x * x * (3 - 2 * x);
  const lerp = (a, b, k) => a + (b - a) * k;
  const fadeIn = (u, at = 0, dur = 0.5) => easeOut(seg(u, at, at + dur));

  // ---- DOM の道具（すべて <svg id="stage"> に描く） ----
  let svg = null;
  const stage = () => svg || (svg = document.getElementById('stage'));
  const el = (tag, attrs = {}, parent = stage()) => {
    const e = document.createElementNS(NS, tag);
    for (const k in attrs) if (attrs[k] !== undefined && attrs[k] !== null) e.setAttribute(k, attrs[k]);
    parent.appendChild(e);
    return e;
  };
  const g = (attrs = {}, parent = stage()) => el('g', attrs, parent);
  const txt = (s, attrs = {}, parent = stage()) => {
    const e = el('text', { 'font-family': FONT, fill: THEME.fg, ...attrs }, parent);
    e.textContent = s;
    return e;
  };
  const textWidth = (s, size = 16, weight = 400, family = FONT) => {
    const e = txt(s, { x: -9999, y: -9999, 'font-size': size, 'font-weight': weight, 'font-family': family });
    const w = e.getComputedTextLength();
    e.remove();
    return w;
  };
  // 文字列を maxWidth に収まる行に折る（空白があれば単語ごと、無ければ文字ごと。日本語は文字ごと）
  const wrap = (s, maxWidth, size = 16, weight = 400) => {
    const words = /\s/.test(s) ? s.split(/\s+/) : Array.from(s);
    const joiner = /\s/.test(s) ? ' ' : '';
    const lines = [];
    let cur = '';
    for (const w of words) {
      const cand = cur ? cur + joiner + w : w;
      if (cur && textWidth(cand, size, weight) > maxWidth) { lines.push(cur); cur = w; } else cur = cand;
    }
    if (cur) lines.push(cur);
    return lines;
  };

  // ---- 部品 ----
  function pill(p, x, y, s, color, { active = true, size = 15, alpha = 1 } = {}) {
    const w = textWidth(s, size, 700) + 30;
    const k = g({ transform: `translate(${x},${y})`, opacity: alpha }, p);
    el('rect', { x: -w / 2, y: -16, width: w, height: 32, rx: 16, fill: color, opacity: active ? 0.22 : 0.05 }, k);
    el('rect', { x: -w / 2, y: -16, width: w, height: 32, rx: 16, fill: 'none', stroke: color, 'stroke-width': 1.5, opacity: active ? 1 : 0.3 }, k);
    txt(s, { x: 0, y: 6, 'font-size': size, 'font-weight': 700, fill: color, 'text-anchor': 'middle', opacity: active ? 1 : 0.45 }, k);
    return w;
  }
  function box(p, x, y, w, h, color, title = '', sub = null, { alpha = 1, fill = THEME.panel, size = 19 } = {}) {
    const k = g({ transform: `translate(${x},${y})`, opacity: alpha }, p);
    el('rect', { x: 0, y: 0, width: w, height: h, rx: 12, fill, stroke: color, 'stroke-width': 2 }, k);
    if (title) txt(title, { x: w / 2, y: sub ? h / 2 - 4 : h / 2 + 7, 'font-size': size, 'font-weight': 700, fill: color, 'text-anchor': 'middle' }, k);
    if (sub) txt(sub, { x: w / 2, y: h / 2 + 20, 'font-size': 14, fill: THEME.dim, 'text-anchor': 'middle' }, k);
    return k;
  }
  function arrow(p, x1, y1, x2, y2, color, { prog = 1, alpha = 1, width = 3, head = 6 } = {}) {
    if (prog <= 0) return;
    const xe = lerp(x1, x2, prog), ye = lerp(y1, y2, prog);
    el('line', { x1, y1, x2: xe, y2: ye, stroke: color, 'stroke-width': width, opacity: 0.6 * alpha }, p);
    el('circle', { cx: xe, cy: ye, r: head, fill: color, opacity: alpha }, p);
  }
  function note(p, x, y, s, { color = THEME.dim, size = 17, alpha = 1, anchor = 'start', bold = false, mono = false } = {}) {
    return txt(s, { x, y, 'font-size': size, fill: color, opacity: alpha, 'text-anchor': anchor, 'font-weight': bold ? 700 : 400, 'font-family': mono ? MONO : FONT }, p);
  }
  function dot(p, x, y, r, color, { alpha = 1, ring = false } = {}) {
    if (ring) el('circle', { cx: x, cy: y, r, fill: 'none', stroke: color, 'stroke-width': 2.5, opacity: alpha }, p);
    else el('circle', { cx: x, cy: y, r, fill: color, opacity: alpha }, p);
  }
  function bar(p, x, y, w, h, v, color, { alpha = 1, track = '#1a2130' } = {}) {
    el('rect', { x, y, width: w, height: h, rx: 3, fill: track, opacity: alpha }, p);
    el('rect', { x, y: y + h - h * clamp(v), width: w, height: h * clamp(v), rx: 3, fill: color, opacity: 0.85 * alpha }, p);
  }
  function hbar(p, x, y, w, h, v, color, { alpha = 1, track = '#1a2130' } = {}) {
    el('rect', { x, y, width: w, height: h, rx: 3, fill: track, opacity: alpha }, p);
    el('rect', { x, y, width: w * clamp(v), height: h, rx: 3, fill: color, opacity: 0.85 * alpha }, p);
  }
  // 画面下の字幕（1 文字ずつ現れる）
  function caption(p, s, u, { speed = 0.03, size = 30 } = {}) {
    const n = Math.floor(u / speed);
    txt(s.slice(0, n), { x: W / 2, y: H - 40, 'font-size': size, 'font-weight': 700, 'text-anchor': 'middle' }, p);
  }

  // ---- 場面の進行役 ----
  // spec = { subtitle, scenes: [{ id, title, dur, draw(p, u), caps: [[開始秒, 字幕], ...] }], fps, poster: {scene, at}, stations: [[札, 色], ...] }
  function defineShow(spec) {
    const scenes = spec.scenes;
    let acc = 0.6;
    scenes.forEach((s) => { s.t0 = acc; acc += s.dur; s.t1 = acc; });
    const END = acc + 0.4;
    const posterScene = scenes.find((s) => s.id === (spec.poster && spec.poster.scene)) || scenes[Math.min(1, scenes.length - 1)];
    const posterTime = posterScene.t0 + ((spec.poster && spec.poster.at) || Math.min(posterScene.dur - 0.5, 4));

    function render(t, opt = {}) {
      const root0 = stage();
      root0.innerHTML = '';
      el('rect', { x: 0, y: 0, width: W, height: H, fill: THEME.bg });
      const root = g({ opacity: seg(t, 0, 0.5) * (1 - seg(t, END - 0.5, END - 0.12)) });
      const sc = scenes.find((s) => t >= s.t0 && t < s.t1) || scenes[scenes.length - 1];
      const u = t - sc.t0;
      const inout = seg(u, 0, 0.4) * (1 - seg(u, sc.dur - 0.4, sc.dur));
      txt(sc.title, { x: 80, y: 80, 'font-size': 34, 'font-weight': 900, opacity: inout }, root);
      if (spec.subtitle) txt(spec.subtitle, { x: 80, y: 114, 'font-size': 17, fill: THEME.dim }, root);
      if (spec.stations) {
        let x = W - 80;
        [...spec.stations].reverse().forEach(([label, color], j) => {
          const i = spec.stations.length - 1 - j;
          const w = textWidth(label, 14, 700) + 30;
          pill(root, x - w / 2, 70, label, color, { active: sc.station === i || sc.station === -1, size: 14 });
          x -= w + 12;
        });
      }
      const body = g({ opacity: inout }, root);
      sc.draw(body, u, t);
      const cap = (sc.caps || []).filter((c) => u >= c[0]).pop();
      if (cap) caption(root, cap[1], u - cap[0]);
      if (opt.stamp) txt(`t=${t.toFixed(2)}s`, { x: W - 24, y: 36, fill: '#ff5577', 'font-family': MONO, 'font-size': 22, 'text-anchor': 'end' });
    }

    window.ARCH = {
      ready: false,
      duration: END,
      fps: spec.fps || 24,
      posterTime,
      render,
      phases: scenes.flatMap((s) => (s.caps || [[0, s.title]]).map((c, i, arr) => ({
        kind: 'stay', t0: s.t0 + c[0], t1: s.t0 + (arr[i + 1] ? arr[i + 1][0] : s.dur), caption: `[${s.id}] ${c[1]}`,
      }))),
    };
    const start = () => { render(0); window.ARCH.ready = true; };
    // Web フォントが読めない環境で fonts.ready が止まることがあるので 3 秒で諦めて進む
    Promise.race([document.fonts.ready, new Promise((r) => setTimeout(r, 3000))]).then(start);
    if (!location.search.includes('render')) {
      const t0 = performance.now();
      (function loop() { render(((performance.now() - t0) / 1000) % END); requestAnimationFrame(loop); })();
    }
    return window.ARCH;
  }

  // データ: tools/render.mjs が注入した window.RETRO_DATA か、ページと同じ場所の data.json（http で配信時）
  async function loadData() {
    if (window.RETRO_DATA) return window.RETRO_DATA;
    const q = new URLSearchParams(location.search).get('data');
    const url = q || 'data.json';
    const res = await fetch(url);
    if (!res.ok) throw new Error(`cannot load ${url}`);
    return res.json();
  }

  window.Arch = { W, H, FONT, MONO, THEME, clamp, seg, easeOut, easeInOut, lerp, fadeIn, el, g, txt, textWidth, wrap,
                  pill, box, arrow, note, dot, bar, hbar, caption, defineShow, loadData };
})();
