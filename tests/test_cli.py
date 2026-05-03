"""End-to-end tests for the CLI surface."""

from __future__ import annotations

import pathlib

import pytest

from ezwow.catalog.schema import Catalog, parse_catalog
from ezwow.cli import run


@pytest.fixture
def fake_catalog(monkeypatch: pytest.MonkeyPatch) -> Catalog:
    raw = {
        "schema_version": 2,
        "updated": "2026-05-03",
        "categories": [{"id": "x", "label": "X"}],
        "addons": [
            {
                "id": "a",
                "name": "A",
                "category": "x",
                "description": "d",
                "author": "u",
                "github": "x/a",
                "folder": "A",
            },
        ],
        "client_mods": [],
        "presets": {"p": {"label": "P", "addons": ["a"], "client_mods": []}},
    }
    cat = parse_catalog(raw)
    monkeypatch.setattr("ezwow.catalog.loader.load_bundled", lambda: cat)
    return cat


def test_cli_list_prints_addon_ids(
    capsys: pytest.CaptureFixture[str],
    fake_catalog: Catalog,
    isolated_config: pathlib.Path,
):
    rc = run(["list"])
    assert rc == 0
    out = capsys.readouterr().out
    assert "a" in out


def test_cli_no_args_returns_error(
    capsys: pytest.CaptureFixture[str],
    fake_catalog: Catalog,
    isolated_config: pathlib.Path,
):
    rc = run([])
    assert rc == 1


def test_cli_doctor_prints_paths(
    capsys: pytest.CaptureFixture[str],
    fake_catalog: Catalog,
    isolated_config: pathlib.Path,
):
    rc = run(["doctor"])
    assert rc == 0
    out = capsys.readouterr().out
    assert "config" in out.lower()
