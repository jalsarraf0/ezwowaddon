"""Tests for install manifest persistence."""

from __future__ import annotations

import datetime as dt
import pathlib

from ezwow.core import manifest


def test_record_and_load_roundtrip(fake_addons_folder: pathlib.Path):
    entry = manifest.InstallEntry(
        addon_id="pfquest",
        folder="pfQuest",
        source="github:shagu/pfQuest",
        ref="master",
        sha="abc",
        installed_at=dt.datetime(2026, 5, 3, tzinfo=dt.UTC),
        files=("pfQuest/pfQuest.toc",),
        size_bytes=1234,
    )
    manifest.record(fake_addons_folder, entry)
    loaded = manifest.load(fake_addons_folder)
    assert "pfquest" in loaded.installs
    assert loaded.installs["pfquest"].sha == "abc"


def test_load_empty_when_missing(fake_addons_folder: pathlib.Path):
    m = manifest.load(fake_addons_folder)
    assert m.installs == {}


def test_remove_entry(fake_addons_folder: pathlib.Path):
    entry = manifest.InstallEntry(
        addon_id="x",
        folder="X",
        source="src",
        ref="master",
        sha="s",
        installed_at=dt.datetime(2026, 5, 3, tzinfo=dt.UTC),
        files=(),
        size_bytes=0,
    )
    manifest.record(fake_addons_folder, entry)
    manifest.remove(fake_addons_folder, "x")
    assert manifest.load(fake_addons_folder).installs == {}


def test_corrupt_manifest_resets(fake_addons_folder: pathlib.Path):
    (fake_addons_folder / ".ezwow-manifest.json").write_text("{not json")
    m = manifest.load(fake_addons_folder)
    assert m.installs == {}
