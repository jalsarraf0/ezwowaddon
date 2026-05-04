"""Compare installed addon SHAs against upstream."""

from __future__ import annotations

import pathlib
from dataclasses import dataclass

from ezwow.catalog.schema import Catalog
from ezwow.core import manifest, pipeline
from ezwow.core.github import GitHubClient


@dataclass(frozen=True, slots=True)
class PendingUpdate:
    addon_id: str
    current: str | None
    latest: str | None


@dataclass(frozen=True, slots=True)
class UpdatePlan:
    updates: list[PendingUpdate]


def plan(
    *,
    addons_folder: pathlib.Path,
    catalog: Catalog,
    gh_client: GitHubClient,
) -> UpdatePlan:
    m = manifest.load(addons_folder)
    pending: list[PendingUpdate] = []
    for addon_id, entry in m.installs.items():
        addon = catalog.addon_by_id(addon_id)
        if not addon:
            continue
        if addon.use_releases:
            latest = gh_client.latest_release_tag(addon.github)
        else:
            branch = pipeline.resolve_branch(addon, gh_client)
            latest = gh_client.branch_head_sha(addon.github, branch)
        if latest is None:
            continue
        if entry.sha != latest:
            pending.append(
                PendingUpdate(addon_id=addon_id, current=entry.sha, latest=latest)
            )
    return UpdatePlan(updates=pending)
