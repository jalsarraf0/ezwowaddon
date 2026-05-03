"""Download → extract → place addons atomically."""

from __future__ import annotations

import io
import logging
import pathlib
import shutil
import tempfile
import zipfile
from dataclasses import dataclass

import requests

DOWNLOAD_TIMEOUT = 60
log = logging.getLogger(__name__)


class InstallError(RuntimeError):
    """Raised when install fails (download, extract, or place)."""


@dataclass(slots=True)
class InstallResult:
    folder: str
    files: tuple[str, ...]
    size_bytes: int


def install_from_url(
    *, url: str, addons_folder: pathlib.Path, target_folder_name: str
) -> InstallResult:
    log.info("downloading %s", url)
    try:
        resp = requests.get(url, timeout=DOWNLOAD_TIMEOUT)
    except requests.RequestException as exc:
        raise InstallError(f"download failed: {exc}") from exc
    if resp.status_code != 200:
        raise InstallError(f"download failed: HTTP {resp.status_code} from {url}")
    return _extract_zip_atomic(
        zip_bytes=resp.content,
        target_root=addons_folder,
        folder_name=target_folder_name,
    )


def _extract_zip_atomic(
    *, zip_bytes: bytes, target_root: pathlib.Path, folder_name: str
) -> InstallResult:
    target_root = target_root.resolve()
    final_dir = target_root / folder_name

    try:
        zf = zipfile.ZipFile(io.BytesIO(zip_bytes))
    except zipfile.BadZipFile as exc:
        raise InstallError(f"corrupt zip: {exc}") from exc

    members = [m for m in zf.namelist() if not m.endswith("/")]
    if not members:
        raise InstallError("zip contains no files")

    top_level = members[0].split("/", 1)[0]

    for m in zf.namelist():
        if ".." in m.split("/") or m.startswith("/"):
            raise InstallError(f"zip slip detected: {m!r}")

    with tempfile.TemporaryDirectory(dir=target_root) as staging:
        staging_path = pathlib.Path(staging)
        zf.extractall(staging_path)
        extracted_root = staging_path / top_level
        if not extracted_root.is_dir():
            raise InstallError(f"expected top-level dir {top_level!r} not in zip")

        if final_dir.exists():
            shutil.rmtree(final_dir)
        shutil.move(str(extracted_root), str(final_dir))

    files: list[str] = []
    size = 0
    for path in final_dir.rglob("*"):
        if path.is_file():
            rel = str(path.relative_to(target_root))
            files.append(rel)
            size += path.stat().st_size

    return InstallResult(folder=folder_name, files=tuple(sorted(files)), size_bytes=size)
