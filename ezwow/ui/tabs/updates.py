"""Updates tab."""

from __future__ import annotations

import datetime as dt
import threading
from typing import TYPE_CHECKING

import customtkinter as ctk

from ezwow import config
from ezwow.core import github, installer, manifest, updater
from ezwow.ui.widgets import notification

if TYPE_CHECKING:
    from ezwow.ui.app import App


class UpdatesTab(ctk.CTkFrame):  # type: ignore[misc]
    def __init__(self, *, master: ctk.CTk, app: App) -> None:
        super().__init__(master)
        self.app = app
        self._build()

    def _build(self) -> None:
        ctk.CTkLabel(
            self, text="Updates", font=ctk.CTkFont(size=18, weight="bold")
        ).pack(anchor="w", padx=12, pady=(12, 4))
        ctk.CTkButton(self, text="Check Now", command=self._refresh).pack(
            anchor="w", padx=12
        )
        ctk.CTkButton(self, text="Update All", command=self._update_all).pack(
            anchor="w", padx=12, pady=4
        )
        self.list = ctk.CTkScrollableFrame(self)
        self.list.pack(fill="both", expand=True, padx=12, pady=8)
        self._refresh()

    def _refresh(self) -> None:
        for child in self.list.winfo_children():
            child.destroy()
        if not self.app.addons_folder:
            ctk.CTkLabel(self.list, text="(AddOns folder not set)").pack()
            return
        cfg = config.load()
        gh = github.GitHubClient(cache_dir=config.cache_dir(), token=cfg.github_pat)
        plan = updater.plan(
            addons_folder=self.app.addons_folder, catalog=self.app.catalog, gh_client=gh
        )
        if not plan.updates:
            ctk.CTkLabel(self.list, text="All addons up to date.").pack()
            return
        for u in plan.updates:
            row = ctk.CTkFrame(self.list)
            row.pack(fill="x", pady=2)
            cur = (u.current or "?")[:7]
            lat = (u.latest or "?")[:7]
            ctk.CTkLabel(
                row, text=f"{u.addon_id}: {cur} → {lat}", anchor="w"
            ).pack(side="left", padx=6)

    def _update_all(self) -> None:
        threading.Thread(target=self._do_update_all, daemon=True).start()

    def _do_update_all(self) -> None:
        if not self.app.addons_folder:
            return
        cfg = config.load()
        gh = github.GitHubClient(cache_dir=config.cache_dir(), token=cfg.github_pat)
        plan = updater.plan(
            addons_folder=self.app.addons_folder, catalog=self.app.catalog, gh_client=gh
        )
        for u in plan.updates:
            addon = self.app.catalog.addon_by_id(u.addon_id)
            if addon is None:
                continue
            self.app.set_status(f"updating {addon.id}…")
            try:
                result = installer.install_from_url(
                    url=addon.branch_zip_url(),
                    addons_folder=self.app.addons_folder,
                    target_folder_name=addon.folder,
                )
            except installer.InstallError as exc:
                self.app.after(0, lambda e=exc: notification.error("Update failed", str(e)))
                return
            manifest.record(
                self.app.addons_folder,
                manifest.InstallEntry(
                    addon_id=addon.id,
                    folder=addon.folder,
                    source=f"github:{addon.github}",
                    ref=addon.branch,
                    sha=u.latest,
                    installed_at=dt.datetime.now(dt.UTC),
                    files=result.files,
                    size_bytes=result.size_bytes,
                ),
            )
        self.app.after(0, lambda: self.app.set_status("Ready."))
        self.app.after(0, self._refresh)
