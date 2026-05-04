"""Tests for the install pipeline composition."""

from __future__ import annotations

import http.server
import pathlib
import socketserver
import threading
from collections.abc import Iterator
from unittest.mock import MagicMock

import pytest

from ezwow.catalog.schema import Addon
from ezwow.core import manifest, pipeline


@pytest.fixture
def http_fixture() -> Iterator[str]:
    docroot = pathlib.Path(__file__).parent / "data"

    class Handler(http.server.SimpleHTTPRequestHandler):
        def __init__(self, *a: object, **kw: object) -> None:
            super().__init__(*a, directory=str(docroot), **kw)  # type: ignore[arg-type]

        def log_message(self, format: str, *args: object) -> None:
            del format, args

    with socketserver.TCPServer(("127.0.0.1", 0), Handler) as srv:
        port = srv.server_address[1]
        t = threading.Thread(target=srv.serve_forever, daemon=True)
        t.start()
        try:
            yield f"http://127.0.0.1:{port}"
        finally:
            srv.shutdown()


def _addon_against(http_fixture: str) -> Addon:
    """Build an Addon whose branch_zip_url() points at our local HTTP fixture."""

    class _UrlOverride(Addon):
        def branch_zip_url(self) -> str:
            return f"{http_fixture}/sample-addon-master.zip"

    return _UrlOverride(
        id="sample",
        name="Sample",
        category="utility",
        description="d",
        author="a",
        github="x/y",
        branch="master",
        folder="SampleAddon",
    )


def test_install_addon_records_manifest(
    http_fixture: str, fake_addons_folder: pathlib.Path
):
    addon = _addon_against(http_fixture)
    gh = MagicMock()
    gh.branch_head_sha.return_value = "deadbeef"

    entry = pipeline.install_addon(
        addon=addon, addons_folder=fake_addons_folder, gh_client=gh
    )

    assert entry.addon_id == "sample"
    assert entry.sha == "deadbeef"
    assert (fake_addons_folder / "SampleAddon" / "SampleAddon.toc").exists()
    loaded = manifest.load(fake_addons_folder)
    assert "sample" in loaded.installs


def test_update_addon_uses_provided_sha_when_known(
    http_fixture: str, fake_addons_folder: pathlib.Path
):
    addon = _addon_against(http_fixture)
    gh = MagicMock()

    entry = pipeline.update_addon_to_sha(
        addon=addon,
        addons_folder=fake_addons_folder,
        gh_client=gh,
        target_sha="newsha",
    )

    assert entry.sha == "newsha"
    gh.branch_head_sha.assert_not_called()


def test_update_addon_falls_back_to_gh_when_sha_none(
    http_fixture: str, fake_addons_folder: pathlib.Path
):
    addon = _addon_against(http_fixture)
    gh = MagicMock()
    gh.branch_head_sha.return_value = "fetchedsha"

    entry = pipeline.update_addon_to_sha(
        addon=addon,
        addons_folder=fake_addons_folder,
        gh_client=gh,
        target_sha=None,
    )

    assert entry.sha == "fetchedsha"
    gh.branch_head_sha.assert_called_once()
