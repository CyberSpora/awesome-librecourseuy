"""Validate every entries/*.json. Exits non-zero when anything is wrong.

Schema and cross-file checks always cover every entry. The network checks (URL
liveness and repository verification) cover every entry too, unless --only
narrows them to the given files or --offline skips them.
"""

from __future__ import annotations

import argparse
import sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from models import Entry, load_categories, load_entry_files
from urls import repository_ok, url_ok


def select_network_entries(
    files: dict[Path, Entry], only: list[str] | None
) -> dict[Path, Entry]:
    """Pick the entries that get network checks: every one, or only the given files.

    Narrowing them to the files a pull request touches keeps a third-party site
    that is down from blocking unrelated changes.
    """
    if only is None:
        return dict(files)
    selected: dict[Path, Entry] = {}
    for raw in only:
        path = Path(raw).resolve()
        if path not in files:
            raise ValueError(f"{raw}: not an entry file (deleted, or outside entries/)")
        selected[path] = files[path]
    return selected


def check_network(entry: Entry) -> list[str]:
    errors: list[str] = []
    ok, detail = url_ok(str(entry.url))
    if not ok:
        errors.append(f"{entry.name}: url not reachable ({detail})")
    ok, detail = repository_ok(str(entry.repository), entry.license)
    if not ok:
        errors.append(f"{entry.name}: repository check failed ({detail})")
    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    network = parser.add_mutually_exclusive_group()
    network.add_argument(
        "--offline",
        action="store_true",
        help="skip the network checks (URL liveness and repository verification)",
    )
    network.add_argument(
        "--only",
        nargs="*",
        metavar="ENTRY",
        help="run the network checks only for these entry files; with no files, skip them",
    )
    args = parser.parse_args()

    categories = load_categories()
    try:
        files = load_entry_files()
    except ValueError as exc:
        print(f"invalid entry: {exc}", file=sys.stderr)
        return 1
    try:
        selected = {} if args.offline else select_network_entries(files, args.only)
    except ValueError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2

    entries = list(files.values())
    errors: list[str] = []
    seen_name: dict[str, str] = {}
    seen_url: dict[str, str] = {}
    seen_repo: dict[str, str] = {}

    for entry in entries:
        if entry.name.lower() in seen_name:
            errors.append(f"{entry.name}: duplicate name")
        seen_name[entry.name.lower()] = entry.name
        url = str(entry.url)
        if url in seen_url:
            errors.append(f"{entry.name}: duplicate url {url}")
        seen_url[url] = entry.name
        repo = str(entry.repository)
        if repo in seen_repo:
            errors.append(f"{entry.name}: duplicate repository {repo}")
        seen_repo[repo] = entry.name

    if selected:
        with ThreadPoolExecutor(max_workers=8) as pool:
            for result in pool.map(check_network, selected.values()):
                errors.extend(result)

    if not entries:
        print("warning: no entries yet", file=sys.stderr)

    if errors:
        print("\n".join(errors), file=sys.stderr)
        return 1

    if args.offline:
        checked = "skipped"
    elif args.only is None:
        checked = f"all {len(selected)} entries"
    else:
        checked = ", ".join(path.name for path in selected) or "none selected"
    print(
        f"ok: {len(entries)} entries across {len(categories)} categories; "
        f"network checks: {checked}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
