"""High-level install pipeline. Composes installer + github + manifest into a single call.

This is the canonical install operation. CLI, GUI, and any future entry point
should call into this module rather than re-implementing the dance.
"""

from __future__ import annotations

import datetime as dt
import logging
import pathlib

from ezwow.catalog.schema import DEFAULT_FALLBACK_BRANCH, Addon
from ezwow.core import installer, manifest
from ezwow.core.github import GitHubClient

log = logging.getLogger(__name__)


def resolve_branch(addon: Addon, gh_client: GitHubClient) -> str:
    """Resolve which branch to install from.

    Priority: explicit catalog branch → live GitHub default branch → 'master' fallback.
    Catalog entries that omit `branch:` get auto-detected, so when an upstream author
    switches master↔main, the catalog doesn't need a PR — installs just keep working.
    """
    if addon.branch:
        return addon.branch
    detected = gh_client.default_branch(addon.github)
    return detected or DEFAULT_FALLBACK_BRANCH


def install_addon(
    *,
    addon: Addon,
    addons_folder: pathlib.Path,
    gh_client: GitHubClient,
) -> manifest.InstallEntry:
    """Download an addon, extract atomically, record in manifest.

    Resolves the branch via `resolve_branch()` so the catalog never breaks when
    upstream switches default branches. Returns the manifest entry persisted.
    Raises installer.InstallError on download or extract failure.
    """
    branch = resolve_branch(addon, gh_client)
    log.info("installing %s from %s (branch=%s)", addon.id, addon.github, branch)
    result = installer.install_from_url(
        url=addon.branch_zip_url(branch),
        addons_folder=addons_folder,
        target_folder_name=addon.folder,
    )
    sha = gh_client.branch_head_sha(addon.github, branch)
    entry = _entry_for(addon, result, branch, sha)
    manifest.record(addons_folder, entry)
    return entry


def update_addon_to_sha(
    *,
    addon: Addon,
    addons_folder: pathlib.Path,
    gh_client: GitHubClient,
    target_sha: str | None,
) -> manifest.InstallEntry:
    """Reinstall an addon and stamp the manifest with target_sha.

    Same as install_addon but uses an already-known target SHA (e.g. from an
    UpdatePlan) instead of re-querying GitHub. Saves one API call per update.
    """
    branch = resolve_branch(addon, gh_client)
    log.info("updating %s to %s (branch=%s)", addon.id, (target_sha or "?")[:7], branch)
    result = installer.install_from_url(
        url=addon.branch_zip_url(branch),
        addons_folder=addons_folder,
        target_folder_name=addon.folder,
    )
    if target_sha is None:
        target_sha = gh_client.branch_head_sha(addon.github, branch)
    entry = _entry_for(addon, result, branch, target_sha)
    manifest.record(addons_folder, entry)
    return entry


def _entry_for(
    addon: Addon, result: installer.InstallResult, branch: str, sha: str | None
) -> manifest.InstallEntry:
    return manifest.InstallEntry(
        addon_id=addon.id,
        folder=addon.folder,
        source=f"github:{addon.github}",
        ref=branch,
        sha=sha,
        installed_at=dt.datetime.now(dt.UTC),
        files=result.files,
        size_bytes=result.size_bytes,
    )
