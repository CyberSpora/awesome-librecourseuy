"""Validate every entry/*.json. Exits non-zero on the first problem."""

from __future__ import annotations

import argparse
import sys
from concurrent.futures import ThreadPoolExecutor

from models import load_categories, load_entries
from urls import is_open_source, url_ok


def check_entry(entry, categories: set[str], *, online: bool) -> list[str]:
    errors: list[str] = []
    if entry.category not in categories:
        errors.append(f"{entry.name}: unknown category {entry.category!r}")
    if not online:
        return errors
    ok, detail = url_ok(str(entry.url))
    if not ok:
        errors.append(f"{entry.name}: url not reachable ({detail})")
    if entry.open_source and entry.repository:
        ok, detail = is_open_source(str(entry.repository), entry.license)
        if not ok:
            errors.append(f"{entry.name}: repository check failed ({detail})")
    return errors


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--offline",
        action="store_true",
        help="skip network checks (URL liveness and open-source verification)",
    )
    args = parser.parse_args()

    categories = set(load_categories())
    try:
        entries = load_entries()
    except ValueError as exc:
        print(f"invalid entry: {exc}", file=sys.stderr)
        return 1

    errors: list[str] = []
    seen_name: dict[str, str] = {}
    seen_url: dict[str, str] = {}

    for entry in entries:
        if entry.name.lower() in seen_name:
            errors.append(f"{entry.name}: duplicate name")
        seen_name[entry.name.lower()] = entry.name
        url = str(entry.url)
        if url in seen_url:
            errors.append(f"{entry.name}: duplicate url {url}")
        seen_url[url] = entry.name

    online = not args.offline
    if entries:
        with ThreadPoolExecutor(max_workers=8) as pool:
            results = pool.map(lambda e: check_entry(e, categories, online=online), entries)
            for result in results:
                errors.extend(result)

    if not entries:
        print("warning: no entries yet", file=sys.stderr)

    if errors:
        print("\n".join(errors), file=sys.stderr)
        return 1

    print(f"ok: {len(entries)} entries across {len(categories)} categories")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
