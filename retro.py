#!/usr/bin/env python3
"""入口: `python retro.py <コマンド> ...`（`python retro.py -h` で一覧）。"""
import sys

from retrokit.cli import main

if __name__ == "__main__":
    sys.exit(main())
