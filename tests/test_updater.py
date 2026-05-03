"""Tests for updater plan generation."""

from __future__ import annotations

import datetime as dt
import pathlib
from unittest.mock import MagicMock

from ezwow.catalog.schema import Addon, Catalog, Category
from ezwow.core import manifest, updater
from ezwow.core.manifest import InstallEntry


def _cat(addons: list[Addon]) -> Catalog:
    return Catalog(
        schema_version=2,
        updated="2026-05-03",
        categories=[Category(id="x", label="X")],
        addons=addons,
        client_mods=[],
        presets={},
    )


def _entry(addon_id: str, sha: str | None) -> InstallEntry:
    return InstallEntry(
        addon_id=addon_id,
        folder=addon_id,
        source=f"github:x/{addon_id}",
        ref="master",
        sha=sha,
        installed_at=dt.datetime(2026, 5, 3, tzinfo=dt.UTC),
        files=(),
        size_bytes=0,
    )


def test_plan_marks_outdated_branch_install(fake_addons_folder: pathlib.Path):
    addon = Addon(
        id="a", name="A", category="x", description="", author="", github="x/a", folder="A"
    )
    manifest.record(fake_addons_folder, _entry("a", "old-sha"))

    gh = MagicMock()
    gh.branch_head_sha.return_value = "new-sha"

    plan = updater.plan(
        addons_folder=fake_addons_folder, catalog=_cat([addon]), gh_client=gh
    )
    assert [u.addon_id for u in plan.updates] == ["a"]
    assert plan.updates[0].current == "old-sha"
    assert plan.updates[0].latest == "new-sha"


def test_plan_skips_uptodate(fake_addons_folder: pathlib.Path):
    addon = Addon(
        id="a", name="A", category="x", description="", author="", github="x/a", folder="A"
    )
    manifest.record(fake_addons_folder, _entry("a", "same"))
    gh = MagicMock()
    gh.branch_head_sha.return_value = "same"
    plan = updater.plan(
        addons_folder=fake_addons_folder, catalog=_cat([addon]), gh_client=gh
    )
    assert plan.updates == []


def test_plan_with_unknown_sha_marks_for_update(fake_addons_folder: pathlib.Path):
    addon = Addon(
        id="a", name="A", category="x", description="", author="", github="x/a", folder="A"
    )
    manifest.record(fake_addons_folder, _entry("a", None))
    gh = MagicMock()
    gh.branch_head_sha.return_value = "anything"
    plan = updater.plan(
        addons_folder=fake_addons_folder, catalog=_cat([addon]), gh_client=gh
    )
    assert plan.updates[0].current is None
