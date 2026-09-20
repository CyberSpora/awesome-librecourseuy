# Contributing to Awesome LibreCourseUY

Thank you for your interest in contributing! Adding a project to this list is
just one file and one pull request; you never edit the README.

The README is **generated** from the JSON files in [`entries/`](entries/),
using [`README.template.md`](README.template.md) as the surrounding
boilerplate. CI validates every entry and, once merged, regenerates the README
and the machine-readable feed at [`public/entries.json`](public/entries.json).

## Before you start

Read and accept our community documents:

| Document | Description |
|----------|-------------|
| [CONTRIBUTING.md](https://github.com/LibrecourseUY/.github/blob/master/CONTRIBUTING.md) | How to contribute to our projects |
| [CLA](https://github.com/LibrecourseUY/.github/blob/master/CLA.md) | Contributor License Agreement (required) |
| [CODE_OF_CONDUCT.md](https://github.com/LibrecourseUY/.github/blob/master/CODE_OF_CONDUCT.md) | Community behavior expectations |

All commits must be **GPG-signed**. See the
[GPG Key Setup guide](https://librecourseuy.github.io/git).

## Add a project

1. Fork and clone this repository.
2. Create a branch: `git checkout -b entry/your-project`.
3. Add one JSON file to `entries/`, named after your project slug
   (e.g. `entries/my-project.json`).
4. Validate locally (needs network access):

   ```bash
   uv run python scripts/validate.py
   ```

   Without network access, run the schema and cross-file checks only:

   ```bash
   uv run python scripts/validate.py --offline
   ```

5. Optionally preview the generated README:

   ```bash
   uv run python scripts/build.py
   ```

6. Commit, push and open a Pull Request.

## Entry format

```json
{
  "name": "My Project",
  "url": "https://my-project.example.com",
  "description": "One sentence describing what it does.",
  "category": "Web",
  "tags": ["astro", "open-data"],
  "language": ["Python", "TypeScript"],
  "maintainers": ["@your-handle"],
  "license": "MIT",
  "monetization": "none",
  "open_source": true,
  "repository": "https://github.com/LibreCourseUY/my-project"
}
```

| Field | Required | Notes |
|-------|----------|-------|
| `name` | yes | Display name. Must be unique. |
| `url` | yes | Project or site URL (`http`/`https`). Must be unique. |
| `description` | yes | One sentence, no trailing period needed. |
| `category` | yes | One of the categories in [`categories.json`](categories.json). |
| `tags` | no | Free-form keywords. |
| `language` | no | Programming languages, as a list. |
| `maintainers` | no | GitHub handles, each starting with `@`. |
| `license` | no | SPDX identifier, e.g. `MIT`. |
| `monetization` | no | One of `none`, `donations`, `subscription`, `freemium`, `paid`, `ads`, `sponsorship`, `other`. Defaults to `none`. |
| `open_source` | yes | `true` or `false`. |
| `repository` | if open source | Source repository URL. Required when `open_source` is `true`. |

Editors get autocomplete and inline errors from the generated
[`schema.json`](schema.json): add this to the top of your entry if your editor
does not pick it up automatically:

```json
{ "$schema": "../schema.json", "name": "..." }
```

> `$schema` is not part of the entry schema and will be rejected by validation.
> Only include it while editing locally, or rely on your editor's JSON Schema
> mapping configured to `schema.json`.

## What CI checks

`scripts/validate.py` runs on every pull request and fails if:

- a field is missing, empty, or of the wrong type;
- an unknown field is present (typos are caught, not ignored);
- a URL is not a valid `http`/`https` URL;
- the project URL is not reachable (HTTP error, dead host, timeout);
- the category is not listed in `categories.json`;
- the name or URL duplicates another entry;
- `open_source` is `true` but `repository` is missing;
- `open_source` is `true` but the repository is private, missing a license,
  or does not exist (GitHub repositories are verified through the API);
- a maintainer handle does not start with `@`.

The network checks run against GitHub with the Actions `GITHUB_TOKEN`, so
public repositories are verified reliably. Locally, set `GITHUB_TOKEN` in your
environment for the same behaviour.

## Adding a category

Categories are defined in [`categories.json`](categories.json), in display
order. To add one, edit that file in the same pull request and explain why the
existing categories do not fit.

## Questions?

Open an Issue. All contributors were where you are now.
