# 📄 Changelog

All notable changes to **EZWowAddon** will be documented in this file.

---

## [v1.0.0] – 2025-05-04

### ✨ Added

- New **Settings** tab to easily select and persist the AddOns folder
- **Recommended AddOns** tab now includes 6 curated, popular GitHub projects:
  - pfQuest
  - pfQuest-Turtle
  - BigWigs
  - LunaUnitFrames
  - ShaguTweaks
  - AtlasLootClassic
- **Automatic detection** of whether each recommended addon is installed or not
- **Button text and status labels** dynamically update based on addon state
- **Custom URL installer** supports direct GitHub repo links (auto-converts to ZIP)
- **Manage Installed** tab lists installed addons and allows clean uninstalls

### 🧼 Changed

- Fully refactored `ezwow.py` for modularity, readability, and maintainability
- Moved folder selection from menu to a **dedicated Settings tab**
- Standardized UI layout using `ttk` themed widgets

### 🐞 Fixed

- AddOn folders are now properly renamed to match expected structure
- Resolved multiple small UX issues and simplified onboarding

---

## [v0.5.0] – 2025-05-01

### Initial Release

- Simple GUI for installing pfQuest and pfQuest-Turtle
- Basic GitHub ZIP download and extract support
- Manual folder selection
- No state persistence, addon detection, or management features

---

> Maintained by Jamal Al-Sarraf — [https://github.com/jalsarraf0](https://github.com/jalsarraf0)

