# 📄 Changelog

All notable changes to **EZWowAddon** will be documented in this file.

---

## [v2.1.0] – 2026-05-03

### Added

- Catalog grew to **123 verified addons** (was 97 in v2.0.2). 26 more clusters surfaced via deeper research.
  - Turtle-WoW-specific: Tmog, DifficultBulletinBoard, QuickHeal, FanatiquesUI, BrainwasherPro, Rested, RestBar, IWINButton, Zorlen, ProcDoc (turtle), AutoBar (turtle), Necrosis (turtle), AntiSpam, ShaguBoat, DistanceDisplay, EzPoison, TheoryCraft (turtle), Gatherer (turtle).
  - yutsuku Vanilla cluster: Gamepad, BetterBabelFish, StealthOverlay, KLHThreatMeterBlizz, UITweaks, BuyPoisons.
  - OldManAlpha: FastTOT, UnitXP_SP3_Addon (companion to client mod).
- New `ezwow.core.pipeline` module: single `install_addon()` and `update_addon_to_sha()` entry points used by CLI + UI tabs.

### Changed

- **Refactor:** install pipeline deduplicated. CLI, Browse tab, and Updates tab no longer each rebuild the install dance — they call `pipeline.install_addon()` / `pipeline.update_addon_to_sha()`. ~80 LOC of duplication removed.
- Hardcore preset upgraded with real addons: friend-o-tron, color-social-frame, wim, auld-lang-syne, rested, klh-threat-meter.
- Raider preset adds quick-heal + klh-threat-meter.

### Coverage

- `ezwow.core` coverage now 91% (up from 90%); new `pipeline.py` 100% covered.

---

## [v2.0.2] – 2026-05-03

### Added

- 27 more verified addons. Catalog now 97 entries (was 70 in v2.0.1).
- New finds across 6 author clusters:
  - **wardz**: FocusFrame, FocusFrame TargetCastbar, Diminish, DispelBorder
  - **shirsig**: cdframes, cooline, aux_merchant_prices, sentry, notoggle, linkmend
  - **shagu**: ShaguScore, ShaguNotify
  - **Road-block**: SimpleCombatLog, Possessions, TriviaBot, PingoMatic, Interruptor, AuldLangSyne, RogueFocus
  - **cubenicke**: Fury (warrior), Mule
  - **wow-vanilla-addons** org: QuestItem, Accountant
  - Plus: Wiggen94/LootMonitor (Turtle-only), S4V4GENZ/TrinketMenu, mitjafelicijan/TurtleTweaks (Turtle-only), enn-wow-addons/HunterSwissKnife
- Presets enhanced: Raider gets cdframes/diminish/interruptor/trinket-menu; Essential gets accountant/quest-item.
- All 97/97 URLs HEAD-verified before ship.

---

## [v2.0.1] – 2026-05-03

### Fixed

- **Catalog rescue**: 31 of 40 addon URLs in v2.0.0 returned 404. Rebuilt the catalog from scratch with canonical repos verified via GitHub search. All entries HEAD-tested before ship.

### Added

- Catalog grew from 40 to 70 addons. Clusters added:
  - shagu's full Vanilla suite (ShaguActions, ShaguJunk, ShaguBoP, ShaguMail, ShaguClock, ShaguValue, ShaguMount, ShaguTooltips, ShaguChat, ShaguCopy, ShaguQuest, ShaguInventory, ShaguController, ShaguWidget, pfQuest-icons, Clique, ShaguScan)
  - shirsig's Vanilla cluster (Mail, WIM, ccwatch, SortBags, Cleanup, crafty, mouseover, retarget)
  - CosminPOP Turtle WoW updates (Atlas, AtlasLoot, PallyPower, TWLC2, TWThreat)
  - Road-block's Vanilla cluster (Cartographer, AttackBar, ClassicSnowFall, CustomNameplates, ColorSocialFrame, AutoProfit, CooldownTimers, SimpleRaidTargetIcons, ArchiTotem)
  - refaim's addons (MobStats, TrainerSkills, TradeSkillsData-turtle)
  - laytya's Vanilla cluster (ATSW, EQL3, Chronometer, Kui-Nameplates)
  - Plus Puppeteer (OldManAlpha), pfExtend (Cliencer), RallyHelper, Vanilla-NewLevelFrame, Vanilla-Iconic
- Presets updated to reference verified IDs.

---

## [v2.0.0] – 2026-05-03

### Added

- Full Python package rewrite: `ezwow/{catalog,core,ui,cli}` with strict types and tests.
- Curated catalog at `catalog/addons.json`: 40+ addons + 6 client mods, 4 presets (Essential, Raider, Hardcore, Minimal UI).
- Real update detection via Git SHA tracking + GitHub API ETag cache.
- Presets / profiles: one-click loadouts; custom JSON import/export.
- Backup / restore of AddOns + SavedVariables (tar.gz snapshots).
- CLI mode: `ezwow install`, `update`, `list`, `remove`, `doctor`, `backup`, `restore`, `profile`.
- CustomTkinter UI with side-nav, search, threaded installs, dark theme by default.
- Auto-detection of Turtle launcher install path (`%APPDATA%/TurtleWoW/`) in addition to classic install.
- Optional GitHub PAT for higher API rate limits.
- Atomic install with zip-slip protection.
- Nightly catalog URL smoke-test workflow.
- Dependency resolution: pfQuest-Turtle automatically pulls pfQuest.
- Client mods tab (VanillaFixes, SuperWoW, Nampower, UnitXP, VanillaTweaks, PerfBoost) — manual install for v2.0; auto-install slated for v2.1.

### Changed

- `ezwow.py` is now a thin shim over the `ezwow` package.
- CI: dropped macOS, upgraded to Python 3.12, `actions/*@v4`, added lint + type + coverage gate.
- Config moved to standard XDG/AppData locations (`~/.config/ezwowaddon/config.json` on Linux, `%APPDATA%/ezwowaddon/` on Windows).

### Removed

- macOS build target.

---

## [v1.0.7] – 2025-06-05

### 🚀 Packaging

- CI workflow now automatically builds and publishes one‑file executables for Windows, Linux, and macOS.
- CI: drop coverage.xml from artifact uploads to avoid missing-file failures

## [v1.0.6] – 2025-06-05

### ✨ Added / 🔧 Changed

- Background installs with progress bar.
- Improved folder detection logic.
- Added "Install All" button in the Recommended AddOns tab.
- Integrated CI binary builds into the GitHub Actions workflow.

## [v1.0.5] – 2025-05-04

### ✨ Changed

- **Recommended AddOns list updated**:
  - ✅ Added: `Auctionator`, `Aux`
  - ❌ Removed: `AtlasLootClassic`, `LunaUnitFrames`
- This change was made to streamline the list and focus on high-utility, lightweight addons.
- Internal `RECOMMENDED_ADDONS` data structure updated to reflect changes
- README.md and interface labels updated to match

> No major UI, config, or feature changes were introduced in this version.

---

## [v1.0.0] – 2025-05-04

### ✨ Added

- New **Settings** tab to configure the Turtle WoW AddOns folder
- GitHub-based one-click install for:
  - pfQuest
  - pfQuest-Turtle
  - BigWigs
  - ShaguTweaks
  - AtlasLootClassic
  - LunaUnitFrames
- Automatic detection of installed addons with "Install"/"Reinstall" buttons
- Config persistence: remembers selected AddOns folder
- Tabs for:
  - Recommended AddOns
  - Install from URL
  - Manage Installed
- Clean uninstall option with confirmation prompt

### 🔁 Changed

- Moved folder selection from the menu to a dedicated **Settings** tab
- Refactored the entire codebase into modular, maintainable structure
- Improved status feedback through a dedicated status bar

---

## [v0.5.0] – 2025-04-29

### 🚀 Initial Release

- Basic GUI with support for installing `pfQuest` and `pfQuest-Turtle`
- Manual folder selection via File menu
- GitHub ZIP download and extract
- No state persistence or addon detection
- No uninstall or addon management functionality

---

> Maintained by Jamal Al-Sarraf — [https://github.com/jalsarraf0](https://github.com/jalsarraf0)
