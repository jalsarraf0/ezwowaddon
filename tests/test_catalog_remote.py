"""Tests for catalog.remote with HTTP mocked."""

from __future__ import annotations

import pathlib

import responses

from ezwow.catalog import remote

REMOTE_URL = (
    "https://raw.githubusercontent.com/jalsarraf0/ezwowaddon/main/catalog/addons.json"
)


@responses.activate
def test_fetch_returns_catalog_when_200(tmp_path: pathlib.Path):
    body = (
        '{"schema_version":2,"updated":"2026-05-03","categories":[],'
        '"addons":[],"client_mods":[],"presets":{}}'
    )
    responses.add(responses.GET, REMOTE_URL, body=body, status=200, headers={"ETag": "abc"})
    cat = remote.fetch_remote(REMOTE_URL, cache_dir=tmp_path)
    assert cat is not None
    assert cat.schema_version == 2
    assert (tmp_path / "remote-catalog.json").exists()
    assert (tmp_path / "remote-catalog.etag").read_text() == "abc"


@responses.activate
def test_fetch_returns_cached_on_304(tmp_path: pathlib.Path):
    (tmp_path / "remote-catalog.json").write_text(
        '{"schema_version":2,"updated":"2026-05-03","categories":[],'
        '"addons":[],"client_mods":[],"presets":{}}'
    )
    (tmp_path / "remote-catalog.etag").write_text("abc")
    responses.add(responses.GET, REMOTE_URL, status=304)
    cat = remote.fetch_remote(REMOTE_URL, cache_dir=tmp_path)
    assert cat is not None
    assert cat.schema_version == 2


@responses.activate
def test_fetch_returns_none_on_network_error(tmp_path: pathlib.Path):
    responses.add(
        responses.GET,
        REMOTE_URL,
        body=ConnectionError("boom"),
    )
    assert remote.fetch_remote(REMOTE_URL, cache_dir=tmp_path) is None


@responses.activate
def test_fetch_returns_none_on_500(tmp_path: pathlib.Path):
    responses.add(responses.GET, REMOTE_URL, status=500)
    assert remote.fetch_remote(REMOTE_URL, cache_dir=tmp_path) is None
