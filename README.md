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
