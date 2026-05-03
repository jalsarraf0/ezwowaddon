"""Tests for atomic install/extract."""

from __future__ import annotations

import http.server
import pathlib
import socketserver
import threading
from collections.abc import Iterator

import pytest

from ezwow.core import installer
from ezwow.core.installer import InstallError


@pytest.fixture
def http_fixture() -> Iterator[str]:
    """Serve tests/data/ via http on a random port."""
    docroot = pathlib.Path(__file__).parent / "data"

    class Handler(http.server.SimpleHTTPRequestHandler):
        def __init__(self, *a: object, **kw: object) -> None:
            super().__init__(*a, directory=str(docroot), **kw)  # type: ignore[arg-type]

        def log_message(self, format: str, *args: object) -> None:
            del format, args

    with socketserver.TCPServer(("127.0.0.1", 0), Handler) as srv:
        port = srv.server_address[1]
        thread = threading.Thread(target=srv.serve_forever, daemon=True)
        thread.start()
        try:
            yield f"http://127.0.0.1:{port}"
        finally:
            srv.shutdown()


def test_install_extracts_to_target_folder(
    http_fixture: str, fake_addons_folder: pathlib.Path
):
    installer.install_from_url(
        url=f"{http_fixture}/sample-addon-master.zip",
        addons_folder=fake_addons_folder,
        target_folder_name="SampleAddon",
    )
    assert (fake_addons_folder / "SampleAddon" / "SampleAddon.toc").exists()


def test_install_replaces_existing_folder(
    http_fixture: str, fake_addons_folder: pathlib.Path
):
    target = fake_addons_folder / "SampleAddon"
    target.mkdir()
    (target / "stale.lua").write_text("old")
    installer.install_from_url(
        url=f"{http_fixture}/sample-addon-master.zip",
        addons_folder=fake_addons_folder,
        target_folder_name="SampleAddon",
    )
    assert not (target / "stale.lua").exists()
    assert (target / "SampleAddon.toc").exists()


def test_install_404_raises_install_error(
    http_fixture: str, fake_addons_folder: pathlib.Path
):
    with pytest.raises(InstallError, match="404"):
        installer.install_from_url(
            url=f"{http_fixture}/missing.zip",
            addons_folder=fake_addons_folder,
            target_folder_name="SampleAddon",
        )
    assert not (fake_addons_folder / "SampleAddon").exists()


def test_install_rejects_zip_slip(
    tmp_path: pathlib.Path, fake_addons_folder: pathlib.Path
):
    """Zip-slip: a member path containing .. must be rejected."""
    import zipfile

    bad = tmp_path / "evil.zip"
    with zipfile.ZipFile(bad, "w") as zf:
        zf.writestr("evil-master/../escape.txt", "boom")
    with pytest.raises(InstallError, match="zip slip"):
        installer._extract_zip_atomic(
            zip_bytes=bad.read_bytes(),
            target_root=fake_addons_folder,
            folder_name="evil",
        )
