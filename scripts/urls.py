"""Shared URL liveness and open-source checks."""

from __future__ import annotations

import json
import os
import re
import urllib.error
import urllib.request

UA = "awesome-librecourseuy-validator/1.0 (+https://github.com/LibreCourseUY/awesome-librecourseuy)"

GITHUB_RE = re.compile(r"^https?://github\.com/([^/]+)/([^/#?]+)")


def is_open_source(repository: str, timeout: int = 15) -> tuple[bool, str]:
    """Check a repository URL looks open source.

    GitHub repos are checked via the API (public + a license file). Non-GitHub
    hosts are accepted if the page is reachable.
    """
    match = GITHUB_RE.match(repository)
    if not match:
        ok, detail = url_ok(repository, timeout)
        return ok, f"non-GitHub host, reachable ({detail})" if ok else detail

    owner, repo = match.group(1), match.group(2).removesuffix(".git")
    api = f"https://api.github.com/repos/{owner}/{repo}"
    headers = {"User-Agent": UA, "Accept": "application/vnd.github+json"}
    if token := os.environ.get("GITHUB_TOKEN"):
        headers["Authorization"] = f"Bearer {token}"
    try:
        with urllib.request.urlopen(
            urllib.request.Request(api, headers=headers), timeout=timeout
        ) as resp:
            data = json.load(resp)
    except urllib.error.HTTPError as exc:
        if exc.code == 404:
            return False, "repository not found or private"
        return False, f"HTTP {exc.code}"
    except (urllib.error.URLError, TimeoutError, OSError) as exc:
        return False, str(getattr(exc, "reason", exc))

    if data.get("private"):
        return False, "repository is private"
    if not data.get("license"):
        return False, "no license file detected"
    return True, f"public, {data['license'].get('spdx_id', 'licensed')}"


def url_ok(url: str, timeout: int = 15) -> tuple[bool, str]:
    """Return (ok, detail). Tries HEAD then GET; 2xx/3xx count as working."""
    for method in ("HEAD", "GET"):
        req = urllib.request.Request(url, method=method, headers={"User-Agent": UA})
        try:
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                if 200 <= resp.status < 400:
                    return True, str(resp.status)
        except urllib.error.HTTPError as exc:
            if exc.code in (403, 405, 501) and method == "HEAD":
                continue
            return False, f"HTTP {exc.code}"
        except (urllib.error.URLError, TimeoutError, OSError) as exc:
            return False, str(getattr(exc, "reason", exc))
    return False, "unreachable"
