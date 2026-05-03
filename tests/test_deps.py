"""Tests for dependency resolution."""

from __future__ import annotations

import pytest

from ezwow.catalog.schema import Addon, Catalog, Category
from ezwow.core import deps


def _make_catalog(addons: list[Addon]) -> Catalog:
    return Catalog(
        schema_version=2,
        updated="2026-05-03",
        categories=[Category(id="x", label="X")],
        addons=addons,
        client_mods=[],
        presets={},
    )


def _addon(id_: str, depends: tuple[str, ...] = ()) -> Addon:
    return Addon(
        id=id_,
        name=id_,
        category="x",
        description="",
        author="",
        github="x/y",
        folder=id_,
        depends=depends,
    )


def test_resolve_no_deps():
    cat = _make_catalog([_addon("a")])
    assert deps.resolve(["a"], cat) == ["a"]


def test_resolve_topo_order():
    cat = _make_catalog(
        [
            _addon("a", ()),
            _addon("b", ("a",)),
            _addon("c", ("b",)),
        ]
    )
    assert deps.resolve(["c"], cat) == ["a", "b", "c"]


def test_resolve_pulls_transitive():
    cat = _make_catalog(
        [
            _addon("base", ()),
            _addon("ext", ("base",)),
        ]
    )
    out = deps.resolve(["ext"], cat)
    assert out == ["base", "ext"]


def test_resolve_dedupes_when_already_in_input():
    cat = _make_catalog([_addon("a"), _addon("b", ("a",))])
    assert deps.resolve(["a", "b"], cat) == ["a", "b"]


def test_resolve_raises_on_cycle():
    cat = _make_catalog(
        [
            _addon("a", ("b",)),
            _addon("b", ("a",)),
        ]
    )
    with pytest.raises(deps.CycleError):
        deps.resolve(["a"], cat)


def test_resolve_raises_on_unknown():
    cat = _make_catalog([_addon("a")])
    with pytest.raises(KeyError):
        deps.resolve(["unknown"], cat)
