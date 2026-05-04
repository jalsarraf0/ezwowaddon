"""High-level install pipeline. Composes installer + github + manifest into a single call.

This is the canonical install operation. CLI, GUI, and any future entry point
should call into this module rather than re-implementing the dance.
"""

from __future__ import annotations

import datetime as dt
import logging
import pathlib

from ezwow.catalog.schema import Addon
from ezwow.core import installer, manifest
from ezwow.core.github import GitHubClient

log = logging.getLogger(__name__)


def install_addon(
    *,
    addon: Addon,
    addons_folder: pathlib.Path,
    gh_client: GitHubClient,
) -> manifest.InstallEntry:
    """Download an addon, extract atomically, record in manifest.

    Returns the manifest entry that was persisted. Raises installer.InstallError
    on download or extract failure (caller decides whether to surface or recover).
    """
    log.info("installing %s from %s", addon.id, addon.branch_zip_url())
    result = installer.install_from_url(
        url=addon.branch_zip_url(),
        addons_folder=addons_folder,
        target_folder_name=addon.folder,
    )
    sha = gh_client.branch_head_sha(addon.github, addon.branch)
    entry = _entry_for(addon, result, sha)
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
    log.info("updating %s to %s", addon.id, (target_sha or "unknown")[:7])
    result = installer.install_from_url(
        url=addon.branch_zip_url(),
        addons_folder=addons_folder,
        target_folder_name=addon.folder,
    )
    if target_sha is None:
        target_sha = gh_client.branch_head_sha(addon.github, addon.branch)
    entry = _entry_for(addon, result, target_sha)
    manifest.record(addons_folder, entry)
    return entry


def _entry_for(
    addon: Addon, result: installer.InstallResult, sha: str | None
) -> manifest.InstallEntry:
    return manifest.InstallEntry(
        addon_id=addon.id,
        folder=addon.folder,
        source=f"github:{addon.github}",
        ref=addon.branch,
        sha=sha,
        installed_at=dt.datetime.now(dt.UTC),
        files=result.files,
        size_bytes=result.size_bytes,
    )
