"""Load catalog data from disk or remote source."""

from __future__ import annotations

import json
import pathlib
from importlib.resources import files

from ezwow.catalog.schema import Catalog, SchemaError, parse_catalog


class CatalogLoadError(RuntimeError):
    """Raised when catalog cannot be loaded or parsed."""


def load_bundled() -> Catalog:
    """Load the catalog shipped inside the package."""
    path = files("ezwow.catalog").joinpath("data/addons.json")
    with path.open("r", encoding="utf-8") as fp:
        raw = json.load(fp)
    try:
        return parse_catalog(raw)
    except SchemaError as exc:
        raise CatalogLoadError(f"bundled catalog invalid: {exc}") from exc


def load_from_path(path: pathlib.Path) -> Catalog:
    """Load and parse a catalog JSON from a filesystem path."""
    if not path.exists():
        raise FileNotFoundError(f"catalog not found at {path}")
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise CatalogLoadError(f"catalog JSON malformed at {path}: {exc}") from exc
    try:
        return parse_catalog(raw)
    except SchemaError as exc:
        raise CatalogLoadError(f"catalog schema invalid at {path}: {exc}") from exc
