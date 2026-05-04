"""
log_change.py — Append a timestamped entry to PROJECT_LOG.md.

Usage
-----
    python scripts/log_change.py "message describing the change"
    python scripts/log_change.py "message" --commit abc1234
    python scripts/log_change.py "message" --files src/foo.py scripts/bar.py

Appended entry format:
    ## YYYY-MM-DD HH:MM  <message>
    - **Files:** ...
    - **Commit:** ... (if provided)
"""

from __future__ import annotations

import argparse
import sys
from datetime import datetime
from pathlib import Path

LOG_PATH = Path(__file__).parent.parent / "PROJECT_LOG.md"


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Append an entry to PROJECT_LOG.md.")
    p.add_argument("message", help="Short description of the change (1-2 sentences)")
    p.add_argument("--commit", default=None, help="Git commit hash")
    p.add_argument("--files", nargs="*", default=None, help="Files changed")
    return p.parse_args()


def append_entry(message: str, commit: str | None = None, files: list[str] | None = None) -> None:
    now = datetime.now().strftime("%Y-%m-%d %H:%M")
    lines = [f"\n## {now}  {message}\n"]
    if files:
        lines.append(f"- **Files:** {', '.join(f'`{f}`' for f in files)}\n")
    else:
        lines.append("- **Files:** (see commit diff)\n")
    if commit:
        lines.append(f"- **Commit:** `{commit}`\n")
    else:
        lines.append("- **Commit:** (uncommitted)\n")

    with open(LOG_PATH, "a", encoding="utf-8") as fh:
        fh.writelines(lines)
    print(f"Appended to {LOG_PATH.name}: {now}  {message}")


if __name__ == "__main__":
    args = parse_args()
    append_entry(args.message, commit=args.commit, files=args.files)
