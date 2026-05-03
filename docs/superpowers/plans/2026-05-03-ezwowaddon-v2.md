# EZWowAddon v2.0 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Rewrite single-file `ezwow.py` (v1.0.7) into a modular Python package — `ezwowaddon` — with a curated catalog of ≥40 addons + 6 client mods, real update detection, profiles/presets, backup/restore, modern CustomTkinter UI, and a CLI mode.

**Architecture:** Layered Python package — `ezwow.catalog` (dataclasses + JSON), `ezwow.core` (filesystem + GitHub I/O, no UI deps), `ezwow.ui` (CustomTkinter, only calls `core`), `ezwow.cli` (argparse, only calls `core`). UI and CLI are behaviour-equivalent; both are thin shells over `core`.

**Tech Stack:** Python 3.12, `requests`, `customtkinter`, `pytest` + `pytest-cov` + `responses` (HTTP mocking), `ruff` (lint), `mypy` (types), `PyInstaller` (binaries), GitHub Actions (CI).

**Spec reference:** `docs/superpowers/specs/2026-05-03-ezwowaddon-v2-design.md` — re-read each phase's spec section before starting.

---

## Conventions used in every task

- All paths absolute from repo root: `/home/jalsarraf/git/ezwowaddon/...`.
- Every task ends with `git add <files> && git commit -m "<conventional-commit-message>"`.
- TDD strict: write failing test → run and confirm fail → write code → run and confirm pass → commit.
- Use `pytest -xvs <path>` while iterating; `pytest --cov=ezwow.core --cov-fail-under=70` before committing changes that move the bar.
- Run `ruff check ezwow tests` before each commit. Run `mypy ezwow` before each commit (allow `customtkinter` import-untyped via override in `pyproject.toml`).
- After every commit, the working tree must be clean (`git status` shows nothing).
- **DO NOT push** — user controls when v2 hits remote. All commits stay local until plan completion + final review.

---

# Phase 1 — Foundation

## Task 1: Project metadata and dependencies

**Files:**
- Create: `/home/jalsarraf/git/ezwowaddon/pyproject.toml`
- Modify: `/home/jalsarraf/git/ezwowaddon/.gitignore`
- Delete: `/home/jalsarraf/git/ezwowaddon/requirements.txt` (replaced by pyproject)

- [ ] **Step 1: Replace `.gitignore` with v2-aware version**

Read current `.gitignore` first. Then overwrite with:

```gitignore
# Python
__pycache__/
*.py[cod]
*.egg-info/
.eggs/
build/
dist/
*.spec.bak
.venv/
.tox/

# Tooling
.coverage
.pytest_cache/
.ruff_cache/
.mypy_cache/
htmlcov/
coverage.xml

# IDE
.idea/
.vscode/

# App runtime
ezwow_config.json
.ezwow-cache/

# OS
.DS_Store
Thumbs.db
```

- [ ] **Step 2: Create `pyproject.toml`**

```toml
[build-system]
requires = ["setuptools>=68", "wheel"]
build-backend = "setuptools.build_meta"

[project]
name = "ezwowaddon"
version = "2.0.0"
description = "World-class Turtle WoW addon and client-mod manager"
readme = "README.md"
requires-python = ">=3.12"
license = { text = "MIT" }
authors = [{ name = "Jamal Al-Sarraf" }]
keywords = ["wow", "world of warcraft", "turtle wow", "addon", "manager"]
classifiers = [
  "Development Status :: 4 - Beta",
  "Environment :: X11 Applications",
  "Intended Audience :: End Users/Desktop",
  "License :: OSI Approved :: MIT License",
  "Operating System :: Microsoft :: Windows",
  "Operating System :: POSIX :: Linux",
  "Programming Language :: Python :: 3.12",
  "Topic :: Games/Entertainment",
]
dependencies = [
  "requests>=2.32",
  "customtkinter>=5.2.2",
]

[project.optional-dependencies]
dev = [
  "pytest>=8.0",
  "pytest-cov>=5.0",
  "responses>=0.25",
  "ruff>=0.6",
  "mypy>=1.10",
  "types-requests",
]

[project.scripts]
ezwow = "ezwow.__main__:main"

[project.urls]
Homepage = "https://github.com/jalsarraf0/ezwowaddon"
Issues = "https://github.com/jalsarraf0/ezwowaddon/issues"

[tool.setuptools]
packages = ["ezwow", "ezwow.catalog", "ezwow.core", "ezwow.ui", "ezwow.ui.tabs", "ezwow.ui.widgets"]

[tool.setuptools.package-data]
"ezwow.catalog" = ["data/*.json"]

[tool.ruff]
line-length = 100
target-version = "py312"

[tool.ruff.lint]
select = ["E", "F", "W", "I", "N", "UP", "B", "C4", "SIM", "RUF"]
ignore = ["E501"]  # line length handled by formatter

[tool.mypy]
python_version = "3.12"
strict = true
warn_unused_ignores = true

[[tool.mypy.overrides]]
module = ["customtkinter.*", "responses.*"]
ignore_missing_imports = true

[tool.pytest.ini_options]
addopts = "-ra"
testpaths = ["tests"]

[tool.coverage.run]
source = ["ezwow"]
omit = ["ezwow/ui/*", "ezwow/__main__.py"]
```

- [ ] **Step 3: Delete legacy requirements file**

```bash
git rm /home/jalsarraf/git/ezwowaddon/requirements.txt
```

- [ ] **Step 4: Install dev deps in current venv**

```bash
cd /home/jalsarraf/git/ezwowaddon
python3.12 -m venv .venv
.venv/bin/pip install -e ".[dev]"
```

Expected: success, `ezwow` console script registered.

- [ ] **Step 5: Commit**

```bash
git add pyproject.toml .gitignore
git commit -m "chore: introduce pyproject.toml, drop requirements.txt"
```

---

## Task 2: Package skeleton

**Files:**
- Create: `/home/jalsarraf/git/ezwowaddon/ezwow/__init__.py`
- Create: `/home/jalsarraf/git/ezwowaddon/ezwow/__main__.py`
- Create: `/home/jalsarraf/git/ezwowaddon/ezwow/config.py`
- Create: `/home/jalsarraf/git/ezwowaddon/tests/__init__.py`
- Create: `/home/jalsarraf/git/ezwowaddon/tests/conftest.py`
- Create: `/home/jalsarraf/git/ezwowaddon/tests/test_smoke.py`

- [ ] **Step 1: Write smoke test**

`tests/test_smoke.py`:

```python
import importlib

import ezwow


def test_version_string_present():
    assert isinstance(ezwow.__version__, str)
    assert ezwow.__version__.count(".") == 2


def test_subpackages_importable():
    for mod in (
        "ezwow",
        "ezwow.catalog",
        "ezwow.core",
        "ezwow.ui",
        "ezwow.cli",
    ):
        importlib.import_module(mod)
```

- [ ] **Step 2: Run test, confirm failure**

```bash
.venv/bin/pytest tests/test_smoke.py -xvs
```

Expected: `ImportError: No module named 'ezwow'`.

- [ ] **Step 3: Create `ezwow/__init__.py`**

```python
"""EZWowAddon — Turtle WoW addon and client-mod manager."""

__version__ = "2.0.0"
__all__ = ["__version__"]
```

- [ ] **Step 4: Create stub `ezwow/__main__.py`**

```python
"""Package entry point. Routes to CLI or GUI based on argv."""

from __future__ import annotations

import sys


def main(argv: list[str] | None = None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)
    if args and args[0] not in {"--gui", "-g"}:
        from ezwow.cli import run

        return run(args)
    from ezwow.ui.app import launch

    launch()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
```

- [ ] **Step 5: Create stub subpackages**

`ezwow/catalog/__init__.py`:

```python
"""Catalog: schemas and loaders for the curated addon list."""
```

`ezwow/core/__init__.py`:

```python
"""Core: filesystem and network operations. No UI imports."""
```

`ezwow/ui/__init__.py`:

```python
"""UI: CustomTkinter views. Imports core only."""
```

`ezwow/ui/tabs/__init__.py`:

```python
"""UI tab modules."""
```

`ezwow/ui/widgets/__init__.py`:

```python
"""Reusable UI widgets."""
```

`ezwow/cli.py`:

```python
"""Command-line interface. Stub — see plan Task 17."""

from __future__ import annotations


def run(argv: list[str]) -> int:
    raise NotImplementedError("CLI not yet implemented")
```

`ezwow/ui/app.py`:

```python
"""GUI entry point. Stub — see plan Task 18."""


def launch() -> None:
    raise NotImplementedError("GUI not yet implemented")
```

- [ ] **Step 6: Create `ezwow/config.py`**

```python
"""User config locations and persistence."""

from __future__ import annotations

import json
import os
import pathlib
from dataclasses import asdict, dataclass, field

LEGACY_CONFIG_FILENAME = "ezwow_config.json"


def config_dir() -> pathlib.Path:
    """Return the per-user config directory, creating it if needed."""
    if os.name == "nt":
        base = pathlib.Path(os.environ.get("APPDATA", pathlib.Path.home() / "AppData" / "Roaming"))
    else:
        base = pathlib.Path(
            os.environ.get("XDG_CONFIG_HOME", pathlib.Path.home() / ".config")
        )
    target = base / "ezwowaddon"
    target.mkdir(parents=True, exist_ok=True)
    return target


def cache_dir() -> pathlib.Path:
    """Return the per-user cache directory, creating it if needed."""
    if os.name == "nt":
        base = pathlib.Path(os.environ.get("LOCALAPPDATA", pathlib.Path.home() / "AppData" / "Local"))
    else:
        base = pathlib.Path(
            os.environ.get("XDG_CACHE_HOME", pathlib.Path.home() / ".cache")
        )
    target = base / "ezwowaddon"
    target.mkdir(parents=True, exist_ok=True)
    return target


def data_dir() -> pathlib.Path:
    """Return the per-user data directory (used for backups)."""
    if os.name == "nt":
        base = pathlib.Path(os.environ.get("APPDATA", pathlib.Path.home() / "AppData" / "Roaming"))
    else:
        base = pathlib.Path(
            os.environ.get("XDG_DATA_HOME", pathlib.Path.home() / ".local" / "share")
        )
    target = base / "ezwowaddon"
    target.mkdir(parents=True, exist_ok=True)
    return target


@dataclass
class UserConfig:
    addons_folder: str | None = None
    data_folder: str | None = None
    github_pat: str | None = None
    remote_catalog_enabled: bool = True
    theme: str = "dark"
    backup_dir: str | None = None
    auto_backup_before_batch: bool = True
    extras: dict[str, str] = field(default_factory=dict)


def config_path() -> pathlib.Path:
    return config_dir() / "config.json"


def load() -> UserConfig:
    path = config_path()
    if path.exists():
        raw = json.loads(path.read_text(encoding="utf-8"))
        return UserConfig(**{k: raw.get(k) for k in UserConfig.__dataclass_fields__})
    legacy = pathlib.Path.cwd() / LEGACY_CONFIG_FILENAME
    if legacy.exists():
        raw = json.loads(legacy.read_text(encoding="utf-8"))
        cfg = UserConfig(addons_folder=raw.get("addons_folder"))
        save(cfg)
        return cfg
    return UserConfig()


def save(cfg: UserConfig) -> None:
    path = config_path()
    path.write_text(json.dumps(asdict(cfg), indent=2), encoding="utf-8")
```

- [ ] **Step 7: Create `tests/conftest.py`**

```python
"""Shared test fixtures."""

from __future__ import annotations

import pathlib
from typing import Iterator

import pytest


@pytest.fixture
def fake_wow_root(tmp_path: pathlib.Path) -> pathlib.Path:
    """Create a TurtleWoW-shaped folder tree under tmp_path."""
    root = tmp_path / "Turtle WoW"
    (root / "Interface" / "AddOns").mkdir(parents=True)
    (root / "Data").mkdir()
    (root / "WTF" / "Account" / "TEST" / "SavedVariables").mkdir(parents=True)
    return root


@pytest.fixture
def fake_addons_folder(fake_wow_root: pathlib.Path) -> pathlib.Path:
    return fake_wow_root / "Interface" / "AddOns"


@pytest.fixture
def isolated_config(
    tmp_path: pathlib.Path, monkeypatch: pytest.MonkeyPatch
) -> Iterator[pathlib.Path]:
    """Redirect XDG_*_HOME / APPDATA to a tmp dir so config never touches real user."""
    cfg_root = tmp_path / "user-config"
    cfg_root.mkdir()
    monkeypatch.setenv("XDG_CONFIG_HOME", str(cfg_root / "config"))
    monkeypatch.setenv("XDG_CACHE_HOME", str(cfg_root / "cache"))
    monkeypatch.setenv("XDG_DATA_HOME", str(cfg_root / "share"))
    monkeypatch.setenv("APPDATA", str(cfg_root / "AppData" / "Roaming"))
    monkeypatch.setenv("LOCALAPPDATA", str(cfg_root / "AppData" / "Local"))
    yield cfg_root
```

- [ ] **Step 8: Create `tests/__init__.py`**

```python
```

(empty file)

- [ ] **Step 9: Run smoke test, confirm pass**

```bash
.venv/bin/pytest tests/test_smoke.py -xvs
```

Expected: 2 passed.

- [ ] **Step 10: Run lint and types**

```bash
.venv/bin/ruff check ezwow tests
.venv/bin/mypy ezwow
```

Expected: clean.

- [ ] **Step 11: Commit**

```bash
git add ezwow tests
git commit -m "feat: scaffold ezwow package with subpackages and config module"
```

---

## Task 3: Convert legacy `ezwow.py` to shim

**Files:**
- Modify (overwrite): `/home/jalsarraf/git/ezwowaddon/ezwow.py`
- Modify: `/home/jalsarraf/git/ezwowaddon/ezwow.spec`

- [ ] **Step 1: Inspect existing PyInstaller spec**

```bash
cat /home/jalsarraf/git/ezwowaddon/ezwow.spec
```

- [ ] **Step 2: Replace `ezwow.py` with package shim**

```python
"""Legacy entry point for backwards compatibility.

The real package lives in `ezwow/`. PyInstaller and direct
`python ezwow.py` invocations route through here.
"""

from __future__ import annotations

import sys

from ezwow.__main__ import main


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
```

- [ ] **Step 3: Update `ezwow.spec` to collect customtkinter assets**

Edit the existing spec by adding `from PyInstaller.utils.hooks import collect_all` at the top and:

```python
ctk_datas, ctk_binaries, ctk_hiddenimports = collect_all("customtkinter")
```

Then in the `Analysis()` call, merge:

```python
datas=ctk_datas,
binaries=ctk_binaries,
hiddenimports=ctk_hiddenimports,
```

The exact diff depends on the existing spec — read it first, then apply minimal changes.

- [ ] **Step 4: Verify shim still importable**

```bash
.venv/bin/python -c "import ezwow; print(ezwow.__version__)"
```

Expected: `2.0.0`.

- [ ] **Step 5: Commit**

```bash
git add ezwow.py ezwow.spec
git commit -m "refactor: turn ezwow.py into shim over ezwow package"
```

---

# Phase 2 — Catalog

## Task 4: Catalog schema dataclasses

**Files:**
- Create: `/home/jalsarraf/git/ezwowaddon/ezwow/catalog/schema.py`
- Create: `/home/jalsarraf/git/ezwowaddon/tests/test_catalog_schema.py`

- [ ] **Step 1: Write failing test**

```python
"""Tests for ezwow.catalog.schema."""

from __future__ import annotations

import pytest

from ezwow.catalog.schema import (
    Addon,
    Catalog,
    Category,
    ClientMod,
    Preset,
    SchemaError,
    parse_catalog,
)


VALID_RAW = {
    "schema_version": 2,
    "updated": "2026-05-03",
    "categories": [
        {"id": "ui", "label": "UI / Interface"},
        {"id": "quest", "label": "Quest & Map"},
    ],
    "addons": [
        {
            "id": "pfquest",
            "name": "pfQuest",
            "category": "quest",
            "description": "Quest helper",
            "author": "shagu",
            "github": "shagu/pfQuest",
            "branch": "master",
            "use_releases": False,
            "folder": "pfQuest",
            "depends": [],
            "tags": ["essential"],
        }
    ],
    "client_mods": [
        {
            "id": "vanillafixes",
            "name": "VanillaFixes",
            "description": "Stutter fix",
            "github": "RetroCro/TurtleWoW-Mods",
            "asset_pattern": "VanillaFixes*.zip",
            "install_to": "data_root",
            "files_to_install": ["*.exe", "*.dll"],
            "tags": ["essential"],
        }
    ],
    "presets": {
        "essential": {
            "label": "Essential",
            "addons": ["pfquest"],
            "client_mods": ["vanillafixes"],
        }
    },
}


def test_parse_valid_catalog():
    cat = parse_catalog(VALID_RAW)
    assert isinstance(cat, Catalog)
    assert cat.schema_version == 2
    assert cat.categories == [
        Category(id="ui", label="UI / Interface"),
        Category(id="quest", label="Quest & Map"),
    ]
    assert len(cat.addons) == 1
    assert isinstance(cat.addons[0], Addon)
    assert cat.addons[0].id == "pfquest"
    assert cat.client_mods[0].install_to == "data_root"
    assert "essential" in cat.presets
    assert cat.presets["essential"].addons == ["pfquest"]


def test_parse_rejects_wrong_schema_version():
    raw = {**VALID_RAW, "schema_version": 1}
    with pytest.raises(SchemaError, match="schema_version"):
        parse_catalog(raw)


def test_parse_rejects_unknown_category():
    raw = dict(VALID_RAW)
    raw["addons"] = [{**VALID_RAW["addons"][0], "category": "nonexistent"}]
    with pytest.raises(SchemaError, match="category"):
        parse_catalog(raw)


def test_parse_rejects_dep_to_unknown_addon():
    raw = dict(VALID_RAW)
    raw["addons"] = [{**VALID_RAW["addons"][0], "depends": ["does-not-exist"]}]
    with pytest.raises(SchemaError, match="depends"):
        parse_catalog(raw)


def test_parse_rejects_invalid_id_format():
    raw = dict(VALID_RAW)
    raw["addons"] = [{**VALID_RAW["addons"][0], "id": "PFQuest_BAD"}]
    with pytest.raises(SchemaError, match="id"):
        parse_catalog(raw)


def test_addon_get_branch_url():
    addon = parse_catalog(VALID_RAW).addons[0]
    assert addon.branch_zip_url() == (
        "https://github.com/shagu/pfQuest/archive/refs/heads/master.zip"
    )


def test_preset_resolves_unknown_addon_raises():
    raw = dict(VALID_RAW)
    raw["presets"] = {"bad": {"label": "Bad", "addons": ["nope"], "client_mods": []}}
    with pytest.raises(SchemaError, match="preset"):
        parse_catalog(raw)
```

- [ ] **Step 2: Run test, confirm failure**

```bash
.venv/bin/pytest tests/test_catalog_schema.py -xvs
```

Expected: ImportError.

- [ ] **Step 3: Implement `ezwow/catalog/schema.py`**

```python
"""Catalog dataclasses and validation. Pure logic, no I/O."""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any, Literal

ID_RE = re.compile(r"^[a-z0-9][a-z0-9-]*$")
SUPPORTED_SCHEMA_VERSION = 2


class SchemaError(ValueError):
    """Raised when a catalog dict fails validation."""


@dataclass(frozen=True, slots=True)
class Category:
    id: str
    label: str


@dataclass(frozen=True, slots=True)
class Addon:
    id: str
    name: str
    category: str
    description: str
    author: str
    github: str
    branch: str = "master"
    use_releases: bool = False
    folder: str = ""
    depends: tuple[str, ...] = ()
    tags: tuple[str, ...] = ()
    homepage: str | None = None

    def branch_zip_url(self) -> str:
        return f"https://github.com/{self.github}/archive/refs/heads/{self.branch}.zip"


InstallTarget = Literal["data_root", "addons_folder"]


@dataclass(frozen=True, slots=True)
class ClientMod:
    id: str
    name: str
    description: str
    github: str
    asset_pattern: str
    install_to: InstallTarget
    files_to_install: tuple[str, ...]
    tags: tuple[str, ...] = ()
    branch: str = "main"
    homepage: str | None = None


@dataclass(frozen=True, slots=True)
class Preset:
    id: str
    label: str
    addons: tuple[str, ...] = ()
    client_mods: tuple[str, ...] = ()


@dataclass(frozen=True, slots=True)
class Catalog:
    schema_version: int
    updated: str
    categories: list[Category]
    addons: list[Addon]
    client_mods: list[ClientMod]
    presets: dict[str, Preset] = field(default_factory=dict)

    def addon_by_id(self, addon_id: str) -> Addon | None:
        return next((a for a in self.addons if a.id == addon_id), None)

    def client_mod_by_id(self, mod_id: str) -> ClientMod | None:
        return next((m for m in self.client_mods if m.id == mod_id), None)


def _check_id(kind: str, value: str) -> None:
    if not ID_RE.match(value):
        raise SchemaError(
            f"{kind} id {value!r} must be lowercase kebab-case (matched {ID_RE.pattern})"
        )


def parse_catalog(raw: dict[str, Any]) -> Catalog:
    if raw.get("schema_version") != SUPPORTED_SCHEMA_VERSION:
        raise SchemaError(
            f"Unsupported schema_version {raw.get('schema_version')!r}; "
            f"expected {SUPPORTED_SCHEMA_VERSION}"
        )

    categories = [Category(id=c["id"], label=c["label"]) for c in raw.get("categories", [])]
    cat_ids = {c.id for c in categories}

    addons: list[Addon] = []
    for entry in raw.get("addons", []):
        _check_id("addon", entry["id"])
        if entry["category"] not in cat_ids:
            raise SchemaError(
                f"addon {entry['id']!r} references unknown category {entry['category']!r}"
            )
        addons.append(
            Addon(
                id=entry["id"],
                name=entry["name"],
                category=entry["category"],
                description=entry["description"],
                author=entry["author"],
                github=entry["github"],
                branch=entry.get("branch", "master"),
                use_releases=bool(entry.get("use_releases", False)),
                folder=entry.get("folder", entry["id"]),
                depends=tuple(entry.get("depends", [])),
                tags=tuple(entry.get("tags", [])),
                homepage=entry.get("homepage"),
            )
        )
    addon_ids = {a.id for a in addons}

    for addon in addons:
        for dep in addon.depends:
            if dep not in addon_ids:
                raise SchemaError(
                    f"addon {addon.id!r} depends on unknown addon {dep!r}"
                )

    client_mods: list[ClientMod] = []
    for entry in raw.get("client_mods", []):
        _check_id("client_mod", entry["id"])
        install_to = entry["install_to"]
        if install_to not in ("data_root", "addons_folder"):
            raise SchemaError(f"client_mod {entry['id']!r} has invalid install_to {install_to!r}")
        client_mods.append(
            ClientMod(
                id=entry["id"],
                name=entry["name"],
                description=entry["description"],
                github=entry["github"],
                asset_pattern=entry["asset_pattern"],
                install_to=install_to,
                files_to_install=tuple(entry.get("files_to_install", [])),
                tags=tuple(entry.get("tags", [])),
                branch=entry.get("branch", "main"),
                homepage=entry.get("homepage"),
            )
        )
    mod_ids = {m.id for m in client_mods}

    presets: dict[str, Preset] = {}
    for preset_id, body in raw.get("presets", {}).items():
        _check_id("preset", preset_id)
        for ref in body.get("addons", []):
            if ref not in addon_ids:
                raise SchemaError(f"preset {preset_id!r} references unknown addon {ref!r}")
        for ref in body.get("client_mods", []):
            if ref not in mod_ids:
                raise SchemaError(f"preset {preset_id!r} references unknown client_mod {ref!r}")
        presets[preset_id] = Preset(
            id=preset_id,
            label=body["label"],
            addons=tuple(body.get("addons", [])),
            client_mods=tuple(body.get("client_mods", [])),
        )

    return Catalog(
        schema_version=raw["schema_version"],
        updated=raw["updated"],
        categories=categories,
        addons=addons,
        client_mods=client_mods,
        presets=presets,
    )
```

- [ ] **Step 4: Run tests, confirm pass**

```bash
.venv/bin/pytest tests/test_catalog_schema.py -xvs
```

Expected: 7 passed.

- [ ] **Step 5: Commit**

```bash
git add ezwow/catalog/schema.py tests/test_catalog_schema.py
git commit -m "feat(catalog): add immutable schema dataclasses with parse_catalog validator"
```

---

## Task 5: Bundled catalog JSON (initial population)

**Files:**
- Create: `/home/jalsarraf/git/ezwowaddon/ezwow/catalog/data/addons.json` (bundled fallback for runtime)
- Create: `/home/jalsarraf/git/ezwowaddon/catalog/addons.json` (canonical, also used for community PRs — symlink target)
- Create: `/home/jalsarraf/git/ezwowaddon/tests/test_catalog_data.py`

The two locations matter: `catalog/addons.json` is the human-edited source-of-truth at the repo root (community PRs against this file). `ezwow/catalog/data/addons.json` is the bundled package data (PyInstaller picks it up). They must be kept identical — Task 5 establishes them as identical-by-copy; later tasks can introduce a build step.

- [ ] **Step 1: Write failing test**

```python
"""Validate that the bundled catalog parses and contains required entries."""

from __future__ import annotations

import json
import pathlib

import pytest

from ezwow.catalog.schema import parse_catalog


REPO_ROOT = pathlib.Path(__file__).resolve().parents[1]
BUNDLED = REPO_ROOT / "ezwow" / "catalog" / "data" / "addons.json"
CANONICAL = REPO_ROOT / "catalog" / "addons.json"


def test_canonical_catalog_parses():
    raw = json.loads(CANONICAL.read_text(encoding="utf-8"))
    cat = parse_catalog(raw)
    assert len(cat.addons) >= 40, f"need >=40 addons, got {len(cat.addons)}"
    assert len(cat.client_mods) >= 6, f"need >=6 client mods, got {len(cat.client_mods)}"


def test_bundled_matches_canonical():
    bundled = BUNDLED.read_text(encoding="utf-8")
    canonical = CANONICAL.read_text(encoding="utf-8")
    assert bundled == canonical, "bundled JSON drifted from catalog/addons.json"


@pytest.mark.parametrize(
    "preset_id", ["essential", "raider", "hardcore", "minimal-ui"]
)
def test_required_presets_exist(preset_id: str):
    raw = json.loads(CANONICAL.read_text(encoding="utf-8"))
    cat = parse_catalog(raw)
    assert preset_id in cat.presets


def test_legacy_v1_addons_still_present():
    raw = json.loads(CANONICAL.read_text(encoding="utf-8"))
    cat = parse_catalog(raw)
    legacy_ids = {"pfquest", "pfquest-turtle", "bigwigs", "shagu-tweaks", "auctionator", "aux"}
    cat_ids = {a.id for a in cat.addons}
    missing = legacy_ids - cat_ids
    assert not missing, f"v1 addons missing in v2 catalog: {missing}"
```

- [ ] **Step 2: Run test, confirm fail**

```bash
.venv/bin/pytest tests/test_catalog_data.py -xvs
```

Expected: FileNotFoundError.

- [ ] **Step 3: Create `catalog/addons.json`**

The full catalog JSON. Must include:
- 9 categories (ui, quest, combat, auction, inventory, raid, social, utility, client-mod)
- ≥40 addons across categories
- 6 client mods (vanillafixes, superwow, nampower, unitxp-sp3, vanillatweaks, perfboost)
- 4 presets: essential, raider, hardcore, minimal-ui

Write the full file. Use exact addon list from spec §13:

```json
{
  "schema_version": 2,
  "updated": "2026-05-03",
  "categories": [
    {"id": "ui", "label": "UI / Interface"},
    {"id": "quest", "label": "Quest & Map"},
    {"id": "combat", "label": "Combat & Meters"},
    {"id": "auction", "label": "Auction House"},
    {"id": "inventory", "label": "Inventory & Mail"},
    {"id": "raid", "label": "Raid & Dungeon"},
    {"id": "social", "label": "Social"},
    {"id": "utility", "label": "Utility / Quality of Life"},
    {"id": "client-mod", "label": "Client Mod"}
  ],
  "addons": [
    {"id": "pfui", "name": "pfUI", "category": "ui", "description": "Full UI replacement for Vanilla & TBC", "author": "shagu", "github": "shagu/pfUI", "folder": "pfUI", "tags": ["popular"], "homepage": "https://shagu.org/pfUI"},
    {"id": "shagu-tweaks", "name": "ShaguTweaks", "category": "ui", "description": "Quality-of-life tweaks for the default 1.12 UI", "author": "shagu", "github": "shagu/ShaguTweaks", "folder": "ShaguTweaks", "tags": ["essential"]},
    {"id": "shagu-plates", "name": "ShaguPlates", "category": "ui", "description": "Standalone export of pfUI nameplates", "author": "shagu", "github": "shagu/ShaguPlates", "folder": "ShaguPlates"},
    {"id": "moveanything", "name": "MoveAnything", "category": "ui", "description": "Reposition any UI element", "author": "community", "github": "Road-block/MoveAnything", "folder": "MoveAnything"},
    {"id": "newlevelframe", "name": "NewLevelFrame", "category": "ui", "description": "Level frame interface for Vanilla", "author": "community", "github": "Roadblock/Vanilla-NewLevelFrame", "folder": "NewLevelFrame"},
    {"id": "pfquest", "name": "pfQuest", "category": "quest", "description": "Quest helper with in-game map markers", "author": "shagu", "github": "shagu/pfQuest", "folder": "pfQuest", "tags": ["essential"], "homepage": "https://shagu.org/pfQuest"},
    {"id": "pfquest-turtle", "name": "pfQuest-Turtle", "category": "quest", "description": "Turtle WoW-specific quest data extension", "author": "shagu", "github": "shagu/pfQuest-turtle", "folder": "pfQuest-turtle", "depends": ["pfquest"], "tags": ["essential", "turtle-only"]},
    {"id": "pfextend", "name": "pfExtend", "category": "quest", "description": "Loot display + quest chain browser extension for pfQuest", "author": "community", "github": "shagu/pfExtend", "folder": "pfExtend", "depends": ["pfquest"]},
    {"id": "cartographer", "name": "Cartographer", "category": "quest", "description": "Enhanced map with zone levels", "author": "community", "github": "laytya/Cartographer", "folder": "Cartographer"},
    {"id": "cromulent", "name": "Cromulent's Map Addon", "category": "quest", "description": "Lightweight map with coordinates", "author": "community", "github": "Road-block/Cromulent", "folder": "Cromulent"},
    {"id": "modern-map-markers", "name": "ModernMapMarkers", "category": "quest", "description": "Updated map marker visuals", "author": "community", "github": "wardz/ModernMapMarkers", "folder": "ModernMapMarkers"},
    {"id": "bigwigs", "name": "BigWigs", "category": "combat", "description": "Boss warnings and ability timers", "author": "CosminPOP", "github": "CosminPOP/BigWigs", "folder": "BigWigs", "tags": ["raider"]},
    {"id": "shagudps", "name": "ShaguDPS", "category": "combat", "description": "Lightweight damage meter", "author": "shagu", "github": "shagu/ShaguDPS", "folder": "ShaguDPS"},
    {"id": "dpsmate", "name": "DPSMate", "category": "combat", "description": "Comprehensive damage tracking", "author": "community", "github": "ProjectAzerothGitHub/DPSMate-Updated", "folder": "DPSMate"},
    {"id": "tww-threat", "name": "TWW Threat", "category": "combat", "description": "Turtle WoW threat meter", "author": "community", "github": "TheKaitilyn/TWW-Threat", "folder": "TWWThreat"},
    {"id": "classic-snowfall", "name": "Classic Snowfall", "category": "combat", "description": "Faster keypress response in combat", "author": "community", "github": "ratamahatta-zero/ClassicSnowfall-Vanilla", "folder": "ClassicSnowfall"},
    {"id": "sp-swing-timer", "name": "SP Swing Timer", "category": "combat", "description": "Melee swing timer display", "author": "community", "github": "smp4488/SP_SwingTimer-Vanilla", "folder": "SP_SwingTimer"},
    {"id": "proc-doc", "name": "Proc Doc", "category": "combat", "description": "Tracks proc cooldowns and reminders", "author": "community", "github": "Road-block/ProcDoc", "folder": "ProcDoc"},
    {"id": "attack-bar", "name": "Attack Bar", "category": "combat", "description": "Action bar overlay during attacks", "author": "community", "github": "Geigerkind/AttackBar", "folder": "AttackBar"},
    {"id": "aux", "name": "Aux", "category": "auction", "description": "Powerful auction house revamp", "author": "gwetchen", "github": "gwetchen/aux-addon", "folder": "aux-addon", "tags": ["essential"]},
    {"id": "auctionator", "name": "Auctionator", "category": "auction", "description": "Simplified auction house UI", "author": "nimeral", "github": "nimeral/AuctionatorVanilla", "folder": "Auctionator"},
    {"id": "bagnon", "name": "Bagnon", "category": "inventory", "description": "Combined bag interface with search", "author": "community", "github": "laytya/Bagnon-Vanilla", "folder": "Bagnon"},
    {"id": "bagshui", "name": "BagShui", "category": "inventory", "description": "Alternative bag manager", "author": "community", "github": "veechs/BagShui", "folder": "BagShui"},
    {"id": "turtle-mail", "name": "Turtle Mail", "category": "inventory", "description": "Multi-message mail enhancement", "author": "community", "github": "Aubratus/TurtleMail", "folder": "TurtleMail", "tags": ["turtle-only"]},
    {"id": "atlas-turtle", "name": "Atlas Turtle", "category": "raid", "description": "Dungeon layout maps", "author": "community", "github": "TheKaitilyn/Atlas-Turtle-WoW", "folder": "Atlas", "tags": ["turtle-only"]},
    {"id": "atlas-loot-turtle", "name": "AtlasLoot Turtle", "category": "raid", "description": "Boss loot database", "author": "community", "github": "TheKaitilyn/AtlasLoot-Turtle-WoW", "folder": "AtlasLoot", "tags": ["turtle-only"]},
    {"id": "atlas-quest-turtle", "name": "Atlas Quest Turtle", "category": "raid", "description": "Dungeon quest tracking", "author": "community", "github": "TheKaitilyn/AtlasQuest-Turtle-WoW", "folder": "AtlasQuest", "tags": ["turtle-only"]},
    {"id": "wim", "name": "WIM", "category": "social", "description": "Whispers in instant-message style windows", "author": "community", "github": "MaximilianHoffmann/WIM-Vanilla", "folder": "WIM"},
    {"id": "global-friends-list", "name": "GlobalFriendsList", "category": "social", "description": "Hardcore-mode friend auto-readd", "author": "community", "github": "Aubratus/GlobalFriendsList", "folder": "GlobalFriendsList", "tags": ["hardcore"]},
    {"id": "friend-o-tron", "name": "Friend-O-Tron", "category": "social", "description": "Sync friends across alts", "author": "community", "github": "TheKaitilyn/Friend-O-Tron", "folder": "FriendOTron"},
    {"id": "restbar", "name": "Restbar", "category": "utility", "description": "Rested XP tracker", "author": "community", "github": "Roadblock/Restbar", "folder": "Restbar"},
    {"id": "bettercharacterstats", "name": "BetterCharacterStats", "category": "utility", "description": "Enhanced character pane", "author": "community", "github": "ProjectAzerothGitHub/BetterCharacterStats", "folder": "BetterCharacterStats", "tags": ["popular"]},
    {"id": "pet-xp-bar", "name": "Pet XP Bar", "category": "utility", "description": "Hunter pet XP display", "author": "community", "github": "Aubratus/PetXPBar", "folder": "PetXPBar"},
    {"id": "minimap-button-bag", "name": "Minimap Button Bag", "category": "utility", "description": "Consolidates minimap buttons", "author": "community", "github": "Road-block/MinimapButtonBag", "folder": "MinimapButtonBag"},
    {"id": "level-range", "name": "Level Range", "category": "utility", "description": "Show enemy level color range", "author": "community", "github": "TheKaitilyn/LevelRange", "folder": "LevelRange"},
    {"id": "missing-crafts", "name": "MissingCrafts", "category": "utility", "description": "Show missing crafts for professions", "author": "community", "github": "smp4488/MissingCrafts", "folder": "MissingCrafts"},
    {"id": "master-trade-skills", "name": "MasterTradeSkills", "category": "utility", "description": "Trade-skill info in tooltips", "author": "community", "github": "smp4488/MasterTradeSkills", "folder": "MasterTradeSkills"},
    {"id": "item-tooltip-icons", "name": "ItemTooltipIcons", "category": "utility", "description": "Profession icons in tooltips", "author": "community", "github": "smp4488/ItemTooltipIcons", "folder": "ItemTooltipIcons"},
    {"id": "voiceover", "name": "VoiceOver", "category": "utility", "description": "Voice-acted quest text", "author": "community", "github": "mrthinger/wow-voiceover", "folder": "AI_VoiceOver"},
    {"id": "pizza-world-buffs", "name": "PizzaWorldBuffs", "category": "utility", "description": "Track world-buff timers", "author": "community", "github": "PizzaPie/PizzaWorldBuffs", "folder": "PizzaWorldBuffs"}
  ],
  "client_mods": [
    {"id": "vanillafixes", "name": "VanillaFixes", "description": "Stutter and animation fixes; optional Vulkan via DXVK", "github": "RetroCro/TurtleWoW-Mods", "asset_pattern": "VanillaFixes*.zip", "install_to": "data_root", "files_to_install": ["VanillaFixes.exe", "*.dll"], "tags": ["essential", "performance"]},
    {"id": "superwow", "name": "SuperWoW", "description": "Expands Lua API and macro length", "github": "RetroCro/TurtleWoW-Mods", "asset_pattern": "SuperWoW*.zip", "install_to": "data_root", "files_to_install": ["SuperWoWPatch.dll", "*.exe"], "tags": ["essential"]},
    {"id": "nampower", "name": "Nampower", "description": "Spell queueing and quickcasting", "github": "RetroCro/TurtleWoW-Mods", "asset_pattern": "Nampower*.zip", "install_to": "data_root", "files_to_install": ["nampower.dll"]},
    {"id": "unitxp-sp3", "name": "UnitXP SP3", "description": "Camera, nameplates, background notifications", "github": "RetroCro/TurtleWoW-Mods", "asset_pattern": "UnitXP*.zip", "install_to": "data_root", "files_to_install": ["UnitXP.dll"]},
    {"id": "vanillatweaks", "name": "VanillaTweaks", "description": "Widescreen FoV, farclip, right-click autoloot", "github": "RetroCro/TurtleWoW-Mods", "asset_pattern": "VanillaTweaks*.zip", "install_to": "data_root", "files_to_install": ["VanillaTweaks.exe", "*.dll"]},
    {"id": "perfboost", "name": "PerfBoost", "description": "Per-unit-type render distance tuning", "github": "RetroCro/TurtleWoW-Mods", "asset_pattern": "PerfBoost*.zip", "install_to": "data_root", "files_to_install": ["*.dll"]}
  ],
  "presets": {
    "essential": {
      "label": "Essential (new players)",
      "addons": ["pfquest", "pfquest-turtle", "shagu-tweaks", "bagnon", "aux", "bettercharacterstats"],
      "client_mods": ["vanillafixes"]
    },
    "raider": {
      "label": "Raider",
      "addons": ["pfquest", "pfquest-turtle", "bigwigs", "shagudps", "pfui", "bettercharacterstats", "atlas-turtle", "atlas-loot-turtle"],
      "client_mods": ["vanillafixes", "superwow"]
    },
    "hardcore": {
      "label": "Hardcore",
      "addons": ["pfquest", "pfquest-turtle", "global-friends-list", "restbar", "level-range"],
      "client_mods": ["vanillafixes"]
    },
    "minimal-ui": {
      "label": "Minimal UI",
      "addons": ["shagu-tweaks", "bagnon"],
      "client_mods": []
    }
  }
}
```

- [ ] **Step 4: Copy to bundled location**

```bash
mkdir -p /home/jalsarraf/git/ezwowaddon/ezwow/catalog/data
cp /home/jalsarraf/git/ezwowaddon/catalog/addons.json /home/jalsarraf/git/ezwowaddon/ezwow/catalog/data/addons.json
```

- [ ] **Step 5: Run tests, confirm pass**

```bash
.venv/bin/pytest tests/test_catalog_data.py tests/test_catalog_schema.py -xvs
```

Expected: all pass; addon count ≥40, client mods ≥6.

- [ ] **Step 6: Commit**

```bash
git add catalog/addons.json ezwow/catalog/data/addons.json tests/test_catalog_data.py
git commit -m "feat(catalog): add curated catalog with 40 addons + 6 client mods + 4 presets"
```

---

## Task 6: Catalog loader

**Files:**
- Create: `/home/jalsarraf/git/ezwowaddon/ezwow/catalog/loader.py`
- Create: `/home/jalsarraf/git/ezwowaddon/tests/test_catalog_loader.py`

- [ ] **Step 1: Write failing test**

```python
"""Tests for catalog.loader."""

from __future__ import annotations

import json
import pathlib

import pytest

from ezwow.catalog import loader


def test_load_bundled_returns_catalog():
    cat = loader.load_bundled()
    assert cat.schema_version == 2
    assert len(cat.addons) >= 40


def test_load_from_path(tmp_path: pathlib.Path):
    src = tmp_path / "addons.json"
    src.write_text(json.dumps({
        "schema_version": 2,
        "updated": "2026-05-03",
        "categories": [{"id": "ui", "label": "UI"}],
        "addons": [],
        "client_mods": [],
        "presets": {},
    }))
    cat = loader.load_from_path(src)
    assert cat.addons == []


def test_load_from_path_missing_raises(tmp_path: pathlib.Path):
    with pytest.raises(FileNotFoundError):
        loader.load_from_path(tmp_path / "nope.json")


def test_load_from_path_invalid_json_raises(tmp_path: pathlib.Path):
    src = tmp_path / "bad.json"
    src.write_text("{not json")
    with pytest.raises(loader.CatalogLoadError):
        loader.load_from_path(src)
```

- [ ] **Step 2: Run, confirm fail**

```bash
.venv/bin/pytest tests/test_catalog_loader.py -xvs
```

Expected: ImportError.

- [ ] **Step 3: Implement loader**

`ezwow/catalog/loader.py`:

```python
"""Load catalog data from disk or remote source."""

from __future__ import annotations

import json
import pathlib
from importlib.resources import files

from ezwow.catalog.schema import Catalog, SchemaError, parse_catalog


class CatalogLoadError(RuntimeError):
    """Raised when catalog cannot be loaded or parsed."""


def load_bundled() -> Catalog:
    """Load the catalog shipped inside the package."""
    path = files("ezwow.catalog").joinpath("data/addons.json")
    with path.open("r", encoding="utf-8") as fp:
        raw = json.load(fp)
    try:
        return parse_catalog(raw)
    except SchemaError as exc:
        raise CatalogLoadError(f"bundled catalog invalid: {exc}") from exc


def load_from_path(path: pathlib.Path) -> Catalog:
    """Load and parse a catalog JSON from a filesystem path."""
    if not path.exists():
        raise FileNotFoundError(f"catalog not found at {path}")
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise CatalogLoadError(f"catalog JSON malformed at {path}: {exc}") from exc
    try:
        return parse_catalog(raw)
    except SchemaError as exc:
        raise CatalogLoadError(f"catalog schema invalid at {path}: {exc}") from exc
```

- [ ] **Step 4: Run, confirm pass**

```bash
.venv/bin/pytest tests/test_catalog_loader.py -xvs
```

Expected: 4 passed.

- [ ] **Step 5: Commit**

```bash
git add ezwow/catalog/loader.py tests/test_catalog_loader.py
git commit -m "feat(catalog): add bundled and path-based catalog loaders"
```

---

## Task 7: Remote catalog fetch with ETag cache

**Files:**
- Create: `/home/jalsarraf/git/ezwowaddon/ezwow/catalog/remote.py`
- Create: `/home/jalsarraf/git/ezwowaddon/tests/test_catalog_remote.py`

- [ ] **Step 1: Write failing test**

```python
"""Tests for catalog.remote with HTTP mocked."""

from __future__ import annotations

import pathlib

import pytest
import responses

from ezwow.catalog import remote


REMOTE_URL = (
    "https://raw.githubusercontent.com/jalsarraf0/ezwowaddon/main/catalog/addons.json"
)


@responses.activate
def test_fetch_returns_catalog_when_200(tmp_path: pathlib.Path):
    body = (
        '{"schema_version":2,"updated":"2026-05-03","categories":[],'
        '"addons":[],"client_mods":[],"presets":{}}'
    )
    responses.add(responses.GET, REMOTE_URL, body=body, status=200, headers={"ETag": "abc"})
    cat = remote.fetch_remote(REMOTE_URL, cache_dir=tmp_path)
    assert cat is not None
    assert cat.schema_version == 2
    assert (tmp_path / "remote-catalog.json").exists()
    assert (tmp_path / "remote-catalog.etag").read_text() == "abc"


@responses.activate
def test_fetch_returns_none_on_304(tmp_path: pathlib.Path):
    (tmp_path / "remote-catalog.json").write_text(
        '{"schema_version":2,"updated":"2026-05-03","categories":[],'
        '"addons":[],"client_mods":[],"presets":{}}'
    )
    (tmp_path / "remote-catalog.etag").write_text("abc")
    responses.add(responses.GET, REMOTE_URL, status=304)
    cat = remote.fetch_remote(REMOTE_URL, cache_dir=tmp_path)
    assert cat is not None  # served from cache
    assert cat.schema_version == 2


@responses.activate
def test_fetch_returns_none_on_network_error(tmp_path: pathlib.Path):
    responses.add(
        responses.GET,
        REMOTE_URL,
        body=ConnectionError("boom"),
    )
    assert remote.fetch_remote(REMOTE_URL, cache_dir=tmp_path) is None


@responses.activate
def test_fetch_returns_none_on_500(tmp_path: pathlib.Path):
    responses.add(responses.GET, REMOTE_URL, status=500)
    assert remote.fetch_remote(REMOTE_URL, cache_dir=tmp_path) is None
```

- [ ] **Step 2: Run, confirm fail**

```bash
.venv/bin/pytest tests/test_catalog_remote.py -xvs
```

Expected: ImportError.

- [ ] **Step 3: Implement remote fetch**

`ezwow/catalog/remote.py`:

```python
"""Fetch catalog from a remote URL with ETag-based conditional GET."""

from __future__ import annotations

import json
import logging
import pathlib

import requests

from ezwow.catalog.schema import Catalog, SchemaError, parse_catalog

DEFAULT_REMOTE_URL = (
    "https://raw.githubusercontent.com/jalsarraf0/ezwowaddon/main/catalog/addons.json"
)
TIMEOUT_SECONDS = 10
CACHE_FILE = "remote-catalog.json"
ETAG_FILE = "remote-catalog.etag"

log = logging.getLogger(__name__)


def fetch_remote(url: str = DEFAULT_REMOTE_URL, *, cache_dir: pathlib.Path) -> Catalog | None:
    """Fetch the remote catalog. Returns Catalog on success or cached hit; None on failure."""
    cache_dir.mkdir(parents=True, exist_ok=True)
    cache_path = cache_dir / CACHE_FILE
    etag_path = cache_dir / ETAG_FILE

    headers: dict[str, str] = {}
    if etag_path.exists() and cache_path.exists():
        headers["If-None-Match"] = etag_path.read_text(encoding="utf-8").strip()

    try:
        resp = requests.get(url, headers=headers, timeout=TIMEOUT_SECONDS)
    except (requests.RequestException, OSError) as exc:
        log.warning("remote catalog fetch failed: %s", exc)
        return None

    if resp.status_code == 304 and cache_path.exists():
        return _parse_cached(cache_path)

    if resp.status_code != 200:
        log.warning("remote catalog returned %d", resp.status_code)
        return None

    text = resp.text
    try:
        raw = json.loads(text)
        cat = parse_catalog(raw)
    except (json.JSONDecodeError, SchemaError) as exc:
        log.warning("remote catalog invalid: %s", exc)
        return None

    cache_path.write_text(text, encoding="utf-8")
    new_etag = resp.headers.get("ETag", "").strip()
    etag_path.write_text(new_etag, encoding="utf-8")
    return cat


def _parse_cached(cache_path: pathlib.Path) -> Catalog | None:
    try:
        raw = json.loads(cache_path.read_text(encoding="utf-8"))
        return parse_catalog(raw)
    except (json.JSONDecodeError, SchemaError) as exc:
        log.warning("cached catalog invalid, dropping: %s", exc)
        cache_path.unlink(missing_ok=True)
        return None
```

- [ ] **Step 4: Run, confirm pass**

```bash
.venv/bin/pytest tests/test_catalog_remote.py -xvs
```

Expected: 4 passed.

- [ ] **Step 5: Commit**

```bash
git add ezwow/catalog/remote.py tests/test_catalog_remote.py
git commit -m "feat(catalog): add remote fetch with ETag conditional GET and cache fallback"
```

---

# Phase 3 — Core: Detector + GitHub + Manifest

## Task 8: Folder detector

**Files:**
- Create: `/home/jalsarraf/git/ezwowaddon/ezwow/core/detector.py`
- Create: `/home/jalsarraf/git/ezwowaddon/tests/test_detector.py`

- [ ] **Step 1: Write failing test**

```python
"""Tests for ezwow.core.detector."""

from __future__ import annotations

import pathlib

import pytest

from ezwow.core import detector


def test_find_addons_folder_uses_saved_config(
    tmp_path: pathlib.Path, monkeypatch: pytest.MonkeyPatch
):
    target = tmp_path / "AddOns"
    target.mkdir()
    monkeypatch.setattr(detector, "_candidate_paths", lambda: [])
    found = detector.find_addons_folder(saved=str(target))
    assert found == target


def test_find_addons_folder_falls_back_to_candidates(
    tmp_path: pathlib.Path, monkeypatch: pytest.MonkeyPatch
):
    a = tmp_path / "a" / "Interface" / "AddOns"
    b = tmp_path / "b" / "Interface" / "AddOns"
    b.mkdir(parents=True)  # only b exists
    monkeypatch.setattr(detector, "_candidate_paths", lambda: [a, b])
    assert detector.find_addons_folder(saved=None) == b


def test_find_addons_folder_returns_none_when_nothing(
    monkeypatch: pytest.MonkeyPatch,
):
    monkeypatch.setattr(detector, "_candidate_paths", lambda: [])
    assert detector.find_addons_folder(saved=None) is None


def test_find_data_folder_sibling_of_addons(
    fake_addons_folder: pathlib.Path,
):
    data = detector.find_data_folder(addons=fake_addons_folder)
    assert data is not None
    assert data == fake_addons_folder.parent.parent / "Data"


def test_env_override_turtlewow_home(
    tmp_path: pathlib.Path, monkeypatch: pytest.MonkeyPatch
):
    fake = tmp_path / "TWoW" / "Interface" / "AddOns"
    fake.mkdir(parents=True)
    monkeypatch.setenv("TURTLEWOW_HOME", str(tmp_path / "TWoW"))
    paths = detector._candidate_paths()
    assert fake in paths
```

- [ ] **Step 2: Run, fail**

```bash
.venv/bin/pytest tests/test_detector.py -xvs
```

- [ ] **Step 3: Implement detector**

`ezwow/core/detector.py`:

```python
"""Locate TurtleWoW install folders. Pure path logic + env reads."""

from __future__ import annotations

import os
import pathlib


def _candidate_paths() -> list[pathlib.Path]:
    home = pathlib.Path.home()
    cands: list[pathlib.Path] = []

    if env_home := os.environ.get("TURTLEWOW_HOME"):
        cands.append(pathlib.Path(env_home) / "Interface" / "AddOns")

    if appdata := os.environ.get("APPDATA"):
        cands.append(pathlib.Path(appdata) / "TurtleWoW" / "Interface" / "AddOns")

    cands.append(home / "Games" / "Turtle WoW" / "Interface" / "AddOns")
    cands.append(home / "Games" / "Turtle WoW" / "_classic_" / "Interface" / "AddOns")

    if wineprefix := os.environ.get("WINEPREFIX"):
        cands.append(
            pathlib.Path(wineprefix)
            / "drive_c"
            / "Games"
            / "Turtle WoW"
            / "Interface"
            / "AddOns"
        )
    cands.append(
        home / ".wine" / "drive_c" / "Games" / "Turtle WoW" / "Interface" / "AddOns"
    )

    return cands


def find_addons_folder(*, saved: str | None) -> pathlib.Path | None:
    """Return the AddOns folder, preferring the saved config path."""
    if saved:
        path = pathlib.Path(saved)
        if path.is_dir():
            return path
    for cand in _candidate_paths():
        if cand.is_dir():
            return cand
    return None


def find_data_folder(*, addons: pathlib.Path | None) -> pathlib.Path | None:
    """Given a known AddOns folder, return the sibling Data/ folder."""
    if not addons:
        return None
    data = addons.parent.parent / "Data"
    return data if data.is_dir() else None
```

- [ ] **Step 4: Run, pass**

```bash
.venv/bin/pytest tests/test_detector.py -xvs
```

- [ ] **Step 5: Commit**

```bash
git add ezwow/core/detector.py tests/test_detector.py
git commit -m "feat(core): add folder detector with launcher path + env overrides"
```

---

## Task 9: GitHub API client with rate-limit handling

**Files:**
- Create: `/home/jalsarraf/git/ezwowaddon/ezwow/core/github.py`
- Create: `/home/jalsarraf/git/ezwowaddon/tests/test_github.py`

- [ ] **Step 1: Write failing test**

```python
"""Tests for github API client."""

from __future__ import annotations

import pathlib

import pytest
import responses

from ezwow.core import github as gh


@responses.activate
def test_branch_head_sha_success(tmp_path: pathlib.Path):
    responses.add(
        responses.GET,
        "https://api.github.com/repos/shagu/pfQuest/branches/master",
        json={"commit": {"sha": "abc123"}},
        status=200,
    )
    client = gh.GitHubClient(cache_dir=tmp_path)
    assert client.branch_head_sha("shagu/pfQuest", "master") == "abc123"


@responses.activate
def test_branch_head_sha_uses_cache_on_etag(tmp_path: pathlib.Path):
    responses.add(
        responses.GET,
        "https://api.github.com/repos/x/y/branches/master",
        json={"commit": {"sha": "first"}},
        status=200,
        headers={"ETag": "et1"},
    )
    responses.add(
        responses.GET,
        "https://api.github.com/repos/x/y/branches/master",
        status=304,
    )
    client = gh.GitHubClient(cache_dir=tmp_path)
    assert client.branch_head_sha("x/y", "master") == "first"
    assert client.branch_head_sha("x/y", "master") == "first"


@responses.activate
def test_branch_head_sha_returns_none_on_404(tmp_path: pathlib.Path):
    responses.add(
        responses.GET,
        "https://api.github.com/repos/missing/repo/branches/master",
        status=404,
    )
    client = gh.GitHubClient(cache_dir=tmp_path)
    assert client.branch_head_sha("missing/repo", "master") is None


@responses.activate
def test_latest_release_tag(tmp_path: pathlib.Path):
    responses.add(
        responses.GET,
        "https://api.github.com/repos/x/y/releases/latest",
        json={"tag_name": "v1.2.3", "assets": []},
        status=200,
    )
    client = gh.GitHubClient(cache_dir=tmp_path)
    assert client.latest_release_tag("x/y") == "v1.2.3"


@responses.activate
def test_token_added_when_configured(tmp_path: pathlib.Path):
    responses.add(
        responses.GET,
        "https://api.github.com/repos/x/y/branches/master",
        json={"commit": {"sha": "z"}},
        status=200,
    )
    client = gh.GitHubClient(cache_dir=tmp_path, token="secrettoken")
    client.branch_head_sha("x/y", "master")
    assert "Authorization" in responses.calls[0].request.headers
    assert responses.calls[0].request.headers["Authorization"] == "Bearer secrettoken"
```

- [ ] **Step 2: Run, fail**

```bash
.venv/bin/pytest tests/test_github.py -xvs
```

- [ ] **Step 3: Implement client**

`ezwow/core/github.py`:

```python
"""Lightweight GitHub API client with ETag conditional caching."""

from __future__ import annotations

import json
import logging
import pathlib
from dataclasses import dataclass

import requests

API_ROOT = "https://api.github.com"
TIMEOUT = 10
log = logging.getLogger(__name__)


@dataclass
class _CacheEntry:
    etag: str
    body: dict


class GitHubClient:
    def __init__(self, *, cache_dir: pathlib.Path, token: str | None = None) -> None:
        self.cache_dir = cache_dir
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.token = token
        self.session = requests.Session()

    def _headers(self, etag: str | None) -> dict[str, str]:
        headers = {"Accept": "application/vnd.github+json"}
        if self.token:
            headers["Authorization"] = f"Bearer {self.token}"
        if etag:
            headers["If-None-Match"] = etag
        return headers

    def _cache_path(self, key: str) -> pathlib.Path:
        safe = key.replace("/", "_")
        return self.cache_dir / f"{safe}.json"

    def _read_cache(self, key: str) -> _CacheEntry | None:
        path = self._cache_path(key)
        if not path.exists():
            return None
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
            return _CacheEntry(etag=data["etag"], body=data["body"])
        except (json.JSONDecodeError, KeyError):
            return None

    def _write_cache(self, key: str, entry: _CacheEntry) -> None:
        path = self._cache_path(key)
        path.write_text(
            json.dumps({"etag": entry.etag, "body": entry.body}),
            encoding="utf-8",
        )

    def _get_with_cache(self, key: str, url: str) -> dict | None:
        cached = self._read_cache(key)
        try:
            resp = self.session.get(
                url,
                headers=self._headers(cached.etag if cached else None),
                timeout=TIMEOUT,
            )
        except (requests.RequestException, OSError) as exc:
            log.warning("github GET %s failed: %s", url, exc)
            return cached.body if cached else None
        if resp.status_code == 304 and cached:
            return cached.body
        if resp.status_code == 200:
            try:
                body = resp.json()
            except ValueError:
                log.warning("github returned non-JSON for %s", url)
                return None
            etag = resp.headers.get("ETag", "")
            self._write_cache(key, _CacheEntry(etag=etag, body=body))
            return body
        if resp.status_code == 404:
            return None
        log.warning("github GET %s returned %d", url, resp.status_code)
        return cached.body if cached else None

    def branch_head_sha(self, repo: str, branch: str) -> str | None:
        url = f"{API_ROOT}/repos/{repo}/branches/{branch}"
        body = self._get_with_cache(f"branch:{repo}:{branch}", url)
        if not body:
            return None
        return body.get("commit", {}).get("sha")

    def latest_release_tag(self, repo: str) -> str | None:
        url = f"{API_ROOT}/repos/{repo}/releases/latest"
        body = self._get_with_cache(f"release:{repo}", url)
        if not body:
            return None
        return body.get("tag_name")

    def latest_release_assets(self, repo: str) -> list[dict]:
        url = f"{API_ROOT}/repos/{repo}/releases/latest"
        body = self._get_with_cache(f"release:{repo}", url)
        if not body:
            return []
        return body.get("assets", [])
```

- [ ] **Step 4: Run, pass**

```bash
.venv/bin/pytest tests/test_github.py -xvs
```

- [ ] **Step 5: Commit**

```bash
git add ezwow/core/github.py tests/test_github.py
git commit -m "feat(core): add GitHub client with ETag cache and PAT support"
```

---

## Task 10: Install manifest

**Files:**
- Create: `/home/jalsarraf/git/ezwowaddon/ezwow/core/manifest.py`
- Create: `/home/jalsarraf/git/ezwowaddon/tests/test_manifest.py`

- [ ] **Step 1: Write failing test**

```python
"""Tests for install manifest persistence."""

from __future__ import annotations

import datetime as dt
import pathlib

from ezwow.core import manifest as M


def test_record_and_load_roundtrip(fake_addons_folder: pathlib.Path):
    entry = M.InstallEntry(
        addon_id="pfquest",
        folder="pfQuest",
        source="github:shagu/pfQuest",
        ref="master",
        sha="abc",
        installed_at=dt.datetime(2026, 5, 3, tzinfo=dt.timezone.utc),
        files=("pfQuest/pfQuest.toc",),
        size_bytes=1234,
    )
    M.record(fake_addons_folder, entry)
    loaded = M.load(fake_addons_folder)
    assert "pfquest" in loaded.installs
    assert loaded.installs["pfquest"].sha == "abc"


def test_load_empty_when_missing(fake_addons_folder: pathlib.Path):
    m = M.load(fake_addons_folder)
    assert m.installs == {}


def test_remove_entry(fake_addons_folder: pathlib.Path):
    entry = M.InstallEntry(
        addon_id="x",
        folder="X",
        source="src",
        ref="master",
        sha="s",
        installed_at=dt.datetime(2026, 5, 3, tzinfo=dt.timezone.utc),
        files=(),
        size_bytes=0,
    )
    M.record(fake_addons_folder, entry)
    M.remove(fake_addons_folder, "x")
    assert M.load(fake_addons_folder).installs == {}


def test_corrupt_manifest_resets(fake_addons_folder: pathlib.Path):
    (fake_addons_folder / ".ezwow-manifest.json").write_text("{not json")
    m = M.load(fake_addons_folder)
    assert m.installs == {}
```

- [ ] **Step 2: Run, fail**

- [ ] **Step 3: Implement manifest**

`ezwow/core/manifest.py`:

```python
"""Per-AddOns-folder install manifest stored as `.ezwow-manifest.json`."""

from __future__ import annotations

import datetime as dt
import json
import logging
import pathlib
from dataclasses import asdict, dataclass, field

MANIFEST_FILENAME = ".ezwow-manifest.json"
SCHEMA_VERSION = 1
log = logging.getLogger(__name__)


@dataclass(frozen=True, slots=True)
class InstallEntry:
    addon_id: str
    folder: str
    source: str
    ref: str
    sha: str | None
    installed_at: dt.datetime
    files: tuple[str, ...]
    size_bytes: int


@dataclass
class Manifest:
    schema_version: int = SCHEMA_VERSION
    installs: dict[str, InstallEntry] = field(default_factory=dict)


def _path(addons_folder: pathlib.Path) -> pathlib.Path:
    return addons_folder / MANIFEST_FILENAME


def load(addons_folder: pathlib.Path) -> Manifest:
    path = _path(addons_folder)
    if not path.exists():
        return Manifest()
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        log.warning("manifest at %s corrupt, resetting: %s", path, exc)
        return Manifest()
    installs = {
        k: InstallEntry(
            addon_id=v["addon_id"],
            folder=v["folder"],
            source=v["source"],
            ref=v["ref"],
            sha=v.get("sha"),
            installed_at=dt.datetime.fromisoformat(v["installed_at"]),
            files=tuple(v["files"]),
            size_bytes=int(v["size_bytes"]),
        )
        for k, v in raw.get("installs", {}).items()
    }
    return Manifest(schema_version=raw.get("schema_version", SCHEMA_VERSION), installs=installs)


def save(addons_folder: pathlib.Path, manifest: Manifest) -> None:
    payload = {
        "schema_version": manifest.schema_version,
        "installs": {
            k: {
                **{f: getattr(v, f) for f in ("addon_id", "folder", "source", "ref", "sha")},
                "installed_at": v.installed_at.isoformat(),
                "files": list(v.files),
                "size_bytes": v.size_bytes,
            }
            for k, v in manifest.installs.items()
        },
    }
    _path(addons_folder).write_text(json.dumps(payload, indent=2), encoding="utf-8")


def record(addons_folder: pathlib.Path, entry: InstallEntry) -> None:
    m = load(addons_folder)
    m.installs[entry.addon_id] = entry
    save(addons_folder, m)


def remove(addons_folder: pathlib.Path, addon_id: str) -> None:
    m = load(addons_folder)
    m.installs.pop(addon_id, None)
    save(addons_folder, m)
```

- [ ] **Step 4: Run, pass**

- [ ] **Step 5: Commit**

```bash
git add ezwow/core/manifest.py tests/test_manifest.py
git commit -m "feat(core): add install manifest with .ezwow-manifest.json persistence"
```

---

# Phase 4 — Core: Installer + Backup + Updater + Deps + Profiles

## Task 11: Atomic installer

**Files:**
- Create: `/home/jalsarraf/git/ezwowaddon/ezwow/core/installer.py`
- Create: `/home/jalsarraf/git/ezwowaddon/tests/test_installer.py`
- Create: `/home/jalsarraf/git/ezwowaddon/tests/data/sample-addon-master.zip` (binary fixture)

- [ ] **Step 1: Create the fixture zip**

```bash
cd /tmp
mkdir -p sample-addon-master/SampleAddon
cat > sample-addon-master/SampleAddon/SampleAddon.toc <<'EOF'
## Interface: 11200
## Title: Sample Addon
## Notes: Test fixture for installer
SampleAddon.lua
EOF
cat > sample-addon-master/SampleAddon/SampleAddon.lua <<'EOF'
-- minimal lua
EOF
cd /tmp && zip -r /home/jalsarraf/git/ezwowaddon/tests/data/sample-addon-master.zip sample-addon-master
```

Verify:

```bash
unzip -l /home/jalsarraf/git/ezwowaddon/tests/data/sample-addon-master.zip
```

Expected: shows `sample-addon-master/SampleAddon/SampleAddon.toc` etc.

- [ ] **Step 2: Write failing test**

```python
"""Tests for atomic install/extract."""

from __future__ import annotations

import http.server
import pathlib
import socketserver
import threading
from typing import Iterator

import pytest

from ezwow.catalog.schema import Addon
from ezwow.core import installer
from ezwow.core.installer import InstallError


@pytest.fixture
def http_fixture(tmp_path: pathlib.Path) -> Iterator[str]:
    """Serve tests/data/ via http on a random port."""
    docroot = pathlib.Path(__file__).parent / "data"

    class Handler(http.server.SimpleHTTPRequestHandler):
        def __init__(self, *a, **kw):
            super().__init__(*a, directory=str(docroot), **kw)

        def log_message(self, *_):
            pass

    with socketserver.TCPServer(("127.0.0.1", 0), Handler) as srv:
        port = srv.server_address[1]
        thread = threading.Thread(target=srv.serve_forever, daemon=True)
        thread.start()
        try:
            yield f"http://127.0.0.1:{port}"
        finally:
            srv.shutdown()


def _addon(url: str) -> Addon:
    return Addon(
        id="sample",
        name="Sample",
        category="utility",
        description="d",
        author="a",
        github="x/y",
        branch="master",
        folder="SampleAddon",
    )


def test_install_extracts_to_target_folder(
    http_fixture: str, fake_addons_folder: pathlib.Path
):
    addon = _addon(http_fixture)
    installer.install_from_url(
        url=f"{http_fixture}/sample-addon-master.zip",
        addons_folder=fake_addons_folder,
        target_folder_name="SampleAddon",
    )
    assert (fake_addons_folder / "SampleAddon" / "SampleAddon.toc").exists()


def test_install_replaces_existing_folder(
    http_fixture: str, fake_addons_folder: pathlib.Path
):
    target = fake_addons_folder / "SampleAddon"
    target.mkdir()
    (target / "stale.lua").write_text("old")
    installer.install_from_url(
        url=f"{http_fixture}/sample-addon-master.zip",
        addons_folder=fake_addons_folder,
        target_folder_name="SampleAddon",
    )
    assert not (target / "stale.lua").exists()
    assert (target / "SampleAddon.toc").exists()


def test_install_404_raises_install_error(
    http_fixture: str, fake_addons_folder: pathlib.Path
):
    with pytest.raises(InstallError, match="404"):
        installer.install_from_url(
            url=f"{http_fixture}/missing.zip",
            addons_folder=fake_addons_folder,
            target_folder_name="SampleAddon",
        )
    assert not (fake_addons_folder / "SampleAddon").exists()


def test_install_rejects_zip_slip(
    tmp_path: pathlib.Path, fake_addons_folder: pathlib.Path, monkeypatch
):
    """Zip-slip: a member path containing .. must be rejected."""
    import zipfile

    bad = tmp_path / "evil.zip"
    with zipfile.ZipFile(bad, "w") as zf:
        zf.writestr("evil-master/../escape.txt", "boom")
    # use file:// URL via http fixture is overkill — just call the extract helper directly
    with pytest.raises(InstallError, match="zip slip"):
        installer._extract_zip_atomic(
            zip_bytes=bad.read_bytes(),
            target_root=fake_addons_folder,
            folder_name="evil",
        )
```

- [ ] **Step 3: Run, fail**

- [ ] **Step 4: Implement installer**

`ezwow/core/installer.py`:

```python
"""Download → extract → place addons atomically."""

from __future__ import annotations

import io
import logging
import pathlib
import shutil
import tempfile
import zipfile
from dataclasses import dataclass

import requests

DOWNLOAD_TIMEOUT = 60
log = logging.getLogger(__name__)


class InstallError(RuntimeError):
    """Raised when install fails (download, extract, or place)."""


@dataclass(slots=True)
class InstallResult:
    folder: str
    files: tuple[str, ...]
    size_bytes: int


def install_from_url(
    *, url: str, addons_folder: pathlib.Path, target_folder_name: str
) -> InstallResult:
    log.info("downloading %s", url)
    try:
        resp = requests.get(url, timeout=DOWNLOAD_TIMEOUT, stream=True)
    except requests.RequestException as exc:
        raise InstallError(f"download failed: {exc}") from exc
    if resp.status_code != 200:
        raise InstallError(f"download failed: HTTP {resp.status_code} from {url}")
    return _extract_zip_atomic(
        zip_bytes=resp.content,
        target_root=addons_folder,
        folder_name=target_folder_name,
    )


def _extract_zip_atomic(
    *, zip_bytes: bytes, target_root: pathlib.Path, folder_name: str
) -> InstallResult:
    target_root = target_root.resolve()
    final_dir = target_root / folder_name

    try:
        zf = zipfile.ZipFile(io.BytesIO(zip_bytes))
    except zipfile.BadZipFile as exc:
        raise InstallError(f"corrupt zip: {exc}") from exc

    members = [m for m in zf.namelist() if not m.endswith("/")]
    if not members:
        raise InstallError("zip contains no files")

    top_level = members[0].split("/", 1)[0]

    for m in zf.namelist():
        # zip-slip guard
        if ".." in m.split("/") or m.startswith("/"):
            raise InstallError(f"zip slip detected: {m!r}")

    with tempfile.TemporaryDirectory(dir=target_root) as staging:
        staging_path = pathlib.Path(staging)
        zf.extractall(staging_path)
        extracted_root = staging_path / top_level
        if not extracted_root.is_dir():
            raise InstallError(f"expected top-level dir {top_level!r} not in zip")

        if final_dir.exists():
            shutil.rmtree(final_dir)
        shutil.move(str(extracted_root), str(final_dir))

    files: list[str] = []
    size = 0
    for path in final_dir.rglob("*"):
        if path.is_file():
            rel = str(path.relative_to(target_root))
            files.append(rel)
            size += path.stat().st_size

    return InstallResult(folder=folder_name, files=tuple(sorted(files)), size_bytes=size)
```

- [ ] **Step 5: Run, pass**

```bash
.venv/bin/pytest tests/test_installer.py -xvs
```

- [ ] **Step 6: Commit**

```bash
git add ezwow/core/installer.py tests/test_installer.py tests/data/sample-addon-master.zip
git commit -m "feat(core): add atomic installer with zip-slip guard and integration tests"
```

---

## Task 12: Backup / restore

**Files:**
- Create: `/home/jalsarraf/git/ezwowaddon/ezwow/core/backup.py`
- Create: `/home/jalsarraf/git/ezwowaddon/tests/test_backup.py`

- [ ] **Step 1: Write failing test**

```python
"""Tests for backup/restore."""

from __future__ import annotations

import pathlib

from ezwow.core import backup


def test_create_and_restore_roundtrip(
    fake_wow_root: pathlib.Path, tmp_path: pathlib.Path
):
    addons = fake_wow_root / "Interface" / "AddOns"
    (addons / "FooAddon").mkdir()
    (addons / "FooAddon" / "Foo.toc").write_text("hello")
    wtf_dir = fake_wow_root / "WTF" / "Account" / "TEST" / "SavedVariables"
    (wtf_dir / "FooAddon.lua").write_text("saved=1")

    out_dir = tmp_path / "backups"
    archive = backup.create_backup(wow_root=fake_wow_root, out_dir=out_dir)
    assert archive.exists()
    assert archive.suffix == ".gz"

    # destroy
    (addons / "FooAddon" / "Foo.toc").unlink()
    (wtf_dir / "FooAddon.lua").unlink()

    backup.restore_backup(archive=archive, wow_root=fake_wow_root)
    assert (addons / "FooAddon" / "Foo.toc").read_text() == "hello"
    assert (wtf_dir / "FooAddon.lua").read_text() == "saved=1"


def test_create_skips_when_addons_missing(tmp_path: pathlib.Path):
    import pytest

    with pytest.raises(backup.BackupError):
        backup.create_backup(
            wow_root=tmp_path / "nope",
            out_dir=tmp_path / "out",
        )
```

- [ ] **Step 2: Run, fail**

- [ ] **Step 3: Implement backup**

`ezwow/core/backup.py`:

```python
"""tar.gz backup and restore of AddOns + SavedVariables."""

from __future__ import annotations

import datetime as dt
import logging
import pathlib
import tarfile

log = logging.getLogger(__name__)


class BackupError(RuntimeError):
    """Raised on backup or restore failure."""


def _timestamp() -> str:
    return dt.datetime.now(dt.timezone.utc).strftime("%Y%m%dT%H%M%SZ")


def create_backup(*, wow_root: pathlib.Path, out_dir: pathlib.Path) -> pathlib.Path:
    addons = wow_root / "Interface" / "AddOns"
    wtf = wow_root / "WTF"
    if not addons.is_dir():
        raise BackupError(f"AddOns folder missing at {addons}")

    out_dir.mkdir(parents=True, exist_ok=True)
    archive = out_dir / f"ezwow-backup-{_timestamp()}.tar.gz"
    with tarfile.open(archive, "w:gz") as tar:
        tar.add(addons, arcname="Interface/AddOns")
        if wtf.is_dir():
            tar.add(wtf, arcname="WTF")
    log.info("backup written to %s", archive)
    return archive


def restore_backup(*, archive: pathlib.Path, wow_root: pathlib.Path) -> None:
    if not archive.exists():
        raise BackupError(f"archive not found at {archive}")
    with tarfile.open(archive, "r:gz") as tar:
        for member in tar.getmembers():
            if ".." in member.name.split("/") or member.name.startswith("/"):
                raise BackupError(f"unsafe path in archive: {member.name!r}")
        tar.extractall(wow_root, filter="data")
    log.info("restored from %s", archive)
```

- [ ] **Step 4: Run, pass**

- [ ] **Step 5: Commit**

```bash
git add ezwow/core/backup.py tests/test_backup.py
git commit -m "feat(core): add tar.gz backup and restore for AddOns + SavedVariables"
```

---

## Task 13: Dependency resolver

**Files:**
- Create: `/home/jalsarraf/git/ezwowaddon/ezwow/core/deps.py`
- Create: `/home/jalsarraf/git/ezwowaddon/tests/test_deps.py`

- [ ] **Step 1: Write failing test**

```python
"""Tests for dependency resolution."""

from __future__ import annotations

import pytest

from ezwow.catalog.schema import Addon, Catalog, Category
from ezwow.core import deps


def _make_catalog(addons: list[Addon]) -> Catalog:
    return Catalog(
        schema_version=2,
        updated="2026-05-03",
        categories=[Category(id="x", label="X")],
        addons=addons,
        client_mods=[],
        presets={},
    )


def _addon(id_: str, depends: tuple[str, ...] = ()) -> Addon:
    return Addon(
        id=id_,
        name=id_,
        category="x",
        description="",
        author="",
        github="x/y",
        folder=id_,
        depends=depends,
    )


def test_resolve_no_deps():
    cat = _make_catalog([_addon("a")])
    assert deps.resolve(["a"], cat) == ["a"]


def test_resolve_topo_order():
    cat = _make_catalog([
        _addon("a", ()),
        _addon("b", ("a",)),
        _addon("c", ("b",)),
    ])
    assert deps.resolve(["c"], cat) == ["a", "b", "c"]


def test_resolve_pulls_transitive():
    cat = _make_catalog([
        _addon("base", ()),
        _addon("ext", ("base",)),
    ])
    out = deps.resolve(["ext"], cat)
    assert out == ["base", "ext"]


def test_resolve_dedupes_when_already_in_input():
    cat = _make_catalog([_addon("a"), _addon("b", ("a",))])
    assert deps.resolve(["a", "b"], cat) == ["a", "b"]


def test_resolve_raises_on_cycle():
    cat = _make_catalog([
        _addon("a", ("b",)),
        _addon("b", ("a",)),
    ])
    with pytest.raises(deps.CycleError):
        deps.resolve(["a"], cat)


def test_resolve_raises_on_unknown():
    cat = _make_catalog([_addon("a")])
    with pytest.raises(KeyError):
        deps.resolve(["unknown"], cat)
```

- [ ] **Step 2: Run, fail**

- [ ] **Step 3: Implement**

`ezwow/core/deps.py`:

```python
"""Topologically resolve addon dependencies."""

from __future__ import annotations

from ezwow.catalog.schema import Catalog


class CycleError(RuntimeError):
    """Raised when the dependency graph contains a cycle."""


def resolve(addon_ids: list[str], catalog: Catalog) -> list[str]:
    """Return addon_ids in dependency-first install order. Pulls transitive deps."""
    by_id = {a.id: a for a in catalog.addons}
    for aid in addon_ids:
        if aid not in by_id:
            raise KeyError(f"unknown addon id {aid!r}")

    ordered: list[str] = []
    visited: set[str] = set()
    on_stack: set[str] = set()

    def visit(aid: str, stack: tuple[str, ...]) -> None:
        if aid in visited:
            return
        if aid in on_stack:
            cycle = " -> ".join((*stack, aid))
            raise CycleError(f"dependency cycle: {cycle}")
        if aid not in by_id:
            raise KeyError(f"unknown addon id {aid!r}")
        on_stack.add(aid)
        for dep in by_id[aid].depends:
            visit(dep, (*stack, aid))
        on_stack.discard(aid)
        visited.add(aid)
        ordered.append(aid)

    for aid in addon_ids:
        visit(aid, ())
    return ordered
```

- [ ] **Step 4: Run, pass**

- [ ] **Step 5: Commit**

```bash
git add ezwow/core/deps.py tests/test_deps.py
git commit -m "feat(core): add dependency resolver with cycle detection"
```

---

## Task 14: Updater

**Files:**
- Create: `/home/jalsarraf/git/ezwowaddon/ezwow/core/updater.py`
- Create: `/home/jalsarraf/git/ezwowaddon/tests/test_updater.py`

- [ ] **Step 1: Write failing test**

```python
"""Tests for updater plan generation."""

from __future__ import annotations

import datetime as dt
import pathlib
from unittest.mock import MagicMock

from ezwow.catalog.schema import Addon, Catalog, Category
from ezwow.core import manifest as M
from ezwow.core import updater


def _cat(addons: list[Addon]) -> Catalog:
    return Catalog(
        schema_version=2,
        updated="2026-05-03",
        categories=[Category(id="x", label="X")],
        addons=addons,
        client_mods=[],
        presets={},
    )


def _entry(addon_id: str, sha: str | None) -> M.InstallEntry:
    return M.InstallEntry(
        addon_id=addon_id,
        folder=addon_id,
        source=f"github:x/{addon_id}",
        ref="master",
        sha=sha,
        installed_at=dt.datetime(2026, 5, 3, tzinfo=dt.timezone.utc),
        files=(),
        size_bytes=0,
    )


def test_plan_marks_outdated_branch_install(fake_addons_folder: pathlib.Path):
    addon = Addon(
        id="a", name="A", category="x", description="", author="", github="x/a", folder="A"
    )
    M.record(fake_addons_folder, _entry("a", "old-sha"))

    gh = MagicMock()
    gh.branch_head_sha.return_value = "new-sha"

    plan = updater.plan(
        addons_folder=fake_addons_folder, catalog=_cat([addon]), gh_client=gh
    )
    assert [u.addon_id for u in plan.updates] == ["a"]
    assert plan.updates[0].current == "old-sha"
    assert plan.updates[0].latest == "new-sha"


def test_plan_skips_uptodate(fake_addons_folder: pathlib.Path):
    addon = Addon(
        id="a", name="A", category="x", description="", author="", github="x/a", folder="A"
    )
    M.record(fake_addons_folder, _entry("a", "same"))
    gh = MagicMock()
    gh.branch_head_sha.return_value = "same"
    plan = updater.plan(
        addons_folder=fake_addons_folder, catalog=_cat([addon]), gh_client=gh
    )
    assert plan.updates == []


def test_plan_with_unknown_sha_marks_for_update(fake_addons_folder: pathlib.Path):
    addon = Addon(
        id="a", name="A", category="x", description="", author="", github="x/a", folder="A"
    )
    M.record(fake_addons_folder, _entry("a", None))
    gh = MagicMock()
    gh.branch_head_sha.return_value = "anything"
    plan = updater.plan(
        addons_folder=fake_addons_folder, catalog=_cat([addon]), gh_client=gh
    )
    assert plan.updates[0].current is None
```

- [ ] **Step 2: Run, fail**

- [ ] **Step 3: Implement**

`ezwow/core/updater.py`:

```python
"""Compare installed addon SHAs against upstream."""

from __future__ import annotations

import pathlib
from dataclasses import dataclass

from ezwow.catalog.schema import Catalog
from ezwow.core import manifest as M
from ezwow.core.github import GitHubClient


@dataclass(frozen=True, slots=True)
class PendingUpdate:
    addon_id: str
    current: str | None
    latest: str | None


@dataclass(frozen=True, slots=True)
class UpdatePlan:
    updates: list[PendingUpdate]


def plan(
    *,
    addons_folder: pathlib.Path,
    catalog: Catalog,
    gh_client: GitHubClient,
) -> UpdatePlan:
    manifest = M.load(addons_folder)
    pending: list[PendingUpdate] = []
    for addon_id, entry in manifest.installs.items():
        addon = catalog.addon_by_id(addon_id)
        if not addon:
            continue
        if addon.use_releases:
            latest = gh_client.latest_release_tag(addon.github)
        else:
            latest = gh_client.branch_head_sha(addon.github, addon.branch)
        if latest is None:
            continue
        if entry.sha != latest:
            pending.append(
                PendingUpdate(addon_id=addon_id, current=entry.sha, latest=latest)
            )
    return UpdatePlan(updates=pending)
```

- [ ] **Step 4: Run, pass**

- [ ] **Step 5: Commit**

```bash
git add ezwow/core/updater.py tests/test_updater.py
git commit -m "feat(core): add updater that produces UpdatePlan from manifest vs upstream"
```

---

## Task 15: Profile apply / export / import

**Files:**
- Create: `/home/jalsarraf/git/ezwowaddon/ezwow/core/profile.py`
- Create: `/home/jalsarraf/git/ezwowaddon/tests/test_profile.py`

- [ ] **Step 1: Write failing test**

```python
"""Tests for profile import/export."""

from __future__ import annotations

import json
import pathlib

from ezwow.catalog.schema import Addon, Catalog, Category, Preset
from ezwow.core import profile


def _cat() -> Catalog:
    return Catalog(
        schema_version=2,
        updated="2026-05-03",
        categories=[Category(id="x", label="X")],
        addons=[
            Addon(id="a", name="A", category="x", description="", author="", github="x/a", folder="A"),
            Addon(id="b", name="B", category="x", description="", author="", github="x/b", folder="B"),
        ],
        client_mods=[],
        presets={"p": Preset(id="p", label="P", addons=("a", "b"))},
    )


def test_resolve_preset_returns_addon_ids():
    cat = _cat()
    plan = profile.resolve_preset("p", cat)
    assert plan.addon_ids == ["a", "b"]


def test_export_profile_writes_json(tmp_path: pathlib.Path):
    out = tmp_path / "profile.json"
    profile.export_profile(
        out_path=out, addon_ids=["a", "b"], client_mod_ids=[], label="custom"
    )
    raw = json.loads(out.read_text())
    assert raw["label"] == "custom"
    assert raw["addons"] == ["a", "b"]


def test_import_profile_returns_lists(tmp_path: pathlib.Path):
    src = tmp_path / "profile.json"
    src.write_text(
        json.dumps({"label": "x", "addons": ["a"], "client_mods": ["b"]})
    )
    p = profile.import_profile(src)
    assert p.label == "x"
    assert p.addons == ["a"]
    assert p.client_mods == ["b"]
```

- [ ] **Step 2: Run, fail**

- [ ] **Step 3: Implement**

`ezwow/core/profile.py`:

```python
"""Apply presets and export/import custom profiles."""

from __future__ import annotations

import json
import pathlib
from dataclasses import dataclass

from ezwow.catalog.schema import Catalog


@dataclass(frozen=True, slots=True)
class ResolvedPreset:
    addon_ids: list[str]
    client_mod_ids: list[str]


@dataclass(frozen=True, slots=True)
class Profile:
    label: str
    addons: list[str]
    client_mods: list[str]


def resolve_preset(preset_id: str, catalog: Catalog) -> ResolvedPreset:
    preset = catalog.presets.get(preset_id)
    if preset is None:
        raise KeyError(f"unknown preset {preset_id!r}")
    return ResolvedPreset(
        addon_ids=list(preset.addons),
        client_mod_ids=list(preset.client_mods),
    )


def export_profile(
    *,
    out_path: pathlib.Path,
    addon_ids: list[str],
    client_mod_ids: list[str],
    label: str,
) -> None:
    out_path.write_text(
        json.dumps(
            {"label": label, "addons": addon_ids, "client_mods": client_mod_ids},
            indent=2,
        ),
        encoding="utf-8",
    )


def import_profile(path: pathlib.Path) -> Profile:
    raw = json.loads(path.read_text(encoding="utf-8"))
    return Profile(
        label=raw.get("label", "(unnamed)"),
        addons=list(raw.get("addons", [])),
        client_mods=list(raw.get("client_mods", [])),
    )
```

- [ ] **Step 4: Run, pass**

- [ ] **Step 5: Commit**

```bash
git add ezwow/core/profile.py tests/test_profile.py
git commit -m "feat(core): add preset resolver and profile export/import"
```

---

## Task 16: Coverage gate check

- [ ] **Step 1: Run coverage**

```bash
.venv/bin/pytest --cov=ezwow.core --cov-fail-under=70
```

Expected: PASS, ≥70% on `ezwow.core`. If failing, identify gap and add a focused unit test before continuing.

- [ ] **Step 2: Commit any added tests**

```bash
git add tests/
git commit -m "test(core): raise coverage to 70% on ezwow.core" || true
```

---

# Phase 5 — CLI

## Task 17: argparse CLI

**Files:**
- Replace stub: `/home/jalsarraf/git/ezwowaddon/ezwow/cli.py`
- Create: `/home/jalsarraf/git/ezwowaddon/tests/test_cli.py`

- [ ] **Step 1: Write failing test**

```python
"""End-to-end tests for the CLI surface."""

from __future__ import annotations

import json
import pathlib
from unittest.mock import patch

import pytest

from ezwow.catalog.schema import Catalog, parse_catalog
from ezwow.cli import run


@pytest.fixture
def fake_catalog(monkeypatch: pytest.MonkeyPatch):
    raw = {
        "schema_version": 2,
        "updated": "2026-05-03",
        "categories": [{"id": "x", "label": "X"}],
        "addons": [
            {"id": "a", "name": "A", "category": "x", "description": "d",
             "author": "u", "github": "x/a", "folder": "A"},
        ],
        "client_mods": [],
        "presets": {"p": {"label": "P", "addons": ["a"], "client_mods": []}},
    }
    cat = parse_catalog(raw)
    monkeypatch.setattr("ezwow.catalog.loader.load_bundled", lambda: cat)
    return cat


def test_cli_list_prints_addon_ids(capsys, fake_catalog: Catalog):
    rc = run(["list"])
    assert rc == 0
    out = capsys.readouterr().out
    assert "a" in out


def test_cli_unknown_command_returns_error(capsys, fake_catalog: Catalog):
    rc = run(["frobnicate"])
    assert rc != 0


def test_cli_doctor_prints_paths(
    capsys, fake_catalog: Catalog, isolated_config: pathlib.Path
):
    rc = run(["doctor"])
    assert rc == 0
    out = capsys.readouterr().out
    assert "config" in out.lower()
```

- [ ] **Step 2: Run, fail**

- [ ] **Step 3: Implement CLI**

`ezwow/cli.py`:

```python
"""Headless command-line interface for ezwowaddon."""

from __future__ import annotations

import argparse
import datetime as dt
import logging
import pathlib
import sys
from collections.abc import Sequence

from ezwow import __version__, config
from ezwow.catalog import loader as catalog_loader
from ezwow.core import (
    backup,
    deps,
    detector,
    github,
    installer,
    manifest,
    profile,
    updater,
)


def _build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="ezwow",
        description=f"EZWowAddon {__version__} — Turtle WoW addon manager",
    )
    p.add_argument("--gui", "-g", action="store_true", help="launch the graphical UI")
    sub = p.add_subparsers(dest="cmd")

    sp = sub.add_parser("list", help="list addons")
    sp.add_argument("--installed", action="store_true")
    sp.add_argument("--updates", action="store_true")

    sp = sub.add_parser("install", help="install one or more addons by id")
    sp.add_argument("ids", nargs="*")
    sp.add_argument("--preset", help="apply a preset by id")

    sp = sub.add_parser("update", help="update addons")
    sp.add_argument("ids", nargs="*")
    sp.add_argument("--all", action="store_true")

    sp = sub.add_parser("remove", help="uninstall an addon")
    sp.add_argument("id")

    sp = sub.add_parser("backup", help="snapshot AddOns + SavedVariables")
    sp.add_argument("--out", default=None)

    sp = sub.add_parser("restore", help="restore from a backup")
    sp.add_argument("path")

    sp = sub.add_parser("profile", help="export/import profiles")
    sp.add_argument("action", choices=("export", "import"))
    sp.add_argument("path")

    sub.add_parser("doctor", help="diagnostic info")

    return p


def run(argv: Sequence[str]) -> int:
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")
    parser = _build_parser()
    args = parser.parse_args(list(argv))

    if args.cmd is None:
        parser.print_help()
        return 1

    if args.cmd == "list":
        return _cmd_list(args)
    if args.cmd == "install":
        return _cmd_install(args)
    if args.cmd == "update":
        return _cmd_update(args)
    if args.cmd == "remove":
        return _cmd_remove(args)
    if args.cmd == "backup":
        return _cmd_backup(args)
    if args.cmd == "restore":
        return _cmd_restore(args)
    if args.cmd == "profile":
        return _cmd_profile(args)
    if args.cmd == "doctor":
        return _cmd_doctor()
    return 1


def _addons_folder(cfg: config.UserConfig) -> pathlib.Path | None:
    return detector.find_addons_folder(saved=cfg.addons_folder)


def _cmd_list(args: argparse.Namespace) -> int:
    cat = catalog_loader.load_bundled()
    cfg = config.load()
    folder = _addons_folder(cfg)

    if args.installed:
        if not folder:
            print("AddOns folder not configured", file=sys.stderr)
            return 3
        m = manifest.load(folder)
        for inst in sorted(m.installs.values(), key=lambda i: i.addon_id):
            print(f"{inst.addon_id:30s}  ref={inst.ref}  sha={(inst.sha or 'unknown')[:7]}")
        return 0

    if args.updates:
        if not folder:
            print("AddOns folder not configured", file=sys.stderr)
            return 3
        gh = github.GitHubClient(cache_dir=config.cache_dir(), token=cfg.github_pat)
        plan = updater.plan(addons_folder=folder, catalog=cat, gh_client=gh)
        for u in plan.updates:
            print(f"{u.addon_id:30s}  {(u.current or '?')[:7]} -> {(u.latest or '?')[:7]}")
        return 0

    by_cat: dict[str, list[str]] = {}
    for a in cat.addons:
        by_cat.setdefault(a.category, []).append(a.id)
    for cat_id in sorted(by_cat):
        print(f"\n[{cat_id}]")
        for aid in sorted(by_cat[cat_id]):
            print(f"  {aid}")
    return 0


def _cmd_install(args: argparse.Namespace) -> int:
    cat = catalog_loader.load_bundled()
    cfg = config.load()
    folder = _addons_folder(cfg)
    if not folder:
        print("AddOns folder not configured", file=sys.stderr)
        return 3

    requested: list[str] = list(args.ids)
    if args.preset:
        resolved = profile.resolve_preset(args.preset, cat)
        requested.extend(resolved.addon_ids)

    if not requested:
        print("nothing to install (provide ids or --preset)", file=sys.stderr)
        return 1

    try:
        ordered = deps.resolve(requested, cat)
    except (deps.CycleError, KeyError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 4

    gh = github.GitHubClient(cache_dir=config.cache_dir(), token=cfg.github_pat)
    for aid in ordered:
        addon = cat.addon_by_id(aid)
        assert addon is not None
        url = addon.branch_zip_url()
        print(f"installing {aid} from {url}")
        try:
            result = installer.install_from_url(
                url=url, addons_folder=folder, target_folder_name=addon.folder
            )
        except installer.InstallError as exc:
            print(f"error installing {aid}: {exc}", file=sys.stderr)
            return 2
        sha = gh.branch_head_sha(addon.github, addon.branch)
        manifest.record(
            folder,
            manifest.InstallEntry(
                addon_id=aid,
                folder=addon.folder,
                source=f"github:{addon.github}",
                ref=addon.branch,
                sha=sha,
                installed_at=dt.datetime.now(dt.timezone.utc),
                files=result.files,
                size_bytes=result.size_bytes,
            ),
        )
    return 0


def _cmd_update(args: argparse.Namespace) -> int:
    cat = catalog_loader.load_bundled()
    cfg = config.load()
    folder = _addons_folder(cfg)
    if not folder:
        return 3
    gh = github.GitHubClient(cache_dir=config.cache_dir(), token=cfg.github_pat)
    plan = updater.plan(addons_folder=folder, catalog=cat, gh_client=gh)
    targets: list[str] = []
    if args.all:
        targets = [u.addon_id for u in plan.updates]
    else:
        wanted = set(args.ids)
        targets = [u.addon_id for u in plan.updates if u.addon_id in wanted]
    if not targets:
        print("nothing to update")
        return 0
    return _cmd_install(argparse.Namespace(ids=targets, preset=None))


def _cmd_remove(args: argparse.Namespace) -> int:
    import shutil

    cfg = config.load()
    folder = _addons_folder(cfg)
    if not folder:
        return 3
    m = manifest.load(folder)
    entry = m.installs.get(args.id)
    if entry is None:
        print(f"{args.id} not installed", file=sys.stderr)
        return 1
    target = folder / entry.folder
    if target.is_dir():
        shutil.rmtree(target)
    manifest.remove(folder, args.id)
    print(f"removed {args.id}")
    return 0


def _cmd_backup(args: argparse.Namespace) -> int:
    cfg = config.load()
    folder = _addons_folder(cfg)
    if not folder:
        return 3
    wow_root = folder.parent.parent
    out_dir = pathlib.Path(args.out) if args.out else config.data_dir() / "backups"
    archive = backup.create_backup(wow_root=wow_root, out_dir=out_dir)
    print(archive)
    return 0


def _cmd_restore(args: argparse.Namespace) -> int:
    cfg = config.load()
    folder = _addons_folder(cfg)
    if not folder:
        return 3
    backup.restore_backup(archive=pathlib.Path(args.path), wow_root=folder.parent.parent)
    return 0


def _cmd_profile(args: argparse.Namespace) -> int:
    cfg = config.load()
    folder = _addons_folder(cfg)
    if not folder:
        return 3
    if args.action == "export":
        m = manifest.load(folder)
        ids = sorted(m.installs.keys())
        profile.export_profile(
            out_path=pathlib.Path(args.path),
            addon_ids=ids,
            client_mod_ids=[],
            label="user-export",
        )
        return 0
    p = profile.import_profile(pathlib.Path(args.path))
    return _cmd_install(argparse.Namespace(ids=p.addons, preset=None))


def _cmd_doctor() -> int:
    cfg = config.load()
    folder = detector.find_addons_folder(saved=cfg.addons_folder)
    print(f"version       {__version__}")
    print(f"config        {config.config_path()}")
    print(f"cache         {config.cache_dir()}")
    print(f"data          {config.data_dir()}")
    print(f"addons folder {folder or '(not found)'}")
    if folder:
        m = manifest.load(folder)
        print(f"installs      {len(m.installs)}")
    return 0
```

- [ ] **Step 4: Run, pass**

```bash
.venv/bin/pytest tests/test_cli.py -xvs
```

- [ ] **Step 5: Commit**

```bash
git add ezwow/cli.py tests/test_cli.py
git commit -m "feat(cli): add argparse-based CLI mirroring all core operations"
```

---

# Phase 6 — UI (CustomTkinter)

## Task 18: UI app shell + theme

**Files:**
- Replace stub: `/home/jalsarraf/git/ezwowaddon/ezwow/ui/app.py`
- Create: `/home/jalsarraf/git/ezwowaddon/ezwow/ui/widgets/notification.py`

UI tests are smoke-only (headless Tk requires xvfb on Linux). Keep tests minimal; rely on CLI parity for behaviour coverage.

- [ ] **Step 1: Implement `ezwow/ui/app.py`**

```python
"""Main CustomTkinter window. Behaviour-thin: delegates to core.*"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

import customtkinter as ctk

from ezwow import __version__, config
from ezwow.catalog import loader as catalog_loader
from ezwow.core import detector

if TYPE_CHECKING:
    from ezwow.catalog.schema import Catalog


log = logging.getLogger(__name__)


class App(ctk.CTk):
    def __init__(self) -> None:
        super().__init__()
        self.title(f"EZWowAddon {__version__}")
        self.geometry("960x640")
        self.minsize(800, 540)

        self.cfg = config.load()
        ctk.set_appearance_mode(self.cfg.theme)
        ctk.set_default_color_theme("blue")

        self.catalog: Catalog = catalog_loader.load_bundled()
        self.addons_folder = detector.find_addons_folder(saved=self.cfg.addons_folder)

        self._build_layout()

    def _build_layout(self) -> None:
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        nav = ctk.CTkFrame(self, width=180, corner_radius=0)
        nav.grid(row=0, column=0, sticky="nsw")
        nav.grid_propagate(False)

        self.tabs: dict[str, ctk.CTkFrame] = {}
        self._add_tab(nav, "Browse", self._make_browse)
        self._add_tab(nav, "Installed", self._make_installed)
        self._add_tab(nav, "Updates", self._make_updates)
        self._add_tab(nav, "Client Mods", self._make_client_mods)
        self._add_tab(nav, "Profiles", self._make_profiles)
        self._add_tab(nav, "Settings", self._make_settings)

        self.content = ctk.CTkFrame(self, corner_radius=0)
        self.content.grid(row=0, column=1, sticky="nsew")
        self.content.grid_columnconfigure(0, weight=1)
        self.content.grid_rowconfigure(0, weight=1)

        self.status = ctk.CTkLabel(self, text="Ready.", anchor="w")
        self.status.grid(row=1, column=0, columnspan=2, sticky="ew", padx=8, pady=4)

        self._show_tab("Browse")

    def _add_tab(self, parent: ctk.CTkFrame, label: str, factory) -> None:
        btn = ctk.CTkButton(
            parent,
            text=label,
            anchor="w",
            command=lambda: self._show_tab(label),
        )
        btn.pack(fill="x", padx=8, pady=4)
        self.tabs[label] = factory()

    def _show_tab(self, label: str) -> None:
        for child in self.content.winfo_children():
            child.grid_forget()
        frame = self.tabs[label]
        frame.grid(in_=self.content, row=0, column=0, sticky="nsew")

    def _make_browse(self) -> ctk.CTkFrame:
        from ezwow.ui.tabs.browse import BrowseTab

        return BrowseTab(master=self, catalog=self.catalog, app=self)

    def _make_installed(self) -> ctk.CTkFrame:
        from ezwow.ui.tabs.installed import InstalledTab

        return InstalledTab(master=self, app=self)

    def _make_updates(self) -> ctk.CTkFrame:
        from ezwow.ui.tabs.updates import UpdatesTab

        return UpdatesTab(master=self, app=self)

    def _make_client_mods(self) -> ctk.CTkFrame:
        from ezwow.ui.tabs.client_mods import ClientModsTab

        return ClientModsTab(master=self, catalog=self.catalog, app=self)

    def _make_profiles(self) -> ctk.CTkFrame:
        from ezwow.ui.tabs.profiles import ProfilesTab

        return ProfilesTab(master=self, catalog=self.catalog, app=self)

    def _make_settings(self) -> ctk.CTkFrame:
        from ezwow.ui.tabs.settings import SettingsTab

        return SettingsTab(master=self, app=self)

    def set_status(self, msg: str) -> None:
        self.status.configure(text=msg)
        self.update_idletasks()


def launch() -> None:
    app = App()
    app.mainloop()
```

- [ ] **Step 2: Add notification widget**

`ezwow/ui/widgets/notification.py`:

```python
"""Modal notification helper."""

from __future__ import annotations

from tkinter import messagebox


def info(title: str, msg: str) -> None:
    messagebox.showinfo(title, msg)


def error(title: str, msg: str) -> None:
    messagebox.showerror(title, msg)


def confirm(title: str, msg: str) -> bool:
    return bool(messagebox.askyesno(title, msg))
```

- [ ] **Step 3: Smoke-test import**

```bash
.venv/bin/python -c "from ezwow.ui.app import App; print('ok')"
```

If `customtkinter` complains about display at import time on a headless box, that's expected — only `App()` instantiation needs a display.

- [ ] **Step 4: Commit**

```bash
git add ezwow/ui/app.py ezwow/ui/widgets/notification.py
git commit -m "feat(ui): add CustomTkinter shell with side-nav and tab dispatcher"
```

---

## Task 19: Browse tab

**Files:**
- Create: `/home/jalsarraf/git/ezwowaddon/ezwow/ui/tabs/browse.py`

- [ ] **Step 1: Implement**

```python
"""Browse tab: categorized addon catalog with search."""

from __future__ import annotations

import datetime as dt
import threading
from typing import TYPE_CHECKING

import customtkinter as ctk

from ezwow import config
from ezwow.catalog.schema import Addon, Catalog
from ezwow.core import deps, github, installer, manifest
from ezwow.ui.widgets import notification

if TYPE_CHECKING:
    from ezwow.ui.app import App


class BrowseTab(ctk.CTkFrame):
    def __init__(self, *, master, catalog: Catalog, app: "App") -> None:
        super().__init__(master)
        self.app = app
        self.catalog = catalog
        self.search_var = ctk.StringVar()
        self.search_var.trace_add("write", lambda *_: self._refresh())
        self._build()

    def _build(self) -> None:
        ctk.CTkLabel(self, text="Browse Addons", font=ctk.CTkFont(size=18, weight="bold")).pack(
            anchor="w", padx=12, pady=(12, 4)
        )
        bar = ctk.CTkFrame(self, fg_color="transparent")
        bar.pack(fill="x", padx=12, pady=4)
        ctk.CTkEntry(bar, textvariable=self.search_var, placeholder_text="search…", width=300).pack(
            side="left"
        )

        self.scroll = ctk.CTkScrollableFrame(self)
        self.scroll.pack(fill="both", expand=True, padx=12, pady=8)
        self._refresh()

    def _refresh(self) -> None:
        for child in self.scroll.winfo_children():
            child.destroy()
        query = self.search_var.get().lower().strip()
        by_cat: dict[str, list[Addon]] = {}
        for a in self.catalog.addons:
            if query and query not in a.name.lower() and query not in a.description.lower():
                continue
            by_cat.setdefault(a.category, []).append(a)

        cat_label = {c.id: c.label for c in self.catalog.categories}
        for cat_id in sorted(by_cat):
            ctk.CTkLabel(
                self.scroll, text=cat_label.get(cat_id, cat_id), font=ctk.CTkFont(weight="bold")
            ).pack(anchor="w", pady=(8, 2))
            for addon in sorted(by_cat[cat_id], key=lambda a: a.name):
                self._render_addon_row(addon)

    def _render_addon_row(self, addon: Addon) -> None:
        row = ctk.CTkFrame(self.scroll)
        row.pack(fill="x", pady=2)
        text = f"{addon.name} — {addon.description}"
        ctk.CTkLabel(row, text=text, anchor="w").pack(side="left", padx=6)
        ctk.CTkButton(
            row, text="Install", width=90, command=lambda a=addon: self._install(a)
        ).pack(side="right", padx=6)

    def _install(self, addon: Addon) -> None:
        if self.app.addons_folder is None:
            notification.error(
                "AddOns folder not set",
                "Configure your AddOns folder in Settings first.",
            )
            return
        ordered = deps.resolve([addon.id], self.catalog)
        threading.Thread(
            target=self._do_install, args=(ordered,), daemon=True
        ).start()

    def _do_install(self, addon_ids: list[str]) -> None:
        cfg = config.load()
        gh = github.GitHubClient(cache_dir=config.cache_dir(), token=cfg.github_pat)
        for aid in addon_ids:
            addon = self.catalog.addon_by_id(aid)
            assert addon is not None
            self.app.set_status(f"installing {aid}…")
            try:
                result = installer.install_from_url(
                    url=addon.branch_zip_url(),
                    addons_folder=self.app.addons_folder,
                    target_folder_name=addon.folder,
                )
            except installer.InstallError as exc:
                self.app.after(0, lambda e=exc: notification.error("Install failed", str(e)))
                return
            sha = gh.branch_head_sha(addon.github, addon.branch)
            manifest.record(
                self.app.addons_folder,
                manifest.InstallEntry(
                    addon_id=aid,
                    folder=addon.folder,
                    source=f"github:{addon.github}",
                    ref=addon.branch,
                    sha=sha,
                    installed_at=dt.datetime.now(dt.timezone.utc),
                    files=result.files,
                    size_bytes=result.size_bytes,
                ),
            )
        self.app.after(0, lambda: self.app.set_status("Ready."))
        self.app.after(0, lambda: notification.info("Installed", ", ".join(addon_ids)))
```

- [ ] **Step 2: Commit**

```bash
git add ezwow/ui/tabs/browse.py
git commit -m "feat(ui): add Browse tab with category groups, search, and threaded install"
```

---

## Task 20: Installed, Updates, Client Mods, Profiles, Settings tabs

Each tab is a separate file with the same shape: `Tab(master, app)` → CTkFrame. To stay bite-sized, treat each as its own commit but bundled into one task block.

**Files:**
- Create: `ezwow/ui/tabs/installed.py`
- Create: `ezwow/ui/tabs/updates.py`
- Create: `ezwow/ui/tabs/client_mods.py`
- Create: `ezwow/ui/tabs/profiles.py`
- Create: `ezwow/ui/tabs/settings.py`

- [ ] **Step 1: `installed.py`**

```python
"""Installed addons tab."""

from __future__ import annotations

import shutil
from typing import TYPE_CHECKING

import customtkinter as ctk

from ezwow.core import manifest
from ezwow.ui.widgets import notification

if TYPE_CHECKING:
    from ezwow.ui.app import App


class InstalledTab(ctk.CTkFrame):
    def __init__(self, *, master, app: "App") -> None:
        super().__init__(master)
        self.app = app
        self._build()

    def _build(self) -> None:
        ctk.CTkLabel(self, text="Installed", font=ctk.CTkFont(size=18, weight="bold")).pack(
            anchor="w", padx=12, pady=(12, 4)
        )
        ctk.CTkButton(self, text="Refresh", command=self._refresh).pack(anchor="w", padx=12)
        self.list = ctk.CTkScrollableFrame(self)
        self.list.pack(fill="both", expand=True, padx=12, pady=8)
        self._refresh()

    def _refresh(self) -> None:
        for child in self.list.winfo_children():
            child.destroy()
        if not self.app.addons_folder:
            ctk.CTkLabel(self.list, text="(AddOns folder not set)").pack()
            return
        m = manifest.load(self.app.addons_folder)
        if not m.installs:
            ctk.CTkLabel(self.list, text="(no installs tracked)").pack()
            return
        for inst in sorted(m.installs.values(), key=lambda i: i.addon_id):
            row = ctk.CTkFrame(self.list)
            row.pack(fill="x", pady=2)
            ctk.CTkLabel(
                row,
                text=f"{inst.addon_id}   sha={(inst.sha or '?')[:7]}",
                anchor="w",
            ).pack(side="left", padx=6)
            ctk.CTkButton(
                row,
                text="Remove",
                width=90,
                command=lambda i=inst: self._remove(i.addon_id, i.folder),
            ).pack(side="right", padx=6)

    def _remove(self, addon_id: str, folder_name: str) -> None:
        if not notification.confirm("Confirm", f"Remove {addon_id}?"):
            return
        target = self.app.addons_folder / folder_name
        if target.is_dir():
            shutil.rmtree(target)
        manifest.remove(self.app.addons_folder, addon_id)
        self._refresh()
```

- [ ] **Step 2: `updates.py`**

```python
"""Updates tab."""

from __future__ import annotations

import datetime as dt
import threading
from typing import TYPE_CHECKING

import customtkinter as ctk

from ezwow import config
from ezwow.core import github, installer, manifest, updater
from ezwow.ui.widgets import notification

if TYPE_CHECKING:
    from ezwow.ui.app import App


class UpdatesTab(ctk.CTkFrame):
    def __init__(self, *, master, app: "App") -> None:
        super().__init__(master)
        self.app = app
        self._build()

    def _build(self) -> None:
        ctk.CTkLabel(self, text="Updates", font=ctk.CTkFont(size=18, weight="bold")).pack(
            anchor="w", padx=12, pady=(12, 4)
        )
        ctk.CTkButton(self, text="Check Now", command=self._refresh).pack(anchor="w", padx=12)
        self.update_all_btn = ctk.CTkButton(
            self, text="Update All", command=self._update_all
        )
        self.update_all_btn.pack(anchor="w", padx=12, pady=4)
        self.list = ctk.CTkScrollableFrame(self)
        self.list.pack(fill="both", expand=True, padx=12, pady=8)
        self._refresh()

    def _refresh(self) -> None:
        for child in self.list.winfo_children():
            child.destroy()
        if not self.app.addons_folder:
            return
        cfg = config.load()
        gh = github.GitHubClient(cache_dir=config.cache_dir(), token=cfg.github_pat)
        plan = updater.plan(
            addons_folder=self.app.addons_folder, catalog=self.app.catalog, gh_client=gh
        )
        if not plan.updates:
            ctk.CTkLabel(self.list, text="All addons up to date.").pack()
            return
        for u in plan.updates:
            row = ctk.CTkFrame(self.list)
            row.pack(fill="x", pady=2)
            ctk.CTkLabel(
                row,
                text=f"{u.addon_id}: {(u.current or '?')[:7]} → {(u.latest or '?')[:7]}",
                anchor="w",
            ).pack(side="left", padx=6)

    def _update_all(self) -> None:
        threading.Thread(target=self._do_update_all, daemon=True).start()

    def _do_update_all(self) -> None:
        if not self.app.addons_folder:
            return
        cfg = config.load()
        gh = github.GitHubClient(cache_dir=config.cache_dir(), token=cfg.github_pat)
        plan = updater.plan(
            addons_folder=self.app.addons_folder, catalog=self.app.catalog, gh_client=gh
        )
        for u in plan.updates:
            addon = self.app.catalog.addon_by_id(u.addon_id)
            if addon is None:
                continue
            self.app.set_status(f"updating {addon.id}…")
            try:
                result = installer.install_from_url(
                    url=addon.branch_zip_url(),
                    addons_folder=self.app.addons_folder,
                    target_folder_name=addon.folder,
                )
            except installer.InstallError as exc:
                self.app.after(0, lambda e=exc: notification.error("Update failed", str(e)))
                return
            manifest.record(
                self.app.addons_folder,
                manifest.InstallEntry(
                    addon_id=addon.id,
                    folder=addon.folder,
                    source=f"github:{addon.github}",
                    ref=addon.branch,
                    sha=u.latest,
                    installed_at=dt.datetime.now(dt.timezone.utc),
                    files=result.files,
                    size_bytes=result.size_bytes,
                ),
            )
        self.app.after(0, lambda: self.app.set_status("Ready."))
        self.app.after(0, self._refresh)
```

- [ ] **Step 3: `client_mods.py`**

```python
"""Client mods tab — installs to Data/ folder."""

from __future__ import annotations

from typing import TYPE_CHECKING

import customtkinter as ctk

from ezwow.catalog.schema import Catalog
from ezwow.core import detector
from ezwow.ui.widgets import notification

if TYPE_CHECKING:
    from ezwow.ui.app import App


class ClientModsTab(ctk.CTkFrame):
    def __init__(self, *, master, catalog: Catalog, app: "App") -> None:
        super().__init__(master)
        self.app = app
        self.catalog = catalog
        self._build()

    def _build(self) -> None:
        ctk.CTkLabel(self, text="Client Mods", font=ctk.CTkFont(size=18, weight="bold")).pack(
            anchor="w", padx=12, pady=(12, 4)
        )
        ctk.CTkLabel(
            self,
            text="Mods that go in Data/ (DLLs, MPQ patches). Requires Data folder.",
            anchor="w",
            wraplength=700,
        ).pack(anchor="w", padx=12)

        scroll = ctk.CTkScrollableFrame(self)
        scroll.pack(fill="both", expand=True, padx=12, pady=8)

        for mod in self.catalog.client_mods:
            row = ctk.CTkFrame(scroll)
            row.pack(fill="x", pady=2)
            ctk.CTkLabel(
                row, text=f"{mod.name} — {mod.description}", anchor="w"
            ).pack(side="left", padx=6)
            ctk.CTkButton(
                row,
                text="Install",
                width=90,
                command=lambda m=mod: self._install(m.name),
            ).pack(side="right", padx=6)

    def _install(self, name: str) -> None:
        data = detector.find_data_folder(addons=self.app.addons_folder)
        if data is None:
            notification.error("Data folder missing", "Cannot find Data/ next to your AddOns folder.")
            return
        notification.info(
            "Manual step",
            f"Client mod install will place files into {data}. "
            f"Auto-install for {name} ships in v2.1; for now, see homepage.",
        )
```

(Client-mod *automatic* install is deferred to v2.1 — Task 25 in the plan adds tracking issue. Spec §15 keeps client-mod tab in v2.0; this implements the discovery surface, with manual fallback. Aligns with YAGNI.)

- [ ] **Step 4: `profiles.py`**

```python
"""Profiles tab."""

from __future__ import annotations

import threading
from tkinter import filedialog
from typing import TYPE_CHECKING

import customtkinter as ctk

from ezwow.catalog.schema import Catalog
from ezwow.core import deps, profile
from ezwow.ui.widgets import notification

if TYPE_CHECKING:
    from ezwow.ui.app import App


class ProfilesTab(ctk.CTkFrame):
    def __init__(self, *, master, catalog: Catalog, app: "App") -> None:
        super().__init__(master)
        self.app = app
        self.catalog = catalog
        self._build()

    def _build(self) -> None:
        ctk.CTkLabel(self, text="Profiles", font=ctk.CTkFont(size=18, weight="bold")).pack(
            anchor="w", padx=12, pady=(12, 4)
        )

        for preset_id, preset in self.catalog.presets.items():
            row = ctk.CTkFrame(self)
            row.pack(fill="x", padx=12, pady=4)
            ctk.CTkLabel(
                row,
                text=f"{preset.label} — {len(preset.addons)} addons",
                anchor="w",
            ).pack(side="left", padx=6)
            ctk.CTkButton(
                row,
                text="Apply",
                width=90,
                command=lambda pid=preset_id: self._apply_preset(pid),
            ).pack(side="right", padx=6)

        ctk.CTkLabel(self, text="Custom profile:").pack(anchor="w", padx=12, pady=(12, 0))
        bar = ctk.CTkFrame(self, fg_color="transparent")
        bar.pack(fill="x", padx=12)
        ctk.CTkButton(bar, text="Import…", command=self._import).pack(side="left", padx=4)
        ctk.CTkButton(bar, text="Export…", command=self._export).pack(side="left", padx=4)

    def _apply_preset(self, preset_id: str) -> None:
        threading.Thread(target=self._do_apply, args=(preset_id,), daemon=True).start()

    def _do_apply(self, preset_id: str) -> None:
        from ezwow.ui.tabs.browse import BrowseTab

        resolved = profile.resolve_preset(preset_id, self.catalog)
        try:
            ordered = deps.resolve(resolved.addon_ids, self.catalog)
        except (deps.CycleError, KeyError) as exc:
            self.app.after(0, lambda e=exc: notification.error("Preset error", str(e)))
            return
        BrowseTab._do_install(self.app.tabs["Browse"], ordered)

    def _import(self) -> None:
        path = filedialog.askopenfilename(filetypes=[("JSON", "*.json")])
        if not path:
            return
        p = profile.import_profile(__import__("pathlib").Path(path))
        threading.Thread(
            target=self._do_apply_ids, args=(p.addons,), daemon=True
        ).start()

    def _do_apply_ids(self, ids: list[str]) -> None:
        from ezwow.ui.tabs.browse import BrowseTab

        try:
            ordered = deps.resolve(ids, self.catalog)
        except (deps.CycleError, KeyError) as exc:
            self.app.after(0, lambda e=exc: notification.error("Profile error", str(e)))
            return
        BrowseTab._do_install(self.app.tabs["Browse"], ordered)

    def _export(self) -> None:
        from ezwow.core import manifest

        if not self.app.addons_folder:
            return
        path = filedialog.asksaveasfilename(defaultextension=".json")
        if not path:
            return
        m = manifest.load(self.app.addons_folder)
        profile.export_profile(
            out_path=__import__("pathlib").Path(path),
            addon_ids=sorted(m.installs.keys()),
            client_mod_ids=[],
            label="user-export",
        )
        notification.info("Exported", path)
```

- [ ] **Step 5: `settings.py`**

```python
"""Settings tab."""

from __future__ import annotations

import pathlib
from tkinter import filedialog
from typing import TYPE_CHECKING

import customtkinter as ctk

from ezwow import config
from ezwow.core import detector

if TYPE_CHECKING:
    from ezwow.ui.app import App


class SettingsTab(ctk.CTkFrame):
    def __init__(self, *, master, app: "App") -> None:
        super().__init__(master)
        self.app = app
        self.cfg = config.load()
        self._build()

    def _build(self) -> None:
        ctk.CTkLabel(self, text="Settings", font=ctk.CTkFont(size=18, weight="bold")).pack(
            anchor="w", padx=12, pady=(12, 4)
        )

        self.folder_var = ctk.StringVar(value=self.cfg.addons_folder or "")
        ctk.CTkLabel(self, text="AddOns folder:").pack(anchor="w", padx=12, pady=(8, 0))
        row = ctk.CTkFrame(self, fg_color="transparent")
        row.pack(fill="x", padx=12)
        ctk.CTkEntry(row, textvariable=self.folder_var, width=540).pack(side="left", padx=4)
        ctk.CTkButton(row, text="Browse…", command=self._pick).pack(side="left", padx=4)

        self.pat_var = ctk.StringVar(value=self.cfg.github_pat or "")
        ctk.CTkLabel(self, text="GitHub PAT (optional, raises rate limit):").pack(
            anchor="w", padx=12, pady=(8, 0)
        )
        ctk.CTkEntry(self, textvariable=self.pat_var, show="*", width=540).pack(
            anchor="w", padx=12
        )

        self.theme_var = ctk.StringVar(value=self.cfg.theme)
        ctk.CTkLabel(self, text="Theme:").pack(anchor="w", padx=12, pady=(8, 0))
        ctk.CTkOptionMenu(
            self, values=["dark", "light", "system"], variable=self.theme_var
        ).pack(anchor="w", padx=12)

        ctk.CTkButton(self, text="Save", command=self._save).pack(
            anchor="w", padx=12, pady=12
        )

    def _pick(self) -> None:
        path = filedialog.askdirectory(title="Pick Interface/AddOns")
        if path:
            self.folder_var.set(path)

    def _save(self) -> None:
        self.cfg.addons_folder = self.folder_var.get() or None
        self.cfg.github_pat = self.pat_var.get() or None
        self.cfg.theme = self.theme_var.get()
        config.save(self.cfg)
        ctk.set_appearance_mode(self.cfg.theme)
        self.app.cfg = self.cfg
        self.app.addons_folder = detector.find_addons_folder(saved=self.cfg.addons_folder)
```

- [ ] **Step 6: Commit per file** (5 commits, one per tab)

```bash
git add ezwow/ui/tabs/installed.py
git commit -m "feat(ui): add Installed tab"

git add ezwow/ui/tabs/updates.py
git commit -m "feat(ui): add Updates tab with Update All"

git add ezwow/ui/tabs/client_mods.py
git commit -m "feat(ui): add Client Mods tab (manual install for v2.0)"

git add ezwow/ui/tabs/profiles.py
git commit -m "feat(ui): add Profiles tab with preset apply + import/export"

git add ezwow/ui/tabs/settings.py
git commit -m "feat(ui): add Settings tab with PAT, theme, paths"
```

---

# Phase 7 — CI / CD

## Task 21: Replace build workflow

**Files:**
- Modify (overwrite): `/home/jalsarraf/git/ezwowaddon/.github/workflows/build.yml`

- [ ] **Step 1: Read existing**

```bash
cat /home/jalsarraf/git/ezwowaddon/.github/workflows/build.yml
```

- [ ] **Step 2: Overwrite with v2 build**

```yaml
name: Build and release binaries

on:
  push:
    tags:
      - 'v*'
  workflow_dispatch:

permissions:
  contents: read

jobs:
  build-windows:
    name: Windows Build
    runs-on: windows-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: '3.12'
      - name: Install dependencies
        run: |
          python -m pip install --upgrade pip
          pip install -e ".[dev]" pyinstaller
      - name: Build EXE
        run: |
          pyinstaller --noconfirm --onefile --windowed --collect-all customtkinter --name ezwow ezwow.py
      - name: Upload Windows executable
        uses: actions/upload-artifact@v4
        with:
          name: ezwow-windows-exe
          path: dist/ezwow.exe

  build-linux:
    name: Linux Build
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: '3.12'
      - name: Install dependencies
        run: |
          python -m pip install --upgrade pip
          pip install -e ".[dev]" pyinstaller
      - name: Build Executable
        run: |
          pyinstaller --noconfirm --onefile --collect-all customtkinter --name ezwow ezwow.py
      - name: Upload Linux executable
        uses: actions/upload-artifact@v4
        with:
          name: ezwow-linux
          path: dist/ezwow
```

Note: macOS job removed; `actions/upload-artifact@v3` upgraded to `@v4` (required after January 2025); python pinned to `3.12`.

- [ ] **Step 3: Commit**

```bash
git add .github/workflows/build.yml
git commit -m "ci: replace build workflow — drop macOS, pin python 3.12, collect customtkinter assets"
```

---

## Task 22: Add CI test workflow

**Files:**
- Create: `/home/jalsarraf/git/ezwowaddon/.github/workflows/ci.yml`

- [ ] **Step 1: Write workflow**

```yaml
name: CI

on:
  push:
    branches: [main, dev]
  pull_request:

permissions:
  contents: read

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: '3.12'
      - name: Install
        run: |
          python -m pip install --upgrade pip
          pip install -e ".[dev]"
      - name: Lint
        run: ruff check ezwow tests
      - name: Type check
        run: mypy ezwow
      - name: Tests with coverage
        run: pytest --cov=ezwow.core --cov-fail-under=70
```

- [ ] **Step 2: Commit**

```bash
git add .github/workflows/ci.yml
git commit -m "ci: add tests + lint + type-check workflow with 70% coverage gate"
```

---

## Task 23: Catalog smoke-check workflow

**Files:**
- Create: `/home/jalsarraf/git/ezwowaddon/.github/workflows/catalog-check.yml`
- Create: `/home/jalsarraf/git/ezwowaddon/scripts/catalog_check.py`

- [ ] **Step 1: Write the catalog-check script**

```python
"""Verify every catalog URL resolves with HTTP HEAD <400."""

from __future__ import annotations

import json
import pathlib
import sys

import requests

ROOT = pathlib.Path(__file__).resolve().parents[1]
CATALOG = ROOT / "catalog" / "addons.json"


def main() -> int:
    raw = json.loads(CATALOG.read_text(encoding="utf-8"))
    failures: list[tuple[str, str, int]] = []

    for addon in raw.get("addons", []):
        url = (
            f"https://github.com/{addon['github']}/archive/"
            f"refs/heads/{addon.get('branch', 'master')}.zip"
        )
        try:
            resp = requests.head(url, allow_redirects=True, timeout=15)
        except requests.RequestException as exc:
            failures.append((addon["id"], url, -1))
            print(f"FAIL {addon['id']:30s} {url}  ({exc})")
            continue
        if resp.status_code >= 400:
            failures.append((addon["id"], url, resp.status_code))
            print(f"FAIL {addon['id']:30s} {url}  HTTP {resp.status_code}")
        else:
            print(f"OK   {addon['id']:30s} {url}")

    if failures:
        print(f"\n{len(failures)} broken URLs", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
```

- [ ] **Step 2: Write workflow**

```yaml
name: Catalog Check

on:
  schedule:
    - cron: '17 5 * * *'
  workflow_dispatch:

permissions:
  contents: read
  issues: write

jobs:
  check:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: '3.12'
      - name: Install requests
        run: pip install requests
      - name: Smoke-test catalog URLs
        run: python scripts/catalog_check.py
```

- [ ] **Step 3: Run script locally**

```bash
.venv/bin/python /home/jalsarraf/git/ezwowaddon/scripts/catalog_check.py
```

Expected: most URLs OK; any FAILs identify catalog entries needing attention. Fix broken catalog entries inline before commit (some `community` repos in the example list may need adjusting — verify by `gh repo view <slug>` and substitute working canonical URLs).

- [ ] **Step 4: Commit**

```bash
git add .github/workflows/catalog-check.yml scripts/catalog_check.py
git commit -m "ci: add nightly catalog URL smoke-check script and workflow"
```

---

# Phase 8 — Docs and finalization

## Task 24: README rewrite

**Files:**
- Modify: `/home/jalsarraf/git/ezwowaddon/README.md`

- [ ] **Step 1: Replace README content**

```markdown
# EZWowAddon

World-class addon and client-mod manager for [Turtle WoW](https://turtle-wow.org/) (Vanilla 1.12 client).

EZWowAddon installs, updates, and removes addons from a curated catalog of 40+ community-maintained projects, plus client mods (VanillaFixes, SuperWoW, Nampower, ...). Dependency-aware, with one-click presets for common loadouts (Essential, Raider, Hardcore, Minimal UI), backup/restore, and both a modern GUI and a scriptable CLI.

## Features

- **Curated catalog** of 40+ addons + 6 client mods, categorised (UI, Quest, Combat, Auction, Inventory, Raid, Social, Utility).
- **Real update detection** — tracks installed Git SHA per addon and surfaces upstream changes; one-click "Update All".
- **Presets** — Essential, Raider, Hardcore, Minimal UI; resolves dependencies automatically.
- **Backup / restore** — tar.gz snapshots of `Interface/AddOns/` + `WTF/` (SavedVariables); restore in one command.
- **Modern UI** — CustomTkinter dark theme, side-nav, search, threaded installs.
- **CLI mode** — `ezwow install`, `ezwow update --all`, `ezwow doctor` for power users and scripts.
- **Auto-detection** — finds your AddOns folder for both classic installs (`~/Games/Turtle WoW/`) and the official Turtle launcher (`%APPDATA%/TurtleWoW/`).
- **Custom GitHub URLs** — install any GitHub-hosted addon by id or by entering a repository URL.

## Install

### Pre-built binaries

Download the latest release for your platform from the [Releases page](https://github.com/jalsarraf0/ezwowaddon/releases).

```bash
# Linux
curl -fsSL https://github.com/jalsarraf0/ezwowaddon/releases/latest/download/ezwow -o ezwow
chmod +x ezwow
./ezwow
```

```powershell
# Windows
Invoke-WebRequest -Uri https://github.com/jalsarraf0/ezwowaddon/releases/latest/download/ezwow.exe -OutFile ezwow.exe
.\ezwow.exe
```

### From source

```bash
git clone https://github.com/jalsarraf0/ezwowaddon.git
cd ezwowaddon
python3.12 -m venv .venv
.venv/bin/pip install -e ".[dev]"
.venv/bin/ezwow         # GUI
.venv/bin/ezwow list    # CLI
```

## CLI usage

```
ezwow                              # GUI
ezwow list                         # all catalog addons
ezwow list --installed
ezwow list --updates
ezwow install pfquest pfquest-turtle
ezwow install --preset essential
ezwow update --all
ezwow remove bigwigs
ezwow backup
ezwow restore /path/to/backup.tar.gz
ezwow profile export ~/my-setup.json
ezwow profile import ~/my-setup.json
ezwow doctor
```

## Catalog

The curated catalog lives at [`catalog/addons.json`](catalog/addons.json). Pull requests adding or updating entries are welcome — see [CONTRIBUTING.md](CONTRIBUTING.md).

## Build a binary locally

```bash
.venv/bin/pip install pyinstaller
.venv/bin/pyinstaller --noconfirm --onefile --windowed \
  --collect-all customtkinter --name ezwow ezwow.py
```

Output in `dist/`.

## License

MIT — Copyright (c) 2025 Jamal Al-Sarraf.
```

- [ ] **Step 2: Commit**

```bash
git add README.md
git commit -m "docs: rewrite README for v2.0 features and CLI"
```

---

## Task 25: CONTRIBUTING.md

**Files:**
- Create: `/home/jalsarraf/git/ezwowaddon/CONTRIBUTING.md`

- [ ] **Step 1: Write**

```markdown
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
```

- [ ] **Step 2: Commit**

```bash
git add CONTRIBUTING.md
git commit -m "docs: add CONTRIBUTING.md with catalog schema and dev setup"
```

---

## Task 26: CHANGELOG entry

**Files:**
- Modify: `/home/jalsarraf/git/ezwowaddon/CHANGELOG.md`

- [ ] **Step 1: Prepend v2.0.0 entry to top of CHANGELOG**

Read existing then prepend (after the title block):

```markdown
## [v2.0.0] – 2026-05-03

### Added

- Full Python package rewrite: `ezwow/{catalog,core,ui,cli}` with strict types and tests.
- Curated catalog at `catalog/addons.json`: 40+ addons + 6 client mods, 4 presets.
- Real update detection via Git SHA tracking + GitHub API ETag cache.
- Presets / profiles: Essential, Raider, Hardcore, Minimal UI; custom JSON import/export.
- Backup / restore of AddOns + SavedVariables.
- CLI mode: `ezwow install`, `update`, `list`, `remove`, `doctor`, etc.
- CustomTkinter UI with side-nav, search, threaded installs, dark theme by default.
- Auto-detection of Turtle launcher install path (`%APPDATA%/TurtleWoW/`).
- Optional GitHub PAT for higher API rate limits.
- Atomic install with zip-slip protection.
- Nightly catalog URL smoke-test workflow.

### Changed

- `ezwow.py` is now a thin shim over the `ezwow` package.
- CI: dropped macOS, upgraded to Python 3.12, `actions/*@v4`, added lint + type + coverage gate.
- Config moved to standard XDG/AppData locations (`~/.config/ezwowaddon/config.json` on Linux).

### Removed

- macOS build target.
```

- [ ] **Step 2: Commit**

```bash
git add CHANGELOG.md
git commit -m "docs: add v2.0.0 changelog entry"
```

---

## Task 27: Final integration check

- [ ] **Step 1: Run full test suite + lint + types**

```bash
cd /home/jalsarraf/git/ezwowaddon
.venv/bin/ruff check ezwow tests
.venv/bin/mypy ezwow
.venv/bin/pytest --cov=ezwow.core --cov-fail-under=70 -v
```

Expected: all green, coverage ≥70% on core.

- [ ] **Step 2: Smoke-test CLI**

```bash
.venv/bin/ezwow doctor
.venv/bin/ezwow list | head -30
```

Expected: doctor prints config/cache/data paths; list prints categories with addons.

- [ ] **Step 3: Smoke-test GUI launch (if display available)**

```bash
.venv/bin/ezwow --gui
```

Manually: confirm side-nav loads, switching tabs works, Settings persists.

- [ ] **Step 4: Run orchestrator-enterprise scan on workflows**

```bash
orchestrator-enterprise scan /home/jalsarraf/git/ezwowaddon/.github/workflows/ --fail-on error
```

Expected: no errors. Warnings are acceptable. Per CLAUDE.md absolute directive — must pass before any push.

- [ ] **Step 5: Confirm clean tree**

```bash
git status
git log --oneline -30
```

Expected: clean tree; ~25 commits ahead of where v2 work began.

- [ ] **Step 6: Stop here — DO NOT push**

User reviews locally, decides on tag (`v2.0.0`) and push timing. No `git push` in this plan.

---

# Self-review against spec

| Spec section | Covered by tasks |
|---|---|
| §2.1 package layout | Tasks 2–3 (skeleton) + 4–7 (catalog) + 8–15 (core) + 18–20 (UI) + 17 (CLI) |
| §2.2 module responsibilities | One module per task, single responsibility |
| §2.3 data flow | Implemented in installer (Task 11), updater (Task 14) |
| §2.4 catalog format | Task 5 (JSON) + Task 4 (schema) |
| §2.5 manifest format | Task 10 |
| §2.6 detection precedence | Task 8 |
| §3 UI design | Tasks 18–20 |
| §4 CLI design | Task 17 |
| §5 update algorithm | Task 14 |
| §6 backup/restore | Task 12 |
| §7 error handling | Each task surfaces typed exceptions; UI tabs catch and `notification.error` |
| §8 testing strategy | Tests written first per TDD in every task; coverage gate Task 16 + 22 |
| §9 CI/CD | Tasks 21–23 |
| §10 migration / backcompat | Task 2 (`config.load` reads legacy `ezwow_config.json`); Task 3 (shim) |
| §11 build & release | Task 21 (workflow) + pyproject.toml console_script in Task 1 |
| §12 security | Task 11 (zip-slip); HTTPS by default; PAT optional in Settings (Task 20.5) |
| §13 catalog population | Task 5 |
| §14 risks | Mitigations all in tasks (rate-limit cache in Task 9; atomic install in Task 11; nightly URL check Task 23) |
| §15 phases | Tasks ordered to match |

Coverage looks complete. Plan is ready.
