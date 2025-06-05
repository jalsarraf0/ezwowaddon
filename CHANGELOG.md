# 📄 Changelog

All notable changes to **EZWowAddon** will be documented in this file.

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
