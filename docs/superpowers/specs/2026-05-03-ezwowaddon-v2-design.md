# EZWowAddon v2.0 — World-Class Turtle WoW Addon Manager

**Date:** 2026-05-03
**Status:** Approved (direction); awaiting spec sign-off
**Owner:** jalsarraf0
**Predecessor:** v1.0.7 (single-file `ezwow.py`)

---

## 1. Goal

Transform EZWowAddon from a 6-addon, single-file Tkinter launcher into the de-facto Turtle WoW addon + client-mod manager: comprehensive curated catalog, real update detection, modern UI, profiles, backups, and CLI — without bloating into a full game launcher (TurtleLauncher already covers that niche).

**Success criteria:**
- Catalog ships with ≥40 curated addons + ≥6 client mods, categorized.
- Installed addons can be updated in-place with one click; UI shows "N updates available" badge.
- Users can apply a one-click preset ("Essential", "Raider", "Hardcore") that resolves dependencies.
- Client mods (`Data/*.mpq`, DLL injectors) install to the right folder automatically.
- CLI works headless: `ezwow install pfquest`, `ezwow update --all`, `ezwow list --installed`.
- All existing v1.0.7 behaviors preserved (recommended tab, install-from-URL, manage installed, folder auto-detect).
- CI builds Windows + Linux only (no macOS, no `attest-build-provenance`).
- Test coverage ≥70% on `ezwow.core.*` modules.

**Non-goals (v2.0):**
- Full game launcher / DXVK / wow.exe launching (TurtleLauncher's lane).
- Custom addon discovery (e.g. crawling forum threads). Catalog is curated.
- Sync/cloud profiles. Profiles are local JSON files; sharing is manual.
- macOS support. Removed entirely.

---

## 2. Architecture

### 2.1 Package layout

```
ezwowaddon/
├── pyproject.toml                  # NEW — replaces requirements.txt; build/test/lint config
├── ezwow.py                        # KEPT as 3-line shim → from ezwow.__main__ import main; main()
├── catalog/
│   └── addons.json                 # NEW — canonical curated catalog (community-PR friendly)
├── ezwow/                          # NEW — Python package
│   ├── __init__.py
│   ├── __main__.py                 # entry point: parse args → CLI or GUI
│   ├── config.py                   # XDG/AppData config paths, persistence
│   ├── catalog/
│   │   ├── __init__.py
│   │   ├── schema.py               # dataclasses: Addon, ClientMod, Preset, Catalog
│   │   ├── loader.py               # load bundled + optionally fetch remote, merge
│   │   └── remote.py               # GitHub raw fetch with ETag cache
│   ├── core/
│   │   ├── __init__.py
│   │   ├── detector.py             # find AddOns/Data folders (Windows, WINE, Turtle launcher AppData)
│   │   ├── github.py               # API client (releases, branch SHA, ETag)
│   │   ├── installer.py            # download → extract → place; handles AddOns + Data targets
│   │   ├── updater.py              # diff installed SHA vs upstream HEAD; produce update plan
│   │   ├── manifest.py             # read/write `.ezwow-manifest.json` per install
│   │   ├── backup.py               # snapshot/restore Interface/AddOns + WTF/Account SavedVariables
│   │   ├── deps.py                 # topological resolution for catalog deps
│   │   └── profile.py              # preset apply / export / import
│   ├── ui/
│   │   ├── __init__.py
│   │   ├── app.py                  # CustomTkinter root window + theme
│   │   ├── tabs/
│   │   │   ├── browse.py           # categorized addon catalog with search + filter
│   │   │   ├── installed.py        # installed list + update/remove
│   │   │   ├── updates.py          # pending updates panel with "Update All"
│   │   │   ├── client_mods.py      # MPQ/DLL client mods (separate from AddOns)
│   │   │   ├── profiles.py         # presets + custom profile import/export
│   │   │   └── settings.py         # paths, GitHub PAT, remote-catalog toggle
│   │   └── widgets/
│   │       ├── addon_card.py
│   │       ├── progress.py
│   │       └── notification.py
│   └── cli.py                      # argparse-based CLI; thin wrapper over core/
├── tests/
│   ├── __init__.py
│   ├── conftest.py                 # tmp_path-based fake AddOns folder fixtures
│   ├── data/                       # tiny fixture zips
│   ├── test_catalog_schema.py
│   ├── test_catalog_loader.py
│   ├── test_detector.py
│   ├── test_installer.py           # uses respx/httpx mock or local fileserver fixture
│   ├── test_updater.py
│   ├── test_manifest.py
│   ├── test_backup.py
│   ├── test_deps.py
│   ├── test_profile.py
│   └── test_cli.py
├── docs/
│   └── superpowers/specs/2026-05-03-ezwowaddon-v2-design.md   # this file
├── .github/
│   └── workflows/
│       ├── build.yml               # MODIFIED — Win + Linux only
│       ├── ci.yml                  # NEW — pytest + ruff + mypy on PR
│       └── catalog-check.yml       # NEW — nightly URL smoke-test for addons.json
├── README.md                       # MODIFIED — feature list, screenshots, catalog contribution guide
├── CHANGELOG.md                    # APPENDED — v2.0.0 entry
├── CONTRIBUTING.md                 # NEW — how to add an addon to catalog
└── LICENSE                         # KEPT
```

### 2.2 Module responsibilities (one purpose each)

| Module | Purpose | Depends on |
|---|---|---|
| `catalog.schema` | Dataclasses + validation. No I/O. | (stdlib only) |
| `catalog.loader` | Load bundled JSON, merge remote if enabled. | `schema`, `remote` |
| `catalog.remote` | Fetch `catalog/addons.json` from GitHub raw with ETag cache. | `requests` |
| `core.detector` | Find install folders. Pure path logic. | (stdlib) |
| `core.github` | GitHub API: latest release, branch HEAD SHA, asset download URL, rate-limit handling. | `requests` |
| `core.installer` | Given (url, target_zone, folder_name): download → unzip → place atomically. | `core.github` |
| `core.updater` | Compare manifest SHA vs upstream → produce `UpdatePlan`. No mutation. | `core.github`, `core.manifest` |
| `core.manifest` | Read/write `.ezwow-manifest.json` (per-install metadata). | (stdlib) |
| `core.backup` | tar.gz snapshot of AddOns + SavedVariables; restore. | (stdlib) |
| `core.deps` | Topo-sort catalog deps; detect cycles. | `catalog.schema` |
| `core.profile` | Apply preset (install missing, mark optional removals); export/import. | `installer`, `deps` |
| `ui.app` + `ui.tabs.*` | CustomTkinter UI. Calls into `core.*` only. | `core`, `customtkinter` |
| `cli` | argparse → core. No GUI imports. | `core`, `catalog` |

**Hard rule:** UI never touches filesystem or network directly — always through `core`. Makes CLI = GUI behaviour-equivalent and tests trivial.

### 2.3 Data flow

```
User clicks "Install pfQuest"
  → ui.tabs.browse.install_clicked(addon_id)
  → core.deps.resolve(addon_id, catalog) → ["pfquest"]   # plus deps if any
  → core.installer.install_many([Addon(...)])
       → core.github.resolve_download_url(addon)
       → download zip to tmp
       → extract to AddOns/<folder>/
       → core.manifest.record(addon_id, sha, files, ts)
  → ui.refresh_state()
```

```
Startup update check
  → catalog.loader.load() → Catalog
  → core.manifest.list_installed() → [InstalledRef]
  → core.updater.plan(installed, catalog) → UpdatePlan
  → ui.app.show_update_badge(count)
```

### 2.4 Catalog format (`catalog/addons.json`)

**ID convention:** lowercase kebab-case (e.g. `pfquest-turtle`, `shagu-tweaks`, `bigwigs`). IDs are stable forever — once an addon ships in a release, its ID never changes. Display name (`name`) can change; `id` cannot.

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
    {"id": "utility", "label": "Utility / QoL"},
    {"id": "client-mod", "label": "Client Mod (Data/)"}
  ],
  "addons": [
    {
      "id": "pfquest",
      "name": "pfQuest",
      "category": "quest",
      "description": "Quest helper with in-game map markers and database",
      "author": "shagu",
      "github": "shagu/pfQuest",
      "branch": "master",
      "use_releases": false,
      "folder": "pfQuest",
      "depends": [],
      "tags": ["essential", "quest"],
      "homepage": "https://shagu.org/pfQuest"
    },
    {
      "id": "pfquest-turtle",
      "name": "pfQuest-Turtle",
      "category": "quest",
      "description": "Turtle WoW-specific quest data extension for pfQuest",
      "author": "shagu",
      "github": "shagu/pfQuest-turtle",
      "branch": "master",
      "folder": "pfQuest-turtle",
      "depends": ["pfquest"],
      "tags": ["essential", "turtle-only"]
    }
  ],
  "client_mods": [
    {
      "id": "vanillafixes",
      "name": "VanillaFixes",
      "description": "Stutter fix, animation lag fix, optional Vulkan via DXVK",
      "github": "RetroCro/TurtleWoW-Mods",
      "asset_pattern": "VanillaFixes*.zip",
      "install_to": "data_root",
      "files_to_install": ["VanillaFixes.exe", "*.dll"],
      "tags": ["essential", "performance"]
    }
  ],
  "presets": {
    "essential": {
      "label": "Essential (new players)",
      "addons": ["pfquest", "pfquest-turtle", "shagu-tweaks", "bagnon", "aux"],
      "client_mods": ["vanillafixes"]
    },
    "raider": {
      "label": "Raider",
      "addons": ["pfquest", "pfquest-turtle", "bigwigs", "shagudps", "pfui", "bettercharacterstats"]
    },
    "hardcore": {
      "label": "Hardcore",
      "addons": ["pfquest", "pfquest-turtle", "globalfriendslist", "restbar"]
    },
    "minimal-ui": {
      "label": "Minimal UI",
      "addons": ["shagu-tweaks", "bagnon"]
    }
  }
}
```

### 2.5 Local manifest format (`<AddOns>/.ezwow-manifest.json`)

```json
{
  "schema_version": 1,
  "installs": {
    "pfquest": {
      "folder": "pfQuest",
      "source": "github:shagu/pfQuest",
      "ref": "master",
      "sha": "abc123def456",
      "installed_at": "2026-05-03T18:42:01Z",
      "files": ["pfQuest/pfQuest.toc", "pfQuest/...", "..."],
      "size_bytes": 4823104
    }
  }
}
```

### 2.6 Folder detection precedence

`core.detector.find_addons_folder()` checks in order:
1. Saved config path (if still valid).
2. Turtle launcher path: `%APPDATA%/TurtleWoW/Interface/AddOns` (Windows), WINE equivalent.
3. Classic install: `~/Games/Turtle WoW/Interface/AddOns`, WINE equivalent.
4. `WINEPREFIX` env override.
5. `TURTLEWOW_HOME` env override (NEW).
6. Returns `None` → user picks via Settings.

Same logic for `find_data_folder()` — sibling of AddOns at `Interface/..` → `Data/`.

---

## 3. UI Design (CustomTkinter)

**Window:** 900×600 default, resizable, dark theme by default (toggle in Settings).

**Tabs (left rail nav, not top tabs — modern look):**
1. **Browse** — categorized addon grid. Search bar, category filter chips, sort by name/popularity. Cards show name, author, description, install button, "★ Featured" badge.
2. **Installed** — list with version, last updated, source. Per-row: Update / Remove / Reveal-folder.
3. **Updates** — appears only when ≥1 update pending. "Update All" button + per-row update.
4. **Client Mods** — separate from addons; shows MPQ/DLL mods that install to `Data/`.
5. **Profiles** — preset cards (Essential, Raider, Hardcore, Minimal UI). "Apply" shows diff (will install X, skip Y). Custom profile section: load/save JSON.
6. **Settings** — AddOns folder, Data folder, GitHub PAT (optional, raises rate limit), remote-catalog toggle, theme.

**Status bar (bottom):** current operation + progress bar (replaces old `progress.start()` indeterminate spinner with determinate per-file progress when possible).

**Update badge:** top-right of window — `🔔 3 updates` clickable → jumps to Updates tab.

---

## 4. CLI Design

```
ezwow                              # launches GUI (default)
ezwow --gui                        # explicit GUI
ezwow list                         # list catalog addons
ezwow list --installed             # list locally installed
ezwow list --updates               # list pending updates
ezwow install <id> [<id>...]       # install one or more by catalog id
ezwow install --preset essential   # apply preset
ezwow update [<id>]                # update one
ezwow update --all                 # update all
ezwow remove <id>                  # uninstall
ezwow backup [--out path.tar.gz]   # snapshot
ezwow restore <path.tar.gz>        # restore
ezwow profile export <out.json>
ezwow profile import <in.json>
ezwow doctor                       # diagnostic: paths, catalog version, rate limit, broken installs
```

Exit codes: 0 success, 1 generic error, 2 catalog/network error, 3 disk/permission error, 4 dependency unresolved.

---

## 5. Update Detection Algorithm

```
For each entry in manifest.installs:
    If addon uses releases (use_releases=true):
        latest = github.latest_release_tag(addon.github)
        If latest != installed.ref → mark for update
    Else (branch tracking):
        upstream_sha = github.branch_head_sha(addon.github, addon.branch)
        If upstream_sha != installed.sha → mark for update
```

Cache GitHub responses for 15 min in `~/.cache/ezwow/github-cache.json` with ETag. Authenticated PAT raises limit from 60/hr to 5000/hr.

---

## 6. Backup / Restore

- `core.backup.create()` → tar.gz of `<AddOns>/` (excludes `.ezwow-manifest.json` if requested) + `<wow_root>/WTF/` (SavedVariables).
- Default location: user config dir, NOT inside the game folder — `%APPDATA%/ezwowaddon/backups/<ISO-timestamp>.tar.gz` (Windows), `~/.local/share/ezwowaddon/backups/...` (Linux). Configurable in Settings. Keeping backups outside the game folder prevents recursive-backup bloat and survives game-folder wipes.
- Auto-backup before "Apply preset", "Update All", "Remove all" — opt-in but ON by default.
- `core.backup.restore(path)` → extract to AddOns/WTF, prompt before overwrite.

---

## 7. Error Handling

- Network errors during install → catch, surface specific error in UI ("GitHub returned 403 — rate limited; add a PAT in Settings").
- Partial extract (zip corrupted mid-download) → delete tmp dir, do NOT touch existing install. Manifest entry only written after successful extract.
- Dep cycle in catalog → `deps.resolve()` raises `CycleError` with the cycle path. CI catalog-check rejects PRs with cycles.
- Rate limit hit → fall back to direct branch tarball download (which doesn't count against API limit). Fallback is logged in status bar + log file — not silent.
- Folder paths missing/wrong → all installer ops short-circuit with explicit error; UI shows red banner directing to Settings.

**No silent fallbacks.** Failures surface visibly with actionable next steps.

---

## 8. Testing Strategy

- **Unit:** `catalog.schema`, `core.deps`, `core.manifest`, `core.detector`, `core.profile` — pure logic, no I/O. `core.github` mocked via `responses` library.
- **Integration:** `core.installer` against a local HTTP fixture serving fixture zips (no GitHub network in CI). Covers the download → extract → manifest write path.
- **CLI:** `tests/test_cli.py` invokes `ezwow.cli.main([...])`, asserts exit code + stdout.
- **GUI smoke (optional):** headless Tkinter via `xvfb-run` in Linux CI; confirms imports + window creates.
- **Catalog validation:** `tests/test_catalog_schema.py` loads bundled `addons.json`, asserts every entry parses + every dep resolves + every category exists.
- Coverage target: ≥70% on `ezwow.core.*`, ≥50% overall (UI excluded from gate).

---

## 9. CI / CD Changes

**`.github/workflows/build.yml`:**
- Drop `build-macos` job entirely.
- Update Python setup to 3.12 (3.x is too vague).
- Add `--collect-all customtkinter` to PyInstaller args.
- Pin actions versions (no `@v3` floats — use `@v4` minimum, pin SHA on push to org repo).

**`.github/workflows/ci.yml` (new):**
- Run on PR + push to main: `ruff check`, `mypy ezwow`, `pytest --cov=ezwow.core --cov-fail-under=70`.

**`.github/workflows/catalog-check.yml` (new):**
- Cron: nightly. For each addon URL, HEAD-request the GitHub repo + branch tarball URL. Open issue if any 404/410.

**Per CLAUDE.md absolute directives:**
- No `actions/attest-build-provenance` (already not present — verify).
- No macOS targets (removing).
- Run `orchestrator-enterprise scan .github/workflows/` before any push.

---

## 10. Migration & Backwards Compatibility

- v1 config file `ezwow_config.json` → migrate on first v2 launch to `~/.config/ezwowaddon/config.json` (Linux) or `%APPDATA%/ezwowaddon/config.json` (Windows). Keep reading old location as fallback for one release.
- Existing v1-installed addons (no manifest) → on first v2 launch, scan AddOns folder, match folder names against catalog, build retroactive manifest with `sha=null` (forces "update available" prompt).
- `ezwow.py` keeps working as entrypoint; PyInstaller spec updated to point at new package entry.

---

## 11. Build & Release

- `pyproject.toml` with `setuptools` backend; declares `ezwowaddon` package, console_scripts `ezwow=ezwow.__main__:main`.
- PyPI publish on tag push (NEW workflow `release.yml`, manual trigger initially to avoid accidental publish).
- PyInstaller produces `ezwow.exe` (Win) + `ezwow` (Linux) on tag push (existing workflow, modified).
- Version source: `ezwow/__init__.py::__version__` — single source of truth; bumped via `bump-my-version` or manual.

---

## 12. Security / Trust Considerations

- Catalog entries point at specific GitHub repos. Catalog PRs require maintainer review (CODEOWNERS already enforces this per recent commits).
- No execution of downloaded code — only file extraction.
- Optional GitHub PAT stored via `keyring` (system credential store), not plain config. Fallback to plain config with warning if `keyring` unavailable.
- HTTPS only for all downloads. Verify SSL certs (default in `requests`).
- Zip extraction guards against zip-slip: reject any member path containing `..` or absolute paths.

---

## 13. Catalog Initial Population (≥40 addons)

**UI:** pfUI, ShaguTweaks, ShaguPlates, MoveAnything, Turtle Dragonflight UI, NewLevelFrame
**Quest/Map:** pfQuest, pfQuest-Turtle, pfExtend, Cartographer, Cromulent's Map, ModernMapMarkers
**Combat:** BigWigs, ShaguDPS, DPSMate, TWW Threat, Classic Snowfall, SP Swing Timer, Proc Doc, Attack Bar
**Auction:** Aux, Auctionator
**Inventory/Mail:** Bagnon, BagShui, Turtle Mail
**Raid/Dungeon:** Atlas Turtle, Atlas Loot Turtle, Atlas Quest Turtle
**Social:** WIM, GlobalFriendsList, Friend-O-Tron
**Utility:** Restbar, BetterCharacterStats, Pet XP Bar, Minimap Button Bag, Level Range, MissingCrafts, MasterTradeSkills, ItemTooltipIcons, VoiceOver, PizzaWorldBuffs

**Client Mods:** VanillaFixes, SuperWoW, Nampower, UnitXP SP3, VanillaTweaks, PerfBoost

Initial `catalog/addons.json` populated by hand; subsequent additions via PR.

---

## 14. Open Questions / Risks

| Risk | Mitigation |
|---|---|
| GitHub anonymous rate limit during update-all on large installs | ETag cache + per-repo HEAD caching; PAT recommended; fall back to tarball download (no API). |
| CustomTkinter PyInstaller asset packaging | `--collect-all customtkinter`; verified locally before CI. |
| Catalog drift (renamed/abandoned repos) | Nightly catalog-check workflow opens issues. |
| MPQ install path differs across launcher/classic install | Detector returns both; user picks in Settings if ambiguous. |
| Rollback if extraction crashes mid-stream | Atomic install: extract to tmp, then rename into place; manifest only after success. |

---

## 15. Implementation Phases

The plan that follows this spec will break work into ordered phases. Approximate order:

1. Package skeleton + `pyproject.toml` + tooling (ruff, mypy, pytest).
2. `catalog.schema` + `catalog.loader` + bundled `addons.json` (≥40 entries).
3. `core.detector` + `core.github` + `core.manifest` (with tests).
4. `core.installer` + `core.backup` + integration tests.
5. `core.updater` + `core.deps` + `core.profile`.
6. CLI (`ezwow.cli`).
7. UI (CustomTkinter) — port v1 tabs first, then add Updates/Profiles/Client Mods.
8. CI overhaul (drop macOS, add ci.yml + catalog-check.yml).
9. README + CONTRIBUTING + CHANGELOG.
10. Tag v2.0.0; verify binaries built; PyPI publish (manual first run).

Each phase ends with passing tests + green CI before moving on.
