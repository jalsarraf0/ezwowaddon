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
