"""Fetch catalog from a remote URL with ETag-based conditional GET."""

from __future__ import annotations

import json
import logging
import pathlib

import requests

from ezwow.catalog.schema import Catalog, SchemaError, parse_catalog

DEFAULT_REMOTE_URL = (
    "https://raw.githubusercontent.com/jalsarraf0/ezwowaddon/main/catalog/addons.json"
)
TIMEOUT_SECONDS = 10
CACHE_FILE = "remote-catalog.json"
ETAG_FILE = "remote-catalog.etag"

log = logging.getLogger(__name__)


def fetch_remote(url: str = DEFAULT_REMOTE_URL, *, cache_dir: pathlib.Path) -> Catalog | None:
    """Fetch the remote catalog. Returns Catalog on success or cached hit; None on failure."""
    cache_dir.mkdir(parents=True, exist_ok=True)
    cache_path = cache_dir / CACHE_FILE
    etag_path = cache_dir / ETAG_FILE

    headers: dict[str, str] = {}
    if etag_path.exists() and cache_path.exists():
        headers["If-None-Match"] = etag_path.read_text(encoding="utf-8").strip()

    try:
        resp = requests.get(url, headers=headers, timeout=TIMEOUT_SECONDS)
    except (requests.RequestException, OSError) as exc:
        log.warning("remote catalog fetch failed: %s", exc)
        return None

    if resp.status_code == 304 and cache_path.exists():
        return _parse_cached(cache_path)

    if resp.status_code != 200:
        log.warning("remote catalog returned %d", resp.status_code)
        return None

    text = resp.text
    try:
        raw = json.loads(text)
        cat = parse_catalog(raw)
    except (json.JSONDecodeError, SchemaError) as exc:
        log.warning("remote catalog invalid: %s", exc)
        return None

    cache_path.write_text(text, encoding="utf-8")
    new_etag = resp.headers.get("ETag", "").strip()
    etag_path.write_text(new_etag, encoding="utf-8")
    return cat


def _parse_cached(cache_path: pathlib.Path) -> Catalog | None:
    try:
        raw = json.loads(cache_path.read_text(encoding="utf-8"))
        return parse_catalog(raw)
    except (json.JSONDecodeError, SchemaError) as exc:
        log.warning("cached catalog invalid, dropping: %s", exc)
        cache_path.unlink(missing_ok=True)
        return None
