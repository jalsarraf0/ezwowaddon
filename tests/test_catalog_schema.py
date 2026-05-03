"""Tests for ezwow.catalog.schema."""

from __future__ import annotations

import pytest

from ezwow.catalog.schema import (
    Addon,
    Catalog,
    Category,
    SchemaError,
    parse_catalog,
)

VALID_RAW = {
    "schema_version": 2,
    "updated": "2026-05-03",
    "categories": [
        {"id": "ui", "label": "UI / Interface"},
        {"id": "quest", "label": "Quest & Map"},
    ],
    "addons": [
        {
            "id": "pfquest",
            "name": "pfQuest",
            "category": "quest",
            "description": "Quest helper",
            "author": "shagu",
            "github": "shagu/pfQuest",
            "branch": "master",
            "use_releases": False,
            "folder": "pfQuest",
            "depends": [],
            "tags": ["essential"],
        }
    ],
    "client_mods": [
        {
            "id": "vanillafixes",
            "name": "VanillaFixes",
            "description": "Stutter fix",
            "github": "RetroCro/TurtleWoW-Mods",
            "asset_pattern": "VanillaFixes*.zip",
            "install_to": "data_root",
            "files_to_install": ["*.exe", "*.dll"],
            "tags": ["essential"],
        }
    ],
    "presets": {
        "essential": {
            "label": "Essential",
            "addons": ["pfquest"],
            "client_mods": ["vanillafixes"],
        }
    },
}


def test_parse_valid_catalog():
    cat = parse_catalog(VALID_RAW)
    assert isinstance(cat, Catalog)
    assert cat.schema_version == 2
    assert cat.categories == [
        Category(id="ui", label="UI / Interface"),
        Category(id="quest", label="Quest & Map"),
    ]
    assert len(cat.addons) == 1
    assert isinstance(cat.addons[0], Addon)
    assert cat.addons[0].id == "pfquest"
    assert cat.client_mods[0].install_to == "data_root"
    assert "essential" in cat.presets
    assert cat.presets["essential"].addons == ("pfquest",)


def test_parse_rejects_wrong_schema_version():
    raw = {**VALID_RAW, "schema_version": 1}
    with pytest.raises(SchemaError, match="schema_version"):
        parse_catalog(raw)


def test_parse_rejects_unknown_category():
    raw = dict(VALID_RAW)
    raw["addons"] = [{**VALID_RAW["addons"][0], "category": "nonexistent"}]
    with pytest.raises(SchemaError, match="category"):
        parse_catalog(raw)


def test_parse_rejects_dep_to_unknown_addon():
    raw = dict(VALID_RAW)
    raw["addons"] = [{**VALID_RAW["addons"][0], "depends": ["does-not-exist"]}]
    with pytest.raises(SchemaError, match="depends"):
        parse_catalog(raw)


def test_parse_rejects_invalid_id_format():
    raw = dict(VALID_RAW)
    raw["addons"] = [{**VALID_RAW["addons"][0], "id": "PFQuest_BAD"}]
    with pytest.raises(SchemaError, match="id"):
        parse_catalog(raw)


def test_addon_get_branch_url():
    addon = parse_catalog(VALID_RAW).addons[0]
    assert addon.branch_zip_url() == (
        "https://github.com/shagu/pfQuest/archive/refs/heads/master.zip"
    )


def test_preset_resolves_unknown_addon_raises():
    raw = dict(VALID_RAW)
    raw["presets"] = {"bad": {"label": "Bad", "addons": ["nope"], "client_mods": []}}
    with pytest.raises(SchemaError, match="preset"):
        parse_catalog(raw)
