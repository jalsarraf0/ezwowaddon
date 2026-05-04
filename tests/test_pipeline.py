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


def _addon_against(http_fixture: str, branch: str | None = "master") -> Addon:
    """Build an Addon whose branch_zip_url() points at our local HTTP fixture."""

    class _UrlOverride(Addon):
        def branch_zip_url(self, branch: str | None = None) -> str:
            del branch
            return f"{http_fixture}/sample-addon-master.zip"

    return _UrlOverride(
        id="sample",
        name="Sample",
        category="utility",
        description="d",
        author="a",
        github="x/y",
        branch=branch,
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
    assert entry.ref == "master"
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


def test_resolve_branch_uses_explicit_catalog_branch():
    addon = Addon(
        id="x",
        name="X",
        category="utility",
        description="",
        author="",
        github="o/r",
        branch="dev",
        folder="X",
    )
    gh = MagicMock()
    gh.default_branch.return_value = "main"
    assert pipeline.resolve_branch(addon, gh) == "dev"
    gh.default_branch.assert_not_called()


def test_resolve_branch_queries_github_when_branch_omitted():
    addon = Addon(
        id="x",
        name="X",
        category="utility",
        description="",
        author="",
        github="o/r",
        branch=None,
        folder="X",
    )
    gh = MagicMock()
    gh.default_branch.return_value = "main"
    assert pipeline.resolve_branch(addon, gh) == "main"
    gh.default_branch.assert_called_once_with("o/r")


def test_resolve_branch_falls_back_to_master_when_github_unavailable():
    addon = Addon(
        id="x",
        name="X",
        category="utility",
        description="",
        author="",
        github="o/r",
        branch=None,
        folder="X",
    )
    gh = MagicMock()
    gh.default_branch.return_value = None
    assert pipeline.resolve_branch(addon, gh) == "master"


def test_install_addon_uses_resolved_branch_when_catalog_branch_omitted(
    http_fixture: str, fake_addons_folder: pathlib.Path
):
    addon = _addon_against(http_fixture, branch=None)
    gh = MagicMock()
    gh.default_branch.return_value = "main"
    gh.branch_head_sha.return_value = "abc"

    entry = pipeline.install_addon(
        addon=addon, addons_folder=fake_addons_folder, gh_client=gh
    )

    assert entry.ref == "main"
    gh.branch_head_sha.assert_called_once_with("x/y", "main")
