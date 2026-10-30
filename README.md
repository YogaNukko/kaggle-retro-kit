# kaggle-retro-kit

**終わった Kaggle コンペを、メダル圏ごとの差分分析と 50 秒の解説動画にする。**

102 位で終わった。解法記事が出そろった。この道具が答えるのは、根拠を示せる数字で
「**上の圏は自分と何が違ったのか。そのうち圏を分けた要素はどれか**」。

![demo](docs/demo.gif)

*合成データの例（`examples/sample-competition`）。画面の数値はすべて **実測**（自陣）か **申告**（他）と書いてある。*

[English README](README.en.md)

## 5 つのコマンド

```bash
python retro.py new     <slug> --name "<コンペ名>"       # competitions/<slug>/ を雛形から作る
python retro.py fetch   <slug> --team "<チーム名>"        # LB と自分の提出 → own/final.md（Kaggle CLI、読み取りのみ）
python retro.py collect <slug>                            # 討論から解法記事を拾い、索引と本文を更新（何度でも）
#   ... 解法 1 件 = カード 1 枚を書く（templates/solution_card.md。Claude Code の skill `retro-card` が書く）...
python retro.py diff    <slug>                            # カード × 自陣 → diff.md + video/data.json
python retro.py video   <slug> --gif                      # → MP4 / GIF / ポスター
```

設定ファイルなし、対話的な質問なし、Kaggle CLI の `kaggle.json` 以外の鍵は要らない。認証なしで試すなら:

```bash
python retro.py diff  examples/sample-competition
cd video && npm install && npx playwright-core install chromium && cd ..   # 初回のみ。ffmpeg は PATH に
python retro.py video examples/sample-competition --gif
```

## 何が出るか

| ファイル | 中身 |
|---|---|
| `own/final.md` | 順位・チーム数・public / private の最良・推定メダル圏 — **実測** |
| `solutions/<順位>-<チーム>.md` | 解法カード: 点数、`構成要素` の表、9 次元、本人申告の効果 |
| `diff.md` | **段の階段**（圏ごとの private）、**構成要素 × 解法の行列**（自陣は最後の列）、**圏ごとの使用率**、**差分の順位**と判定 |
| `video/out/<slug>.mp4` | 5 場面: 到達点 → 階段 → 行列 → 差分の上位 3 → 次に試すもの |

判定の列がこの道具の要点:

| 判定 | 意味 |
|---|---|
| **境目の候補** | 自陣より上の圏で多く使われ、**かつ** 同じ解法の中の 1 変更の申告（ablation の数値）が 1 件以上ある |
| 頻度だけ | 上の圏で多いが、単独で測った人がいない。手掛かりであって原因ではない |
| 境目でない | 両方の圏が同じ程度に使う |

コードが守る 3 つの約束（疲れていると破りがちなもの）:

1. 「本文に無い」（`?`）を「使っていない」に数えない
2. 別々の解法の申告を足し合わせない（並べるだけ）
3. 実測は自陣の値だけ。他はすべて本人の申告として表示する

## カードの書式（覚えるのはこれだけ）

```markdown
---
rank: 7
team: some-team
medal: gold
private: 0.9574
single_model_private: 0.9551      # 任意。階段に「単一モデル → 合成」を出す
url: https://www.kaggle.com/competitions/<slug>/discussion/<id>
---
## 構成要素
| 要素 | 次元 | 使用 | 効果 | 根拠 |
|---|---|---|---|---|
| 画像を読む教師ラベル | training | yes | レポート由来より CV +0.006 | 本文に明記 |
| テストの疑似ラベル   | training | no  |                           | 本文に明記 |
```

要素名はカード同士と `own/pipeline.md` で揃える（行列が揃う条件）。次元は
`features preprocessing augmentation model training cv inference postprocessing ensemble` の 9 つ（日本語名も通る）。
自陣の `own/pipeline.md` も同じ表で、**試して落としたもの**は `使用 = no` にして「効果」に実測の差を書く。

## 動画エンジン

`video/` は、他の解説動画にも使い回せる小さな描画器:

- `lib/arch.js` — SVG の部品（`box` `arrow` `dot` `bar` `pill` `wrap`）と場面の進行役。ページは
  `window.ARCH = { duration, fps, posterTime, render(t) }` を出し、`render(t)` は時刻 t だけで 1 コマを描く（乱数・実時間なし → 同じデータから同じ動画）
- `tools/render.mjs` — Playwright で撮影 → ffmpeg。`info` / `sheet N`（一覧画像）/ `frames 秒…`（原寸コマ）/ `video`（MP4・GIF・ポスター）
- `pages/explainer.html` — `data.json` 駆動の 5 場面。文言は `T` に集約してあり、1 か所で翻訳できる
- `pages/custom-example.html` — 手描きの深掘り場面の最小例（40 行）。`retro video --page` で書き出す

書き出した動画は既定で git 管理外（GitHub Release などに添付して report.md からリンク）。

## Claude Code と使う（任意）

`CLAUDE.md` と `.claude/skills/` の 6 本が、「`<slug>` の振り返りを始めて」「解法を集めて」「7 位と 21 位を読んで」「差分を出して」「動画にして」「教訓」で各段を進める。
**聞き取りをしない設計**: CLI で分からないもの（選んだ 2 本・単一モデルの点）は private 最良で代用して明記する。カード作成は 1 記事 1 サブエージェントで並行する。

## 必要なもの

| 段 | 必要 |
|---|---|
| `new` `diff` `lint` | Python 3.10+（標準ライブラリのみ） |
| `fetch` `collect` | [Kaggle CLI](https://github.com/Kaggle/kaggle-api) 1.6+ と `~/.kaggle/kaggle.json` |
| `video` | Node 18+、`video/` で `npm install` と `npx playwright-core install chromium`、ffmpeg |

開発: `pip install -e .[dev] && ruff check retrokit tests && python -m pytest -q`

## 構成

```
retro.py                 入口（python retro.py -h）
retrokit/                メダル圏・解法記事の索引・カードの読み込み・差分の分析・検査・雛形
templates/               status / own/final / own/pipeline / 解法カード / report / lessons / article
video/                   lib/arch.js・tools/render.mjs・pages/explainer.*・pages/custom-example.*
competitions/<slug>/     振り返り（追跡）        tmp/<slug>/   取得した本文（管理外）
examples/sample-competition/   合成データ。end-to-end で動く
```

## よくある質問

- **メダル圏の境目**はチーム数から Kaggle の公開規則で推定する。同点で 1 位ずれることがある。LB のページを正とする
- **選んだ 2 本**は Kaggle CLI が返さない。`fetch` は private 最良を仮置きしてそう書く。別の提出を選んでいたら `own/final.md` の `private_final` を直す
- **小さいほど良い指標**: `fetch --lower-is-better`（`higher_is_better: no` として保存。階段の軸が反転する）
- **英語で書きたい**: カードの見出しと列名は英語（`## Elements` / `Element | Dimension | Used | Effect | Evidence`）でも読める。動画の文言は `video/pages/explainer.js` の `T`

MIT © YogaNukko
