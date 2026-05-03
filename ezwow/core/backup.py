"""tar.gz backup and restore of AddOns + SavedVariables."""

from __future__ import annotations

import datetime as dt
import logging
import pathlib
import tarfile

log = logging.getLogger(__name__)


class BackupError(RuntimeError):
    """Raised on backup or restore failure."""


def _timestamp() -> str:
    return dt.datetime.now(dt.UTC).strftime("%Y%m%dT%H%M%SZ")


def create_backup(*, wow_root: pathlib.Path, out_dir: pathlib.Path) -> pathlib.Path:
    addons = wow_root / "Interface" / "AddOns"
    wtf = wow_root / "WTF"
    if not addons.is_dir():
        raise BackupError(f"AddOns folder missing at {addons}")

    out_dir.mkdir(parents=True, exist_ok=True)
    archive = out_dir / f"ezwow-backup-{_timestamp()}.tar.gz"
    with tarfile.open(archive, "w:gz") as tar:
        tar.add(addons, arcname="Interface/AddOns")
        if wtf.is_dir():
            tar.add(wtf, arcname="WTF")
    log.info("backup written to %s", archive)
    return archive


def restore_backup(*, archive: pathlib.Path, wow_root: pathlib.Path) -> None:
    if not archive.exists():
        raise BackupError(f"archive not found at {archive}")
    with tarfile.open(archive, "r:gz") as tar:
        for member in tar.getmembers():
            if ".." in member.name.split("/") or member.name.startswith("/"):
                raise BackupError(f"unsafe path in archive: {member.name!r}")
        tar.extractall(wow_root, filter="data")
    log.info("restored from %s", archive)
