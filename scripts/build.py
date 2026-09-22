"""Regenerate README.md, public/entries.json and schema.json from entries/.

Pass --check to verify the committed files are current without writing. Pass
--verbose with --check to show a unified diff of each stale file.
"""

from __future__ import annotations

import argparse
import difflib
import json
import sys

from models import CATEGORIES, ROOT, TAGS, Entry, load_categories, load_entries

TEMPLATE = ROOT / "README.template.md"
README = ROOT / "README.md"
FEED = ROOT / "public" / "entries.json"
SCHEMA = ROOT / "schema.json"

BANNER = "<!-- GENERATED FILE - DO NOT EDIT. Edit README.template.md or entries/*.json. -->\n"
START, END = "<!-- PROJECTS:START -->", "<!-- PROJECTS:END -->"


def entry_line(entry: Entry) -> str:
    line = f"- [{entry.name}]({entry.url}): {entry.description}"
    if entry.maintainers:
        people = " · ".join(
            f"[{handle}](https://github.com/{handle.lstrip('@')})"
            for handle in entry.maintainers
        )
        line += f" ({people})"
    return line


def render_projects(entries: list[Entry], categories: list[str]) -> str:
    groups = {name: [] for name in categories}
    for entry in entries:
        groups[entry.category].append(entry)

    lines: list[str] = []
    for name in categories:
        group = sorted(groups[name], key=lambda e: e.name.lower())
        if not group:
            continue
        lines.append(f"### {name}\n")
        lines.extend(entry_line(e) for e in group)
        lines.append("")
    return "\n".join(lines).rstrip() or "_No entries yet._"


def render_readme(entries: list[Entry], categories: list[str]) -> str:
    template = TEMPLATE.read_text(encoding="utf-8")
    if START not in template or END not in template:
        raise SystemExit(f"README.template.md must contain {START} and {END}")
    head, rest = template.split(START, 1)
    _, tail = rest.split(END, 1)
    body = head + START + "\n" + render_projects(entries, categories) + "\n" + END + tail
    return BANNER + body.format(count=len(entries))


def render_feed(entries: list[Entry], categories: list[str]) -> str:
    return json.dumps(
        {
            "categories": categories,
            "entries": sorted(
                (e.model_dump(mode="json", exclude_none=True) for e in entries),
                key=lambda e: (e["category"], e["name"].lower()),
            ),
        },
        ensure_ascii=False,
        indent=2,
    ) + "\n"


def render_schema() -> dict:
    schema = Entry.model_json_schema()
    schema["properties"]["category"]["enum"] = CATEGORIES
    schema["properties"]["tags"]["items"]["enum"] = sorted(TAGS)
    return schema


def render_all() -> dict:
    """Render every generated file. Single source of truth for build and --check."""
    categories = load_categories()
    entries = load_entries()
    return {
        README: render_readme(entries, categories),
        FEED: render_feed(entries, categories),
        SCHEMA: json.dumps(render_schema(), indent=2, ensure_ascii=False) + "\n",
    }


def check_all(*, verbose: bool) -> int:
    stale: list[str] = []
    for path, rendered in render_all().items():
        current = path.read_text(encoding="utf-8") if path.exists() else ""
        if current == rendered:
            continue
        stale.append(str(path.relative_to(ROOT)))
        if verbose:
            diff = difflib.unified_diff(
                current.splitlines(),
                rendered.splitlines(),
                fromfile=f"{path.relative_to(ROOT)} (committed)",
                tofile=f"{path.relative_to(ROOT)} (regenerated)",
                lineterm="",
            )
            print("\n".join(diff))

    if stale:
        print(
            "stale generated files: run `uv run python scripts/build.py`: "
            + ", ".join(stale),
            file=sys.stderr,
        )
        return 1

    print("generated files are current")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--check",
        action="store_true",
        help="verify the generated files are current; write nothing",
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="with --check, show a unified diff of each stale file",
    )
    args = parser.parse_args()

    if args.check:
        return check_all(verbose=args.verbose)

    for path, rendered in render_all().items():
        path.parent.mkdir(exist_ok=True)
        path.write_text(rendered, encoding="utf-8")

    print(f"wrote {README.name}, {FEED.relative_to(ROOT)}, {SCHEMA.name}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
