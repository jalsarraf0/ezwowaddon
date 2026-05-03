"""User config locations and persistence."""

from __future__ import annotations

import json
import os
import pathlib
from dataclasses import asdict, dataclass, field

LEGACY_CONFIG_FILENAME = "ezwow_config.json"


def config_dir() -> pathlib.Path:
    """Return the per-user config directory, creating it if needed."""
    if os.name == "nt":
        base = pathlib.Path(os.environ.get("APPDATA", pathlib.Path.home() / "AppData" / "Roaming"))
    else:
        base = pathlib.Path(
            os.environ.get("XDG_CONFIG_HOME", pathlib.Path.home() / ".config")
        )
    target = base / "ezwowaddon"
    target.mkdir(parents=True, exist_ok=True)
    return target


def cache_dir() -> pathlib.Path:
    """Return the per-user cache directory, creating it if needed."""
    if os.name == "nt":
        base = pathlib.Path(os.environ.get("LOCALAPPDATA", pathlib.Path.home() / "AppData" / "Local"))
    else:
        base = pathlib.Path(
            os.environ.get("XDG_CACHE_HOME", pathlib.Path.home() / ".cache")
        )
    target = base / "ezwowaddon"
    target.mkdir(parents=True, exist_ok=True)
    return target


def data_dir() -> pathlib.Path:
    """Return the per-user data directory (used for backups)."""
    if os.name == "nt":
        base = pathlib.Path(os.environ.get("APPDATA", pathlib.Path.home() / "AppData" / "Roaming"))
    else:
        base = pathlib.Path(
            os.environ.get("XDG_DATA_HOME", pathlib.Path.home() / ".local" / "share")
        )
    target = base / "ezwowaddon"
    target.mkdir(parents=True, exist_ok=True)
    return target


@dataclass
class UserConfig:
    addons_folder: str | None = None
    data_folder: str | None = None
    github_pat: str | None = None
    remote_catalog_enabled: bool = True
    theme: str = "dark"
    backup_dir: str | None = None
    auto_backup_before_batch: bool = True
    extras: dict[str, str] = field(default_factory=dict)


def config_path() -> pathlib.Path:
    return config_dir() / "config.json"


def load() -> UserConfig:
    path = config_path()
    if path.exists():
        raw = json.loads(path.read_text(encoding="utf-8"))
        return UserConfig(**{k: raw.get(k) for k in UserConfig.__dataclass_fields__})
    legacy = pathlib.Path.cwd() / LEGACY_CONFIG_FILENAME
    if legacy.exists():
        raw = json.loads(legacy.read_text(encoding="utf-8"))
        cfg = UserConfig(addons_folder=raw.get("addons_folder"))
        save(cfg)
        return cfg
    return UserConfig()


def save(cfg: UserConfig) -> None:
    path = config_path()
    path.write_text(json.dumps(asdict(cfg), indent=2), encoding="utf-8")
