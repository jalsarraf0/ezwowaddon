#!/usr/bin/env bash
set -euo pipefail

# Build the EZWowAddon executable
rm -rf build dist
pyinstaller --noconfirm --onefile --windowed ezwow.py