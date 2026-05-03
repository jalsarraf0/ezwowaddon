"""Per-AddOns-folder install manifest stored as `.ezwow-manifest.json`."""

from __future__ import annotations

import datetime as dt
import json
import logging
import pathlib
from dataclasses import dataclass, field

MANIFEST_FILENAME = ".ezwow-manifest.json"
SCHEMA_VERSION = 1
log = logging.getLogger(__name__)


@dataclass(frozen=True, slots=True)
class InstallEntry:
    addon_id: str
    folder: str
    source: str
    ref: str
    sha: str | None
    installed_at: dt.datetime
    files: tuple[str, ...]
    size_bytes: int


@dataclass
class Manifest:
    schema_version: int = SCHEMA_VERSION
    installs: dict[str, InstallEntry] = field(default_factory=dict)


def _path(addons_folder: pathlib.Path) -> pathlib.Path:
    return addons_folder / MANIFEST_FILENAME


def load(addons_folder: pathlib.Path) -> Manifest:
    path = _path(addons_folder)
    if not path.exists():
        return Manifest()
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        log.warning("manifest at %s corrupt, resetting: %s", path, exc)
        return Manifest()
    installs = {
        k: InstallEntry(
            addon_id=v["addon_id"],
            folder=v["folder"],
            source=v["source"],
            ref=v["ref"],
            sha=v.get("sha"),
            installed_at=dt.datetime.fromisoformat(v["installed_at"]),
            files=tuple(v["files"]),
            size_bytes=int(v["size_bytes"]),
        )
        for k, v in raw.get("installs", {}).items()
    }
    return Manifest(schema_version=raw.get("schema_version", SCHEMA_VERSION), installs=installs)


def save(addons_folder: pathlib.Path, manifest: Manifest) -> None:
    payload = {
        "schema_version": manifest.schema_version,
        "installs": {
            k: {
                "addon_id": v.addon_id,
                "folder": v.folder,
                "source": v.source,
                "ref": v.ref,
                "sha": v.sha,
                "installed_at": v.installed_at.isoformat(),
                "files": list(v.files),
                "size_bytes": v.size_bytes,
            }
            for k, v in manifest.installs.items()
        },
    }
    _path(addons_folder).write_text(json.dumps(payload, indent=2), encoding="utf-8")


def record(addons_folder: pathlib.Path, entry: InstallEntry) -> None:
    m = load(addons_folder)
    m.installs[entry.addon_id] = entry
    save(addons_folder, m)


def remove(addons_folder: pathlib.Path, addon_id: str) -> None:
    m = load(addons_folder)
    m.installs.pop(addon_id, None)
    save(addons_folder, m)
