"""Catalog dataclasses and validation. Pure logic, no I/O."""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any, Literal

ID_RE = re.compile(r"^[a-z0-9][a-z0-9-]*$")
SUPPORTED_SCHEMA_VERSION = 2


class SchemaError(ValueError):
    """Raised when a catalog dict fails validation."""


@dataclass(frozen=True, slots=True)
class Category:
    id: str
    label: str


@dataclass(frozen=True, slots=True)
class Addon:
    id: str
    name: str
    category: str
    description: str
    author: str
    github: str
    branch: str = "master"
    use_releases: bool = False
    folder: str = ""
    depends: tuple[str, ...] = ()
    tags: tuple[str, ...] = ()
    homepage: str | None = None

    def branch_zip_url(self) -> str:
        return f"https://github.com/{self.github}/archive/refs/heads/{self.branch}.zip"


InstallTarget = Literal["data_root", "addons_folder"]


@dataclass(frozen=True, slots=True)
class ClientMod:
    id: str
    name: str
    description: str
    github: str
    asset_pattern: str
    install_to: InstallTarget
    files_to_install: tuple[str, ...]
    tags: tuple[str, ...] = ()
    branch: str = "main"
    homepage: str | None = None


@dataclass(frozen=True, slots=True)
class Preset:
    id: str
    label: str
    addons: tuple[str, ...] = ()
    client_mods: tuple[str, ...] = ()


@dataclass(frozen=True, slots=True)
class Catalog:
    schema_version: int
    updated: str
    categories: list[Category]
    addons: list[Addon]
    client_mods: list[ClientMod]
    presets: dict[str, Preset] = field(default_factory=dict)

    def addon_by_id(self, addon_id: str) -> Addon | None:
        return next((a for a in self.addons if a.id == addon_id), None)

    def client_mod_by_id(self, mod_id: str) -> ClientMod | None:
        return next((m for m in self.client_mods if m.id == mod_id), None)


def _check_id(kind: str, value: str) -> None:
    if not ID_RE.match(value):
        raise SchemaError(
            f"{kind} id {value!r} must be lowercase kebab-case (matched {ID_RE.pattern})"
        )


def parse_catalog(raw: dict[str, Any]) -> Catalog:
    if raw.get("schema_version") != SUPPORTED_SCHEMA_VERSION:
        raise SchemaError(
            f"Unsupported schema_version {raw.get('schema_version')!r}; "
            f"expected {SUPPORTED_SCHEMA_VERSION}"
        )

    categories = [Category(id=c["id"], label=c["label"]) for c in raw.get("categories", [])]
    cat_ids = {c.id for c in categories}

    addons: list[Addon] = []
    for entry in raw.get("addons", []):
        _check_id("addon", entry["id"])
        if entry["category"] not in cat_ids:
            raise SchemaError(
                f"addon {entry['id']!r} references unknown category {entry['category']!r}"
            )
        addons.append(
            Addon(
                id=entry["id"],
                name=entry["name"],
                category=entry["category"],
                description=entry["description"],
                author=entry["author"],
                github=entry["github"],
                branch=entry.get("branch", "master"),
                use_releases=bool(entry.get("use_releases", False)),
                folder=entry.get("folder", entry["id"]),
                depends=tuple(entry.get("depends", [])),
                tags=tuple(entry.get("tags", [])),
                homepage=entry.get("homepage"),
            )
        )
    addon_ids = {a.id for a in addons}

    for addon in addons:
        for dep in addon.depends:
            if dep not in addon_ids:
                raise SchemaError(
                    f"addon {addon.id!r} depends on unknown addon {dep!r}"
                )

    client_mods: list[ClientMod] = []
    for entry in raw.get("client_mods", []):
        _check_id("client_mod", entry["id"])
        install_to = entry["install_to"]
        if install_to not in ("data_root", "addons_folder"):
            raise SchemaError(f"client_mod {entry['id']!r} has invalid install_to {install_to!r}")
        client_mods.append(
            ClientMod(
                id=entry["id"],
                name=entry["name"],
                description=entry["description"],
                github=entry["github"],
                asset_pattern=entry["asset_pattern"],
                install_to=install_to,
                files_to_install=tuple(entry.get("files_to_install", [])),
                tags=tuple(entry.get("tags", [])),
                branch=entry.get("branch", "main"),
                homepage=entry.get("homepage"),
            )
        )
    mod_ids = {m.id for m in client_mods}

    presets: dict[str, Preset] = {}
    for preset_id, body in raw.get("presets", {}).items():
        _check_id("preset", preset_id)
        for ref in body.get("addons", []):
            if ref not in addon_ids:
                raise SchemaError(f"preset {preset_id!r} references unknown addon {ref!r}")
        for ref in body.get("client_mods", []):
            if ref not in mod_ids:
                raise SchemaError(f"preset {preset_id!r} references unknown client_mod {ref!r}")
        presets[preset_id] = Preset(
            id=preset_id,
            label=body["label"],
            addons=tuple(body.get("addons", [])),
            client_mods=tuple(body.get("client_mods", [])),
        )

    return Catalog(
        schema_version=raw["schema_version"],
        updated=raw["updated"],
        categories=categories,
        addons=addons,
        client_mods=client_mods,
        presets=presets,
    )
