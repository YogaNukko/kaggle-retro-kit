"""video/tools/render.mjs（Node + Playwright + ffmpeg）を呼んで、コンペの解説動画を書き出す。"""

from __future__ import annotations

import os
import shutil
import subprocess
from pathlib import Path


def render(root: Path, comp_dir: Path, page: str | None, name: str | None, fps: int | None, gif: bool, sheet: bool) -> int:
    tool = root / "video" / "tools" / "render.mjs"
    if shutil.which("node") is None:
        print("[ERROR] node が無い（動画の段には Node.js 18 以上が要る）")
        return 1
    if not (root / "video" / "node_modules" / "playwright-core").exists() and not (root / "node_modules" / "playwright-core").exists():
        print("[hint] playwright-core が未インストール: video/ で `npm install`（初回のみ）")
    data = comp_dir / "video" / "data.json"
    page_path = Path(page) if page else root / "video" / "pages" / "explainer.html"
    if not page and not data.exists():
        print(f"[ERROR] {data} が無い — 先に `retro diff {comp_dir.name}`")
        return 1
    out_dir = comp_dir / "video" / "out"
    out_dir.mkdir(parents=True, exist_ok=True)
    env = dict(os.environ, RETRO_DATA=str(data.resolve()), RETRO_OUT=str(out_dir.resolve()))   # ページに渡すデータと出力先
    cmd = ["node", str(tool), "sheet" if sheet else "video", "--page", str(page_path), "--name", name or comp_dir.name]
    if fps:
        cmd += ["--fps", str(fps)]
    if gif:
        cmd += ["--gif"]
    print("$", " ".join(cmd))
    return subprocess.run(cmd, env=env, check=False).returncode
