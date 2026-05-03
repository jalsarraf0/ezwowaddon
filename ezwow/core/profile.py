"""Apply presets and export/import custom profiles."""

from __future__ import annotations

import json
import pathlib
from dataclasses import dataclass

from ezwow.catalog.schema import Catalog


@dataclass(frozen=True, slots=True)
class ResolvedPreset:
    addon_ids: list[str]
    client_mod_ids: list[str]


@dataclass(frozen=True, slots=True)
class Profile:
    label: str
    addons: list[str]
    client_mods: list[str]


def resolve_preset(preset_id: str, catalog: Catalog) -> ResolvedPreset:
    preset = catalog.presets.get(preset_id)
    if preset is None:
        raise KeyError(f"unknown preset {preset_id!r}")
    return ResolvedPreset(
        addon_ids=list(preset.addons),
        client_mod_ids=list(preset.client_mods),
    )


def export_profile(
    *,
    out_path: pathlib.Path,
    addon_ids: list[str],
    client_mod_ids: list[str],
    label: str,
) -> None:
    out_path.write_text(
        json.dumps(
            {"label": label, "addons": addon_ids, "client_mods": client_mod_ids},
            indent=2,
        ),
        encoding="utf-8",
    )


def import_profile(path: pathlib.Path) -> Profile:
    raw = json.loads(path.read_text(encoding="utf-8"))
    return Profile(
        label=raw.get("label", "(unnamed)"),
        addons=list(raw.get("addons", [])),
        client_mods=list(raw.get("client_mods", [])),
    )
