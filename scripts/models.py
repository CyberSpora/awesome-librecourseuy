"""Pydantic models for awesome-librecourseuy entries. Single source of truth."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Literal

from pydantic import BaseModel, ConfigDict, HttpUrl, field_validator, model_validator

ROOT = Path(__file__).resolve().parent.parent
ENTRIES_DIR = ROOT / "entries"
CATEGORIES_FILE = ROOT / "categories.json"
TAGS_FILE = ROOT / "tags.json"
LICENSES_FILE = ROOT / "licenses.json"
ORG = "LibreCourseUY"


def load_categories() -> list[str]:
    data = json.loads(CATEGORIES_FILE.read_text(encoding="utf-8"))
    return [c["name"] for c in data["categories"]]


def load_tags() -> set[str]:
    return set(json.loads(TAGS_FILE.read_text(encoding="utf-8"))["tags"])


def load_licenses() -> set[str]:
    return set(json.loads(LICENSES_FILE.read_text(encoding="utf-8"))["licenses"])


CATEGORIES = load_categories()
TAGS = load_tags()
LICENSES = load_licenses()


class Entry(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str
    url: HttpUrl | None = None
    description: str
    category: str
    tags: list[str] = []
    language: list[str] = []
    maintainers: list[str] = []
    license: str
    monetization: Literal[
        "none",
        "donations",
        "subscription",
        "freemium",
        "paid",
        "ads",
        "sponsorship",
        "other",
    ] = "none"
    repository: HttpUrl
    open_to_contributions: bool | None = None

    @field_validator("name", "description", "category")
    @classmethod
    def _non_empty(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("must not be empty")
        return v.strip()

    @field_validator("category")
    @classmethod
    def _known_category(cls, v: str) -> str:
        if v not in CATEGORIES:
            raise ValueError(f"unknown category {v!r}; allowed: {', '.join(CATEGORIES)}")
        return v

    @field_validator("tags")
    @classmethod
    def _known_tags(cls, v: list[str]) -> list[str]:
        unknown = sorted({tag for tag in v if tag not in TAGS})
        if unknown:
            raise ValueError(
                f"unknown tags {', '.join(unknown)}; add them to tags.json"
            )
        return v

    @field_validator("license")
    @classmethod
    def _known_license(cls, v: str) -> str:
        if v not in LICENSES:
            raise ValueError(f"unknown license {v!r}; use an identifier from licenses.json")
        return v

    @field_validator("maintainers")
    @classmethod
    def _at_handles(cls, v: list[str]) -> list[str]:
        for handle in v:
            if not handle.startswith("@"):
                raise ValueError(f"maintainer {handle!r} must start with '@'")
        return v

    @model_validator(mode="after")
    def _url_defaults_to_repository(self) -> Entry:
        if self.url is None:
            self.url = self.repository
        return self

    @property
    def relationship(self) -> Literal["official", "community"]:
        """Derived from the repository owner, never declared, so no entry can claim it."""
        owner = (self.repository.path or "/").split("/")[1]
        if self.repository.host == "github.com" and owner.lower() == ORG.lower():
            return "official"
        return "community"


def load_entries() -> list[Entry]:
    entries = []
    for path in sorted(ENTRIES_DIR.glob("*.json")):
        try:
            entries.append(Entry.model_validate_json(path.read_text(encoding="utf-8")))
        except Exception as exc:  # noqa: BLE001 - surface file name in the error
            raise ValueError(f"{path.name}: {exc}") from exc
    return entries
