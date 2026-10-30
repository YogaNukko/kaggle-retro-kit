# kaggle-retro-kit (English)

> The primary README, templates, skills and on-screen strings are in Japanese. Card headings and table columns are accepted in English too (`## Elements`, `Element | Dimension | Used | Effect | Evidence`), and the video strings live in one `T` object in `video/pages/explainer.js`. [日本語 README](README.md)

**Turn a finished Kaggle competition into a gap analysis against the medal bands — and a 50-second explainer video.**

You finished #102. The writeups are out. This kit answers, with numbers you can defend:
*what did the bands above me do that I did not, and which of those gaps actually separated the bands?*

![demo](docs/demo.gif)

*Synthetic example (`examples/sample-competition`). Every number on screen is labelled **measured** (ours) or **claimed** (theirs).*

## Five commands

```bash
python retro.py new     <slug> --name "<competition>"          # scaffold competitions/<slug>/
python retro.py fetch   <slug> --team "<your team>"             # leaderboard + your submissions -> own/final.md   (Kaggle CLI)
python retro.py collect <slug>                                  # discussion writeups -> index + bodies (repeatable)
#   ... write one card per writeup (templates/solution_card.md; Claude Code skill `retro-card` does it) ...
python retro.py diff    <slug>                                  # cards x your pipeline -> diff.md + video/data.json
python retro.py video   <slug> --gif                            # -> MP4, GIF, poster
```

No config files, no interactive prompts, no API keys beyond the Kaggle CLI's own `kaggle.json`.
Try it without any credentials:

```bash
python retro.py diff  examples/sample-competition
cd video && npm install && npx playwright-core install chromium && cd ..   # once; ffmpeg must be on PATH
python retro.py video examples/sample-competition --gif
```

## What you get

| file | what it is |
|---|---|
| `own/final.md` | rank, teams, best public / private, estimated medal band — **measured** |
| `solutions/<rank>-<team>.md` | one card per writeup: scores, an `Elements` table, nine pipeline dimensions, the author's claimed effects |
| `diff.md` | **ladder** (private score by band), **element matrix** (who used what, you last), **usage by band**, **ranked gaps** with a verdict |
| `video/out/<slug>.mp4` | five scenes: where you finished → ladder → matrix → top-3 gaps → what to try first |

The verdict column is the point of the kit:

| verdict | meaning |
|---|---|
| **boundary candidate** | used more in the bands above yours **and** at least one author reports an ablation number for it |
| frequency only | used more above you, but nobody measured it in isolation — a hint, not a cause |
| not a boundary | both sides use it about equally |

Three rules are enforced by the code, because they are the ones people break when they are tired:

1. "The writeup does not say" (`?`) is never counted as "not used".
2. Claims from different solutions are listed side by side, never added up.
3. Your numbers are the only *measured* ones; everything else is somebody's claim and is labelled so.

## How a card looks (the only format you need to learn)

```markdown
---
rank: 7
team: some-team
medal: gold
private: 0.9574
single_model_private: 0.9551      # optional: lets the ladder show single vs blend
url: https://www.kaggle.com/competitions/<slug>/discussion/<id>
---
## Elements
| Element | Dimension | Used | Effect | Evidence |
|---|---|---|---|---|
| image-read teacher labels | training | yes | CV +0.006 vs report labels | stated |
| pseudo-labels on test     | training | no  |                            | stated |
```

Use the same element names across cards and in `own/pipeline.md`; that is what makes the matrix line up.
Dimensions: `features preprocessing augmentation model training cv inference postprocessing ensemble`.
Your own `own/pipeline.md` has the same table; rows you *tried and dropped* get `Used = no` with the measured delta in `Effect`.

## The video engine

`video/` is a small, dependency-light renderer you can reuse for any explainer:

- `lib/arch.js` — SVG primitives (`box`, `arrow`, `dot`, `bar`, `pill`, `wrap`) and a scene runner. A page exposes
  `window.ARCH = { duration, fps, posterTime, render(t) }`; `render(t)` draws the frame for time *t* from scratch, so the output is
  deterministic (same data → same video).
- `tools/render.mjs` — Playwright screenshots → ffmpeg. `info`, `sheet N` (contact sheet), `frames t…`, `video` (MP4 / GIF / poster).
- `pages/explainer.html` — the built-in five-scene page driven by `data.json`. Strings are in one `T` object for translation.
- `pages/custom-example.html` — 40 lines showing how to hand-draw a deep-dive scene; render it with `retro video --page`.

Rendered media is git-ignored by default; attach it to a GitHub Release and link from your report.

## With Claude Code (optional)

`CLAUDE.md` and six skills in `.claude/skills/` drive the steps conversationally — "start the retrospective for `<slug>`",
"collect writeups", "read #7 and #21", "diff", "make the video", "lessons". They are written to **not** interview you:
the only facts the CLI cannot know (which two submissions you selected, your single-model score) default to the best private score
and are flagged. Card writing is parallelised one writeup per sub-agent.

## Requirements

| step | needs |
|---|---|
| `new` `diff` `lint` | Python 3.10+ (standard library only) |
| `fetch` `collect` | [Kaggle CLI](https://github.com/Kaggle/kaggle-api) 1.6+ with `~/.kaggle/kaggle.json` |
| `video` | Node 18+, `npm install` + `npx playwright-core install chromium` in `video/`, ffmpeg on PATH |

Development: `pip install -e .[dev] && ruff check retrokit tests && python -m pytest -q`.

## Layout

```
retro.py                 CLI entry (python retro.py -h)
retrokit/                medal cutoffs, writeup index, card parser, gap analysis, lint, scaffold
templates/               status, own/final, own/pipeline, solution card, report, lessons, article
video/                   lib/arch.js, tools/render.mjs, pages/explainer.*, pages/custom-example.*
competitions/<slug>/     your retrospectives (tracked)   tmp/<slug>/   fetched bodies (ignored)
examples/sample-competition/   synthetic, runs end to end
```

## FAQ

- **Medal cutoffs** are estimated from the team count with Kaggle's published rules; ties can move them by a place. Trust the leaderboard page.
- **Selected submissions** are not exposed by the Kaggle CLI; `fetch` uses your best private score and says so. Edit `private_final` in `own/final.md` if you selected a different one.
- **Lower-is-better metrics**: `fetch --lower-is-better` (stored as `higher_is_better: no`; the ladder flips its axis).
- **English cards**: headings and table columns may be written in English (see above); dimensions keep their English keys.

MIT © YogaNukko
