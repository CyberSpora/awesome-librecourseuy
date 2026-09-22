"""Self-check for scripts/build.py rendering. Run: uv run python scripts/test_build.py"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from models import Entry  # noqa: E402

SAMPLE = Entry(
    name="Sample",
    url="https://example.com",
    description="A sample project.",
    category="Web",
    language=["Python"],
    license="MIT",
    open_source=True,
    repository="https://github.com/LibreCourseUY/sample",
    maintainers=["@someone"],
)


def _self_check() -> None:
    from build import check_all, render_projects, render_readme

    line = render_projects([SAMPLE], ["Web", "APIs"])
    assert line.startswith("### Web\n"), line
    assert "- [Sample](https://example.com/): A sample project." in line, line
    assert "[@someone](https://github.com/someone)" in line, line
    assert "source" not in line, "no source/extra metadata in the line"
    assert "APIs" not in line, "empty categories must be omitted"

    readme = render_readme([SAMPLE], ["Web"])
    assert readme.count("<!-- PROJECTS:START -->") == 1
    assert readme.count("<!-- PROJECTS:END -->") == 1
    assert "1 projects and counting" in readme
    assert "PROJECTS:START -->\n### Web" in readme, "list must be injected at the marker"

    assert check_all(verbose=False) == 0, "committed generated files are stale"
    print("build self-check ok")


if __name__ == "__main__":
    _self_check()
