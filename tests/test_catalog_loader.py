"""Tests for catalog.loader."""

from __future__ import annotations

import json
import pathlib

import pytest

from ezwow.catalog import loader


def test_load_bundled_returns_catalog():
    cat = loader.load_bundled()
    assert cat.schema_version == 2
    assert len(cat.addons) >= 40


def test_load_from_path(tmp_path: pathlib.Path):
    src = tmp_path / "addons.json"
    src.write_text(
        json.dumps(
            {
                "schema_version": 2,
                "updated": "2026-05-03",
                "categories": [{"id": "ui", "label": "UI"}],
                "addons": [],
                "client_mods": [],
                "presets": {},
            }
        )
    )
    cat = loader.load_from_path(src)
    assert cat.addons == []


def test_load_from_path_missing_raises(tmp_path: pathlib.Path):
    with pytest.raises(FileNotFoundError):
        loader.load_from_path(tmp_path / "nope.json")


def test_load_from_path_invalid_json_raises(tmp_path: pathlib.Path):
    src = tmp_path / "bad.json"
    src.write_text("{not json")
    with pytest.raises(loader.CatalogLoadError):
        loader.load_from_path(src)
