"""Tests for profile import/export."""

from __future__ import annotations

import json
import pathlib

from ezwow.catalog.schema import Addon, Catalog, Category, Preset
from ezwow.core import profile


def _cat() -> Catalog:
    return Catalog(
        schema_version=2,
        updated="2026-05-03",
        categories=[Category(id="x", label="X")],
        addons=[
            Addon(
                id="a",
                name="A",
                category="x",
                description="",
                author="",
                github="x/a",
                folder="A",
            ),
            Addon(
                id="b",
                name="B",
                category="x",
                description="",
                author="",
                github="x/b",
                folder="B",
            ),
        ],
        client_mods=[],
        presets={"p": Preset(id="p", label="P", addons=("a", "b"))},
    )


def test_resolve_preset_returns_addon_ids():
    cat = _cat()
    plan = profile.resolve_preset("p", cat)
    assert plan.addon_ids == ["a", "b"]


def test_export_profile_writes_json(tmp_path: pathlib.Path):
    out = tmp_path / "profile.json"
    profile.export_profile(
        out_path=out, addon_ids=["a", "b"], client_mod_ids=[], label="custom"
    )
    raw = json.loads(out.read_text())
    assert raw["label"] == "custom"
    assert raw["addons"] == ["a", "b"]


def test_import_profile_returns_lists(tmp_path: pathlib.Path):
    src = tmp_path / "profile.json"
    src.write_text(json.dumps({"label": "x", "addons": ["a"], "client_mods": ["b"]}))
    p = profile.import_profile(src)
    assert p.label == "x"
    assert p.addons == ["a"]
    assert p.client_mods == ["b"]


def test_resolve_preset_raises_on_unknown_id():
    import pytest

    cat = _cat()
    with pytest.raises(KeyError, match="unknown preset"):
        profile.resolve_preset("does-not-exist", cat)
