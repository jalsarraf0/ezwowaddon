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


def test_install_rejects_corrupt_zip(fake_addons_folder: pathlib.Path):
    with pytest.raises(InstallError, match="corrupt zip"):
        installer._extract_zip_atomic(
            zip_bytes=b"definitely not a zip file",
            target_root=fake_addons_folder,
            folder_name="x",
        )


def test_install_rejects_empty_zip(
    tmp_path: pathlib.Path, fake_addons_folder: pathlib.Path
):
    import zipfile

    empty = tmp_path / "empty.zip"
    with zipfile.ZipFile(empty, "w"):
        pass
    with pytest.raises(InstallError, match="contains no files"):
        installer._extract_zip_atomic(
            zip_bytes=empty.read_bytes(),
            target_root=fake_addons_folder,
            folder_name="x",
        )


def test_install_rejects_missing_top_level_dir(
    tmp_path: pathlib.Path, fake_addons_folder: pathlib.Path
):
    """Top-level dir is taken from the first file's path; if it doesn't exist as a dir, fail."""
    import zipfile

    weird = tmp_path / "weird.zip"
    with zipfile.ZipFile(weird, "w") as zf:
        # First member references a top_level dir but no actual files inside it
        zf.writestr("ghost-dir/loose.txt", "x")
        # Then add a file at root level (no top_level dir match)
        zf.writestr("root.txt", "y")
    # Manually craft so first non-dir member's split yields a top_level dir
    # that won't exist after extract — actually the zip above WILL extract
    # ghost-dir as a real dir. Use a truly path-less first member.
    weird2 = tmp_path / "weird2.zip"
    with zipfile.ZipFile(weird2, "w") as zf:
        zf.writestr("loneifle.txt", "z")  # split('/', 1)[0] == "loneifle.txt"
    with pytest.raises(InstallError, match="expected top-level dir"):
        installer._extract_zip_atomic(
            zip_bytes=weird2.read_bytes(),
            target_root=fake_addons_folder,
            folder_name="x",
        )


def test_install_from_url_raises_on_request_exception(
    fake_addons_folder: pathlib.Path, monkeypatch: pytest.MonkeyPatch
):
    import requests

    def boom(*_a: object, **_kw: object) -> object:
        raise requests.ConnectionError("offline")

    monkeypatch.setattr(installer.requests, "get", boom)
    with pytest.raises(InstallError, match="download failed"):
        installer.install_from_url(
            url="http://nope.invalid/x.zip",
            addons_folder=fake_addons_folder,
            target_folder_name="X",
        )
