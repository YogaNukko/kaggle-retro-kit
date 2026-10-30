"""retrokit — 終わった Kaggle コンペを、上位解法との差分分析と解説動画にする。

流れ（1 段 = 1 コマンド。対話的な質問はしない）:

    retro new <slug>        competitions/<slug>/ を雛形から作る
    retro fetch <slug>      LB と自分の提出一覧 → own/final.md（Kaggle CLI、読み取りのみ）
    retro collect <slug>    討論の解法記事 → tmp/<slug>/writeups/ と writeups_index.csv
    retro diff <slug>       カード × 自陣 → diff.md（階段・行列・圏ごとの使用率・差分の順位）と video/data.json
    retro video <slug>      data.json → MP4 / GIF / ポスター（Playwright + ffmpeg）
    retro lint <slug>       カード・自陣・レポートの形を検査する
"""

__version__ = "0.1.0"
