"""Validate that the bundled catalog parses and contains required entries."""

from __future__ import annotations

import json
import pathlib

import pytest

from ezwow.catalog.schema import parse_catalog

REPO_ROOT = pathlib.Path(__file__).resolve().parents[1]
BUNDLED = REPO_ROOT / "ezwow" / "catalog" / "data" / "addons.json"
CANONICAL = REPO_ROOT / "catalog" / "addons.json"


def test_canonical_catalog_parses():
    raw = json.loads(CANONICAL.read_text(encoding="utf-8"))
    cat = parse_catalog(raw)
    assert len(cat.addons) >= 40, f"need >=40 addons, got {len(cat.addons)}"
    assert len(cat.client_mods) >= 6, f"need >=6 client mods, got {len(cat.client_mods)}"


def test_bundled_matches_canonical():
    bundled = BUNDLED.read_text(encoding="utf-8")
    canonical = CANONICAL.read_text(encoding="utf-8")
    assert bundled == canonical, "bundled JSON drifted from catalog/addons.json"


@pytest.mark.parametrize("preset_id", ["essential", "raider", "hardcore", "minimal-ui"])
def test_required_presets_exist(preset_id: str):
    raw = json.loads(CANONICAL.read_text(encoding="utf-8"))
    cat = parse_catalog(raw)
    assert preset_id in cat.presets


def test_legacy_v1_addons_still_present():
    raw = json.loads(CANONICAL.read_text(encoding="utf-8"))
    cat = parse_catalog(raw)
    legacy_ids = {"pfquest", "pfquest-turtle", "bigwigs", "shagu-tweaks", "auctionator", "aux"}
    cat_ids = {a.id for a in cat.addons}
    missing = legacy_ids - cat_ids
    assert not missing, f"v1 addons missing in v2 catalog: {missing}"
