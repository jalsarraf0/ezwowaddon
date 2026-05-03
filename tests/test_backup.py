"""Tests for backup/restore."""

from __future__ import annotations

import pathlib

import pytest

from ezwow.core import backup


def test_create_and_restore_roundtrip(
    fake_wow_root: pathlib.Path, tmp_path: pathlib.Path
):
    addons = fake_wow_root / "Interface" / "AddOns"
    (addons / "FooAddon").mkdir()
    (addons / "FooAddon" / "Foo.toc").write_text("hello")
    wtf_dir = fake_wow_root / "WTF" / "Account" / "TEST" / "SavedVariables"
    (wtf_dir / "FooAddon.lua").write_text("saved=1")

    out_dir = tmp_path / "backups"
    archive = backup.create_backup(wow_root=fake_wow_root, out_dir=out_dir)
    assert archive.exists()
    assert archive.suffix == ".gz"

    (addons / "FooAddon" / "Foo.toc").unlink()
    (wtf_dir / "FooAddon.lua").unlink()

    backup.restore_backup(archive=archive, wow_root=fake_wow_root)
    assert (addons / "FooAddon" / "Foo.toc").read_text() == "hello"
    assert (wtf_dir / "FooAddon.lua").read_text() == "saved=1"


def test_create_skips_when_addons_missing(tmp_path: pathlib.Path):
    with pytest.raises(backup.BackupError):
        backup.create_backup(
            wow_root=tmp_path / "nope",
            out_dir=tmp_path / "out",
        )
