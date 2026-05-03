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
    b.mkdir(parents=True)
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
