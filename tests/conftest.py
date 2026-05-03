"""Shared test fixtures."""

from __future__ import annotations

import pathlib
from collections.abc import Iterator

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
