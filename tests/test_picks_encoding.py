"""
test_picks_encoding.py — Verify all generated picks files are valid UTF-8.
"""

from pathlib import Path

import pytest

PICKS_DIR = Path(__file__).parent.parent / "picks"


def _collect_picks_files():
    return list(PICKS_DIR.rglob("*.md"))


@pytest.mark.skipif(not PICKS_DIR.exists(), reason="picks/ directory not present")
def test_picks_dir_exists():
    assert PICKS_DIR.is_dir()


@pytest.mark.skipif(not any(PICKS_DIR.rglob("*.md")), reason="no picks files present")
def test_all_picks_files_are_valid_utf8():
    """Every *.md file under picks/ must decode cleanly as UTF-8."""
    failures = []
    for path in _collect_picks_files():
        try:
            path.read_bytes().decode("utf-8")
        except UnicodeDecodeError as exc:
            failures.append(f"{path.relative_to(PICKS_DIR)}: {exc}")
    assert not failures, "Non-UTF-8 picks files found:\n" + "\n".join(failures)


@pytest.mark.skipif(not any(PICKS_DIR.rglob("*.md")), reason="no picks files present")
def test_picks_files_have_table_header():
    """Every picks file should contain the standard table header row."""
    missing = []
    for path in _collect_picks_files():
        text = path.read_text(encoding="utf-8")
        if "| Rank |" not in text and "| Rank|" not in text:
            missing.append(str(path.relative_to(PICKS_DIR)))
    assert not missing, "Picks files missing table header:\n" + "\n".join(missing)
