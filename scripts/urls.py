"""Shared URL liveness and repository checks."""

from __future__ import annotations

import json
import os
import re
import urllib.error
import urllib.request

UA = "awesome-librecourseuy-validator/1.0 (+https://github.com/LibreCourseUY/awesome-librecourseuy)"

GITHUB_RE = re.compile(r"^https?://github\.com/([^/]+)/([^/#?]+)")


def repository_ok(repository: str, declared: str, timeout: int = 15) -> tuple[bool, str]:
    """Check a repository is public, not archived, and open source under the declared license.

    GitHub repos are checked via the API: public, not archived, with a license
    GitHub can identify that matches the declared one. Non-GitHub hosts are
    accepted if the page is reachable; reviewers check their license by hand.
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
    if data.get("archived"):
        return False, "repository is archived"
    detected = (data.get("license") or {}).get("spdx_id")
    if not detected:
        return False, "no license file detected"
    # Licensee only names licenses it recognizes, all of them open source;
    # source-available ones (Business Source License, SSPL) come back as NOASSERTION.
    if detected == "NOASSERTION":
        return False, "GitHub cannot identify the license"
    if detected != declared:
        return False, f"entry declares {declared} but GitHub detects {detected}"
    return True, f"public, {detected}"


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


def org_ok(repository: str, timeout: int = 15) -> tuple[bool, str]:
    """Check a GitHub organization exists and is public."""
    match = re.match(r"^https?://github\.com/([^/]+)/?$", repository)
    if not match:
        return False, "not a GitHub organization URL"
    api = f"https://api.github.com/orgs/{match.group(1)}"
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
            return False, "organization not found or private"
        return False, f"HTTP {exc.code}"
    except (urllib.error.URLError, TimeoutError, OSError) as exc:
        return False, str(getattr(exc, "reason", exc))
    return True, f"public ({data.get('login')})"
