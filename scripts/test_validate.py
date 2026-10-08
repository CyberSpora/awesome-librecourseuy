"""Self-check for validate.py's entry selection. Run: uv run python scripts/test_validate.py"""

from __future__ import annotations

import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from models import ENTRIES_DIR, load_entry_files  # noqa: E402
from validate import select_network_entries  # noqa: E402


def _self_check() -> None:
    files = load_entry_files()
    assert files, "needs at least one entry to select from"
    first = next(iter(files))

    assert select_network_entries(files, None) == files, "no restriction selects every entry"
    assert select_network_entries(files, []) == {}, "an empty restriction selects none"

    relative = os.path.relpath(first)
    for spelling in (str(first), relative, os.path.join(".", relative)):
        assert list(select_network_entries(files, [spelling])) == [first], spelling

    try:
        select_network_entries(files, [str(ENTRIES_DIR / "missing.json")])
    except ValueError as exc:
        assert "missing.json" in str(exc), exc
    else:
        raise AssertionError("a path that is not an entry file must be rejected")
    print("validate self-check ok")


if __name__ == "__main__":
    _self_check()
