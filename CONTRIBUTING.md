# Contributing to EZWowAddon

## Adding an addon to the catalog

The catalog lives at `catalog/addons.json`. To add an addon, open a PR that:

1. Adds an entry under `addons` (or `client_mods`) with the schema below.
2. Mirrors the change to `ezwow/catalog/data/addons.json` (use `cp catalog/addons.json ezwow/catalog/data/`).
3. Verifies tests pass: `pytest tests/test_catalog_data.py tests/test_catalog_schema.py -xvs`.
4. Verifies the URL resolves: `python scripts/catalog_check.py`.

Schema:

```json
{
  "id": "kebab-case-id",
  "name": "Display Name",
  "category": "ui",
  "description": "One-line summary",
  "author": "github-username",
  "github": "owner/repo",
  "branch": "master",
  "use_releases": false,
  "folder": "FolderInsideInterfaceAddOns",
  "depends": ["other-id"],
  "tags": ["essential"],
  "homepage": "https://..."
}
```

Rules:

- IDs are immutable. Once shipped, an `id` never changes.
- IDs are lowercase kebab-case (regex `^[a-z0-9][a-z0-9-]*$`).
- `depends` IDs must reference other catalog entries.
- One `category` per addon; categories are defined in the same JSON file.

## Reporting issues

Please open an issue at <https://github.com/jalsarraf0/ezwowaddon/issues>. Include OS, Python version (if running from source), and the contents of `ezwow doctor` output.

## Development setup

```bash
python3.12 -m venv .venv
.venv/bin/pip install -e ".[dev]"
.venv/bin/pytest                    # tests
.venv/bin/ruff check ezwow tests    # lint
.venv/bin/mypy ezwow                # types
```

PRs must pass CI (lint + type-check + tests, ≥70% coverage on `ezwow.core`).
