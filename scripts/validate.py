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

from models import Entry, Org, load_categories, load_entry_files, load_org_files
from urls import org_ok, repository_ok, url_ok


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


def check_org_network(org: Org) -> list[str]:
    errors: list[str] = []
    ok, detail = url_ok(str(org.url))
    if not ok:
        errors.append(f"{org.name}: url not reachable ({detail})")
    ok, detail = org_ok(str(org.repository))
    if not ok:
        errors.append(f"{org.name}: organization check failed ({detail})")
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
        org_files = load_org_files()
    except ValueError as exc:
        print(f"invalid entry: {exc}", file=sys.stderr)
        return 1
    try:
        selected = {} if args.offline else select_network_entries(files, args.only)
    except ValueError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2

    entries = list(files.values())
    orgs = list(org_files.values())
    errors: list[str] = []
    # Orgs and projects are separate namespaces: an org and its flagship
    # project may share a name or a website.
    for group, label in ((orgs, "org"), (entries, "entry")):
        seen_name: dict[str, str] = {}
        seen_url: dict[str, str] = {}
        seen_repo: dict[str, str] = {}
        for item in group:
            if item.name.lower() in seen_name:
                errors.append(f"{item.name}: duplicate {label} name")
            seen_name[item.name.lower()] = item.name
            url = str(item.url)
            if url in seen_url:
                errors.append(f"{item.name}: duplicate {label} url {url}")
            seen_url[url] = item.name
            repo = str(item.repository)
            if repo in seen_repo:
                errors.append(f"{item.name}: duplicate {label} repository {repo}")
            seen_repo[repo] = item.name

    if selected:
        with ThreadPoolExecutor(max_workers=8) as pool:
            for result in pool.map(check_network, selected.values()):
                errors.extend(result)
    if orgs and not args.offline and args.only is None:
        with ThreadPoolExecutor(max_workers=4) as pool:
            for result in pool.map(check_org_network, orgs):
                errors.extend(result)

    if not entries:
        print("warning: no entries yet", file=sys.stderr)

    if errors:
        print("\n".join(errors), file=sys.stderr)
        return 1

    if args.offline:
        checked = "skipped"
    elif args.only is None:
        checked = f"all {len(selected)} entries, {len(orgs)} orgs"
    else:
        checked = ", ".join(path.name for path in selected) or "none selected"
    print(
        f"ok: {len(entries)} entries across {len(categories)} categories, "
        f"{len(orgs)} orgs; network checks: {checked}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
