// ============================================================
// explainer.js — `retro diff` が出す video/data.json から 5 場面の振り返り動画を描く。
//
// 場面: 1 到達点  2 メダル圏ごとの段の階段  3 構成要素の行列  4 差分の上位 3  5 次に試すもの。
// すべて時刻 t だけから描く（乱数なし）ので、同じ data.json からは必ず同じ動画が出る。
// 画面の文言は T にまとめてあり、ここだけ直せば翻訳できる。
// ============================================================
(async () => {
  const A = window.Arch;
  const { W, H, THEME: C, MONO, seg, lerp, fadeIn, easeInOut, easeOut, g, el, txt, note, pill, box, dot, textWidth, wrap } = A;
  const D = await A.loadData();

  const T = {
    subtitle: `${D.name} — 自陣の数値は実測、他はすべて本人の申告`,
    s1: '自陣はどこで終わったか', s2: 'メダル圏ごとの private', s3: '誰が何を使ったか', s4: '最も効いた差', s5: '次に試すもの',
    measured: '実測', claimed: '申告', ours: '自陣', median: '中央値', single: '単一モデル', final: '最終',
    bands: { gold: '金', silver: '銀', bronze: '銅', none: '圏外', unknown: '圏 不明' },
    usedBy: '持っていた解法', verdict: { candidate: '境目の候補', 'frequency only': '頻度だけ', 'not a boundary': '境目でない', 'n/a': '記述が少なく判定不能' },
    sharedBy: '分析済みの上位解法に共通',
  };
  const bandColor = (b) => C[b] || C.none;
  const fmt = (x) => (x === null || x === undefined ? '' : String(+(+x).toFixed(4)));

  // ---- 派生データ ----
  const BAND_ORDER = ['gold', 'silver', 'bronze', 'none', 'unknown'];
  const bandsPresent = BAND_ORDER.filter((b) => (D.ladder.bands[b] || []).length || b === D.ladder.own_band);
  // 階段の列: 自陣の圏（左）から金（右）へ
  const ownIdx = BAND_ORDER.indexOf(D.ladder.own_band);
  const ladderBands = bandsPresent.filter((b) => ownIdx < 0 || BAND_ORDER.indexOf(b) <= ownIdx).reverse();
  const hib = D.higher_is_better !== false;
  const allScores = [];
  for (const b of ladderBands) for (const x of D.ladder.bands[b] || []) { allScores.push(+x.private); if (x.single !== null && x.single !== undefined) allScores.push(+x.single); }
  for (const v of [D.ladder.own_final, D.ladder.own_best, D.ladder.own_single]) if (v !== null && v !== undefined) allScores.push(+v);
  const sMin = Math.min(...allScores), sMax = Math.max(...allScores);
  const pad = (sMax - sMin || 0.01) * 0.15;
  const lo = sMin - pad, hi = sMax + pad;
  const PY0 = 760, PY1 = 200;
  const py = (v) => (hib ? lerp(PY0, PY1, (v - lo) / (hi - lo)) : lerp(PY1, PY0, (v - lo) / (hi - lo)));

  const cards = D.cards;
  const elements = D.elements.slice(0, 14);
  const gaps = D.gaps.slice(0, 3);
  const topCards = cards.filter((c) => c.rank !== null && c.rank <= D.top_n);

  // ---- 場面 1: 到達点 ----
  const S1 = (p, u) => {
    const a = fadeIn(u, 0.2);
    txt(`#${D.own_rank ?? '?'}`, { x: 80, y: 330, 'font-size': 150, 'font-weight': 900, 'font-family': MONO, fill: C.ours, opacity: a }, p);
    note(p, 80, 390, `${D.teams ?? '?'} チーム中`, { size: 30, alpha: fadeIn(u, 0.6), color: C.fg });
    pill(p, 230, 440, T.bands[D.own_band] || D.own_band, bandColor(D.own_band), { size: 20, alpha: fadeIn(u, 1.0) });
    if (D.ladder.own_final !== null) note(p, 80, 520, `private ${fmt(D.ladder.own_final)}  (${T.measured})`, { size: 24, alpha: fadeIn(u, 1.4), color: C.fg, mono: true });
    if (D.ladder.own_best !== null && D.ladder.own_best !== D.ladder.own_final) {
      note(p, 80, 560, `選ばなかった最良 ${fmt(D.ladder.own_best)}`, { size: 20, alpha: fadeIn(u, 1.8), mono: true });
    }
    // メダル圏の帯
    if (D.cutoffs && D.teams) {
      const bx = 760, by = 300, bw = 740, bh = 46;
      const ab = fadeIn(u, 2.0, 0.8);
      const k = g({ opacity: ab }, p);
      const xr = (r) => bx + bw * Math.log(r) / Math.log(D.teams);   // 対数の目盛り: メダルは 1 位の近くに集まる
      note(k, bx, by - 24, '1 位', { size: 14 });
      note(k, bx + bw, by - 24, `${D.teams}`, { size: 14, anchor: 'end' });
      const segs = [['gold', 1, D.cutoffs.gold], ['silver', D.cutoffs.gold + 1, D.cutoffs.silver], ['bronze', D.cutoffs.silver + 1, D.cutoffs.bronze], ['none', D.cutoffs.bronze + 1, D.teams]];
      segs.forEach(([b, r0, r1]) => {
        if (r1 < r0) return;
        const x0 = xr(r0), x1 = xr(Math.min(D.teams, r1 + 1));
        el('rect', { x: x0, y: by, width: Math.max(2, x1 - x0), height: bh, fill: bandColor(b), opacity: b === 'none' ? 0.25 : 0.75 }, k);
        if (b !== 'none') note(k, x1 - 4, by + bh + 20, `≤${r1}`, { size: 13, anchor: 'end', color: bandColor(b), mono: true });
      });
      note(k, bx, by + bh + 50, 'メダル圏の境目はチーム数からの推定（同点で 1 位ずれることがある）', { size: 14 });
      if (D.own_rank) {
        const x = lerp(bx + bw, xr(D.own_rank), easeInOut(seg(u, 2.8, 4.0)));
        el('line', { x1: x, y1: by - 8, x2: x, y2: by + bh + 8, stroke: C.ours, 'stroke-width': 4 }, k);
        dot(k, x, by - 16, 8, C.ours);
        note(k, x, by - 32, T.ours, { size: 14, anchor: 'middle', color: C.ours, bold: true });
      }
    }
    note(p, 760, 480, `解法記事 ${cards.length} 件をカードに（うち上位 ${D.top_n} 位以内 ${topCards.length} 件）`, { size: 20, alpha: fadeIn(u, 4.4), color: C.fg });
  };

  // ---- 場面 2: 段の階段 ----
  const colX = (i) => 260 + i * ((W - 400) / Math.max(1, ladderBands.length - 1 || 1));
  const S2 = (p, u) => {
    const a0 = fadeIn(u, 0.1);
    el('line', { x1: 150, y1: PY0, x2: W - 100, y2: PY0, stroke: C.line, 'stroke-width': 1.5, opacity: a0 }, p);
    for (let i = 0; i <= 4; i++) {
      const v = lo + (hi - lo) * (i / 4);
      const y = py(v);
      el('line', { x1: 150, y1: y, x2: W - 100, y2: y, stroke: C.line, 'stroke-width': 1, 'stroke-dasharray': '3 6', opacity: 0.5 * a0 }, p);
      note(p, 140, y + 5, fmt(v), { size: 13, anchor: 'end', mono: true, alpha: a0 });
    }
    note(p, 150, 180, hib ? 'private（上ほど良い）' : 'private（小さいほど良い指標。上 = 良い に反転）', { size: 14, alpha: a0 });
    const medianPts = [];
    ladderBands.forEach((b, i) => {
      const x = colX(i);
      const at = 0.6 + i * 2.2;
      const a = fadeIn(u, at, 0.6);
      pill(p, x, PY0 + 40, T.bands[b], bandColor(b), { size: 16, alpha: a });
      const items = D.ladder.bands[b] || [];
      items.forEach((it, j) => {
        const k = fadeIn(u, at + 0.3 + j * 0.25, 0.5);
        const off = (j - (items.length - 1) / 2) * 40;
        if (it.single !== null && it.single !== undefined) {
          dot(p, x + off, py(+it.single), 7, bandColor(b), { alpha: 0.9 * k, ring: true });
          el('line', { x1: x + off, y1: py(+it.single), x2: x + off, y2: py(+it.private), stroke: bandColor(b), 'stroke-width': 2, opacity: 0.5 * k }, p);
        }
        dot(p, x + off, py(+it.private), 9, bandColor(b), { alpha: k });
        // 札を左右交互に置き、隣の点と重ならないようにする
        const left = j % 2 === 0;
        note(p, x + off + (left ? -14 : 14), py(+it.private) + 5, `${it.label} ${fmt(it.private)}`, { size: 12, anchor: left ? 'end' : 'start', mono: true, alpha: k, color: C.fg });
      });
      const m = D.ladder.medians[b];
      if (m !== null && m !== undefined && items.length) {
        const ak = fadeIn(u, at + 0.6 + items.length * 0.25, 0.5);
        const half = 30 + items.length * 20;
        el('line', { x1: x - half, y1: py(+m), x2: x + half, y2: py(+m), stroke: bandColor(b), 'stroke-width': 3, opacity: ak }, p);
        note(p, x, py(+m) - 24 - (items.length > 1 ? 10 : 0), `${T.median} ${fmt(m)} (${T.claimed})`, { size: 12, mono: true, anchor: 'middle', alpha: ak, color: bandColor(b) });
        medianPts.push([x, py(+m), at + 1.0 + items.length * 0.25]);
      }
      if (b === D.ladder.own_band) {
        const ox = x - (items.length ? 110 : 0);
        const own = D.ladder.own_final, single = D.ladder.own_single, best = D.ladder.own_best;
        if (single !== null && single !== undefined && own !== null) {
          const r = easeInOut(seg(u, at + 1.0, at + 2.0));
          dot(p, ox, py(+single), 9, C.ours, { ring: true, alpha: fadeIn(u, at + 0.5) });
          note(p, ox - 14, py(+single) + 5, `${T.single} ${fmt(single)}`, { size: 12, anchor: 'end', mono: true, color: C.ours, alpha: fadeIn(u, at + 0.5) });
          el('line', { x1: ox, y1: py(+single), x2: ox, y2: lerp(py(+single), py(+own), r), stroke: C.ours, 'stroke-width': 3, opacity: fadeIn(u, at + 1.0) }, p);
        }
        if (own !== null) {
          const ak = fadeIn(u, single !== null ? at + 1.8 : at + 0.5);
          dot(p, ox, py(+own), 11, C.ours, { alpha: ak });
          note(p, ox - 14, py(+own) + 5, `${T.ours} ${T.final} ${fmt(own)} (${T.measured})`, { size: 13, anchor: 'end', mono: true, color: C.ours, bold: true, alpha: ak });
        }
        if (best !== null && best !== undefined && own !== null && best !== own) {
          const ak = fadeIn(u, at + 2.2);
          dot(p, ox, py(+best), 7, C.ours, { ring: true, alpha: 0.7 * ak });
          note(p, ox - 14, py(+best) + 5, `選ばなかった最良 ${fmt(best)}`, { size: 11, anchor: 'end', mono: true, color: C.ours, alpha: 0.8 * ak });
        }
      }
    });
    // 圏の中央値をつなぐ階段
    for (let i = 1; i < medianPts.length; i++) {
      const [x0, y0, t0] = medianPts[i - 1], [x1, y1] = medianPts[i];
      const r = easeOut(seg(u, t0 + 0.4, t0 + 1.2));
      if (r <= 0) continue;
      const xm = lerp(x0, x1, Math.min(1, r * 2)), ym = r > 0.5 ? lerp(y0, y1, (r - 0.5) * 2) : y0;
      el('polyline', { points: `${x0},${y0} ${xm},${y0} ${xm},${ym}`, fill: 'none', stroke: C.fg, 'stroke-width': 2, 'stroke-dasharray': '6 5', opacity: 0.6 }, p);
    }
  };

  // ---- 場面 3: 行列 ----
  const S3 = (p, u) => {
    const labels = [...cards.map((c) => c.label), T.ours];
    const x0 = 420, y0 = 190, rowH = Math.min(38, 560 / Math.max(1, elements.length)), colW = Math.min(90, (W - 560 - x0) / labels.length);
    labels.forEach((lab, j) => {
      const x = x0 + j * colW + colW / 2;
      const isOwn = j === labels.length - 1;
      const c = isOwn ? C.ours : bandColor((cards[j] || {}).band);
      note(p, x, y0 - 14, lab, { size: 14, anchor: 'middle', color: c, bold: true, mono: true, alpha: fadeIn(u, 0.1 + j * 0.05) });
    });
    const ownX = x0 + (labels.length - 1) * colW;
    el('rect', { x: ownX, y: y0 - 34, width: colW, height: rowH * elements.length + 40, rx: 8, fill: C.ours, opacity: 0.08 * fadeIn(u, 0.3) }, p);
    note(p, x0 + labels.length * colW + 30, y0 - 14, `上位 ${D.top_n} 位での使用`, { size: 13, alpha: fadeIn(u, 0.3) });
    elements.forEach((e, i) => {
      const y = y0 + i * rowH;
      const at = 0.4 + i * 0.32;
      const a = fadeIn(u, at, 0.4);
      const isGap = e.own !== 'yes' && e.used_top > 0;
      note(p, x0 - 16, y + rowH / 2 + 5, e.name.length > 34 ? e.name.slice(0, 33) + '…' : e.name, { size: 15, anchor: 'end', color: isGap ? C.fg : C.dim, bold: isGap, alpha: a });
      labels.forEach((lab, j) => {
        const v = j === labels.length - 1 ? e.own : e.cells[lab];
        const x = x0 + j * colW + colW / 2;
        const k = fadeIn(u, at + 0.05 * j, 0.3);
        if (v === 'yes') dot(p, x, y + rowH / 2, 9, j === labels.length - 1 ? C.ours : C.good, { alpha: k });
        else if (v === 'no') el('line', { x1: x - 7, y1: y + rowH / 2, x2: x + 7, y2: y + rowH / 2, stroke: C.grey, 'stroke-width': 2.5, opacity: k }, p);
        else note(p, x, y + rowH / 2 + 5, '?', { size: 15, anchor: 'middle', color: C.grey, mono: true, alpha: k });
      });
      note(p, x0 + labels.length * colW + 30, y + rowH / 2 + 5, `${e.used_top} / ${e.known_top}`, { size: 14, mono: true, alpha: a, color: isGap ? C.warn : C.dim });
      if (isGap) el('rect', { x: x0 - 400, y: y + 2, width: 400 + labels.length * colW + 120, height: rowH - 4, rx: 6, fill: C.warn, opacity: 0.07 * fadeIn(u, at + 0.8, 0.6) }, p);
    });
    if (D.elements.length > elements.length) note(p, x0 - 16, y0 + elements.length * rowH + 24, `… 残り ${D.elements.length - elements.length} 件は diff.md`, { size: 13, anchor: 'end' });
    const legY = 820;
    dot(p, 90, legY, 8, C.good); note(p, 106, legY + 5, '使った', { size: 14 });
    el('line', { x1: 170, y1: legY, x2: 184, y2: legY, stroke: C.grey, 'stroke-width': 2.5 }, p); note(p, 194, legY + 5, '使っていない', { size: 14 });
    note(p, 300, legY + 5, '?', { size: 15, color: C.grey, mono: true }); note(p, 316, legY + 5, '本文に無い（「使っていない」には数えない）', { size: 14 });
  };

  // ---- 場面 4: 差分の上位 ----
  const S4 = (p, u) => {
    const n = Math.max(1, gaps.length);
    const cw = Math.min(460, (W - 160 - (n - 1) * 30) / n), ch = 540;
    gaps.forEach((e, i) => {
      const x = 80 + i * (cw + 30), y = 180;
      const at = 0.3 + i * 2.6;
      const a = fadeIn(u, at, 0.6);
      const k = g({ transform: `translate(${x},${y})`, opacity: a }, p);
      el('rect', { x: 0, y: 0, width: cw, height: ch, rx: 14, fill: C.panel, stroke: C.warn, 'stroke-width': 2 }, k);
      txt(`${i + 1}`, { x: 24, y: 58, 'font-size': 40, 'font-weight': 900, 'font-family': MONO, fill: C.warn }, k);
      wrap(e.name, cw - 100, 24, 700).slice(0, 2).forEach((ln, li) => txt(ln, { x: 70, y: 48 + li * 30, 'font-size': 24, 'font-weight': 700 }, k));
      pill(k, 70 + textWidth(e.dimension, 13, 700) / 2 + 15, 112, e.dimension, C.accent, { size: 13 });
      const usedBy = cards.filter((c) => e.cells[c.label] === 'yes').map((c) => c.label);
      note(k, 24, 160, `${T.usedBy}: ${usedBy.join('  ')}`, { size: 16, color: C.fg, mono: true });
      // 圏ごとの使用率の小さな表
      let yy = 196;
      bandsPresent.forEach((b) => {
        const bu = e.band_usage[b];
        if (!bu || !(bu.known + bu.unknown)) return;
        note(k, 24, yy + 14, T.bands[b], { size: 14, color: bandColor(b), bold: true });
        A.hbar(k, 110, yy, cw - 230, 14, bu.known ? bu.used / bu.known : 0, bandColor(b), { alpha: fadeIn(u, at + 0.6) });
        note(k, cw - 110, yy + 12, `${bu.used}/${bu.known}${bu.unknown ? ` ?${bu.unknown}` : ''}`, { size: 13, mono: true });
        yy += 26;
      });
      wrap(`${T.ours}: ${e.own === 'no' ? '使っていない' : '記録なし'}${e.own_effect ? ' — ' + e.own_effect : ''}`, cw - 48, 15).slice(0, 2)
        .forEach((ln) => { note(k, 24, yy + 24, ln, { size: 15, color: C.ours }); yy += 20; });
      yy += 36;
      note(k, 24, yy, `${T.claimed}（本人の ablation。解法ごと）:`, { size: 14 });
      yy += 24;
      const claims = e.effects.length ? e.effects.map((x) => `${x.label}: ${x.effect}`) : ['— 申告なし —'];
      claims.slice(0, 4).forEach((s) => {
        wrap(s, cw - 48, 15).slice(0, 2).forEach((ln) => { note(k, 24, yy, ln, { size: 15, color: C.fg, alpha: fadeIn(u, at + 1.0) }); yy += 22; });
      });
      const vc = e.verdict === 'candidate' ? C.good : e.verdict === 'frequency only' ? C.warn : C.dim;
      pill(k, cw / 2, ch - 34, T.verdict[e.verdict] || e.verdict, vc, { size: 15, alpha: fadeIn(u, at + 1.6) });
    });
    if (!gaps.length) note(p, W / 2, 400, '差分なし: 上位が使った要素はすべて自陣にもある', { size: 24, anchor: 'middle', color: C.fg });
  };

  // ---- 場面 5: 締め ----
  const S5 = (p, u) => {
    gaps.forEach((e, i) => {
      const a = fadeIn(u, 0.6 + i * 0.7);
      txt(`${i + 1}.`, { x: 160, y: 300 + i * 90, 'font-size': 40, 'font-weight': 900, 'font-family': MONO, fill: C.warn, opacity: a }, p);
      txt(e.name, { x: 240, y: 300 + i * 90, 'font-size': 34, 'font-weight': 700, opacity: a }, p);
      note(p, 240, 332 + i * 90, `${e.dimension} · ${T.usedBy} ${cards.filter((c) => e.cells[c.label] === 'yes').map((c) => c.label).join(' ')} · ${T.verdict[e.verdict] || e.verdict}`, { size: 16, alpha: a });
    });
    if (D.shared && D.shared.length) {
      const a = fadeIn(u, 0.6 + gaps.length * 0.7 + 0.4);
      note(p, 160, 640, `${T.sharedBy}: ${D.shared.join(', ')}`, { size: 18, alpha: a, color: C.fg });
    }
    note(p, W / 2, 760, '出典: diff.md（retro diff）・solutions/ のカード・own/final.md、own/pipeline.md', { size: 14, anchor: 'middle', alpha: fadeIn(u, 2.5) });
  };

  const bandCaps = ladderBands.map((b, i) => [0.6 + i * 2.2, b === D.ladder.own_band
    ? `${T.bands[b]}: 自陣の位置 — 単一モデルから最終の合成へ`
    : `${T.bands[b]}: 点は各解法の申告した private`]);
  const matrixDur = 2.5 + elements.length * 0.32 + 2.5;

  A.defineShow({
    subtitle: T.subtitle,
    fps: 24,
    poster: { scene: 'ladder', at: Math.min(2.2 * ladderBands.length + 1.5, 14) },
    stations: [['1 到達点', C.ours], ['2 階段', C.accent], ['3 行列', C.good], ['4 差分', C.warn], ['5 次', C.violet]],
    scenes: [
      { id: 'result', station: 0, title: T.s1, dur: 9, draw: S1, caps: [[0, `自陣は ${D.teams ?? '?'} チーム中 ${D.own_rank ?? '?'} 位（${T.bands[D.own_band] || D.own_band}）`], [4.4, `上位の解法記事 ${cards.length} 件を、自陣と同じ 9 次元のカードに写した`]] },
      { id: 'ladder', station: 1, title: T.s2, dur: 2.2 * ladderBands.length + 4, draw: S2, caps: [...bandCaps, [2.2 * ladderBands.length + 0.6, '破線の階段は、圏ごとの申告の中央値をつなぐ']] },
      { id: 'matrix', station: 2, title: T.s3, dur: matrixDur, draw: S3, caps: [[0, '行は構成要素、列は解法、最後の列が自陣'], [matrixDur - 2.5, '光る行は、上の圏が使い、自陣に無いもの']] },
      { id: 'gaps', station: 3, title: T.s4, dur: 2.6 * Math.max(1, gaps.length) + 3, draw: S4, caps: [[0, '上の圏での使用率の順。申告は並べるだけで足さない'], [2.6 * Math.max(1, gaps.length), '境目の候補には、使用率の差と ablation の数値の両方が要る']] },
      { id: 'next', station: 4, title: T.s5, dur: 7, draw: S5, caps: [[0, '最初に試す構造の変更 3 つ。順番は提案']] },
    ],
  });
})();
