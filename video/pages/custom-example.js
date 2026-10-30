// ============================================================
// custom-example.js — 手描きの場面の最小例。この 2 ファイルを写して、1 つの段の深掘り（例「上位はどう教師ラベルを作ったか」）を描き、
//   python retro.py video <slug> --page video/pages/custom-example.html --name my-scene
// で書き出す。約束: 場面の頭からの秒 `u` だけから描く。数値には必ず「実測」か「申告」を添える。
// ============================================================
(() => {
  const A = window.Arch;
  const { THEME: C, g, el, note, box, arrow, fadeIn, seg, easeInOut, lerp } = A;

  const flow = (p, u) => {
    const stages = ['入力', '前処理', '教師', 'モデル', '合成'];
    stages.forEach((s, i) => box(p, 120 + i * 290, 300, 230, 110, i === 2 ? C.warn : C.accent, s, null, { alpha: fadeIn(u, 0.2 + i * 0.3) }));
    for (let i = 0; i < stages.length - 1; i++) arrow(p, 350 + i * 290, 355, 410 + i * 290, 355, C.dim, { prog: seg(u, 0.6 + i * 0.3, 1.0 + i * 0.3) });
    // 1 件のデータがパイプラインを通っていく
    const k = easeInOut(seg(u, 2.0, 6.0));
    const x = lerp(120, 1280, k);
    el('circle', { cx: x, cy: 355, r: 14, fill: C.ours, opacity: fadeIn(u, 2.0) }, p);
    note(p, 235 + 2 * 290, 460, '上位: 画像を読む教師でラベルを作り直した（申告 +0.004）', { size: 18, color: C.warn, anchor: 'middle', alpha: fadeIn(u, 3.0) });
    note(p, 235 + 2 * 290, 490, '自陣: レポート由来のラベル（実測）', { size: 18, color: C.ours, anchor: 'middle', alpha: fadeIn(u, 3.6) });
  };

  A.defineShow({
    subtitle: '手描きの場面 — 1 つの例',
    scenes: [
      { id: 'flow', title: '教師の段だけが違う', dur: 8, draw: flow, caps: [[0, '1 件のデータが両方のパイプラインを通る'], [3.0, '違う箱は教師の段だけ']] },
    ],
  });
})();
