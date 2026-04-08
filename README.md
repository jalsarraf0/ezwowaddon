# EZWowAddon

Lightweight GUI addon manager for [Turtle WoW](https://turtle-wow.org/) (1.12 client).

## Overview

EZWowAddon lets you install, update, and remove World of Warcraft addons from GitHub without manually downloading ZIP files or navigating game folders. It targets Turtle WoW specifically and is not compatible with Retail or Classic WoW.

The app is a single Python script backed by Tkinter. It ships as a self-contained executable for Windows and Linux via PyInstaller.

## Features

- Graphical interface with four tabs: Settings, Recommended Addons, Install from URL, Manage Installed
- One-click install for six pre-configured popular addons
- Install any addon by pasting a GitHub repository URL
- Auto-detects your Turtle WoW AddOns folder on Windows and WINE
- Remembers your AddOns folder between sessions
- Shows installed/not-installed status for each recommended addon
- Remove installed addons from the Manage tab
- Downloads run on a background thread so the UI stays responsive

## Built-In Recommended Addons

| Addon | Description |
|---|---|
| pfQuest | Quest helper with in-game map markers |
| pfQuest-Turtle | Turtle WoW-specific quest data for pfQuest |
| BigWigs | Boss warnings and ability timers |
| ShaguTweaks | Quality-of-life enhancements for 1.12 |
| Auctionator | Simplified auction house UI |
| Aux | Advanced auction house addon for Vanilla |

## Download

Go to the [Releases page](https://github.com/jalsarraf0/ezwowaddon/releases) and download the latest binary for your platform.

**Linux / macOS:**
```bash
curl -fsSL https://github.com/jalsarraf0/ezwowaddon/releases/latest/download/ezwow -o ezwow && chmod +x ezwow
./ezwow
```

**Windows (PowerShell):**
```powershell
Invoke-WebRequest -Uri https://github.com/jalsarraf0/ezwowaddon/releases/latest/download/ezwow.exe -OutFile ezwow.exe
.\ezwow.exe
```

## Run from Source

Requires Python 3.11+.

```bash
git clone https://github.com/jalsarraf0/ezwowaddon.git
cd ezwowaddon
pip install requests
python ezwow.py
```

## Build Executable Locally

```bash
pip install requests pyinstaller
pyinstaller --noconfirm --onefile --windowed ezwow.py
```

The output binary is placed in `dist/`.

## Dependencies

- Python 3.11+
- [requests](https://pypi.org/project/requests/)
- tkinter (included in the Python standard library)

## License

MIT License — Copyright (c) 2025 Jamal Al-Sarraf
