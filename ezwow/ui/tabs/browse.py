"""Browse tab: categorized addon catalog with search."""

from __future__ import annotations

import datetime as dt
import threading
from typing import TYPE_CHECKING

import customtkinter as ctk

from ezwow import config
from ezwow.catalog.schema import Addon, Catalog
from ezwow.core import deps, github, installer, manifest
from ezwow.ui.widgets import notification

if TYPE_CHECKING:
    from ezwow.ui.app import App


class BrowseTab(ctk.CTkFrame):  # type: ignore[misc]
    def __init__(self, *, master: ctk.CTk, catalog: Catalog, app: App) -> None:
        super().__init__(master)
        self.app = app
        self.catalog = catalog
        self.search_var = ctk.StringVar()
        self.search_var.trace_add("write", lambda *_: self._refresh())
        self._build()

    def _build(self) -> None:
        ctk.CTkLabel(
            self, text="Browse Addons", font=ctk.CTkFont(size=18, weight="bold")
        ).pack(anchor="w", padx=12, pady=(12, 4))
        bar = ctk.CTkFrame(self, fg_color="transparent")
        bar.pack(fill="x", padx=12, pady=4)
        ctk.CTkEntry(
            bar, textvariable=self.search_var, placeholder_text="search…", width=300
        ).pack(side="left")

        self.scroll = ctk.CTkScrollableFrame(self)
        self.scroll.pack(fill="both", expand=True, padx=12, pady=8)
        self._refresh()

    def _refresh(self) -> None:
        for child in self.scroll.winfo_children():
            child.destroy()
        query = self.search_var.get().lower().strip()
        by_cat: dict[str, list[Addon]] = {}
        for a in self.catalog.addons:
            if query and query not in a.name.lower() and query not in a.description.lower():
                continue
            by_cat.setdefault(a.category, []).append(a)

        cat_label = {c.id: c.label for c in self.catalog.categories}
        for cat_id in sorted(by_cat):
            ctk.CTkLabel(
                self.scroll,
                text=cat_label.get(cat_id, cat_id),
                font=ctk.CTkFont(weight="bold"),
            ).pack(anchor="w", pady=(8, 2))
            for addon in sorted(by_cat[cat_id], key=lambda a: a.name):
                self._render_addon_row(addon)

    def _render_addon_row(self, addon: Addon) -> None:
        row = ctk.CTkFrame(self.scroll)
        row.pack(fill="x", pady=2)
        text = f"{addon.name} — {addon.description}"
        ctk.CTkLabel(row, text=text, anchor="w").pack(side="left", padx=6)
        ctk.CTkButton(
            row, text="Install", width=90, command=lambda a=addon: self._install(a)
        ).pack(side="right", padx=6)

    def _install(self, addon: Addon) -> None:
        if self.app.addons_folder is None:
            notification.error(
                "AddOns folder not set",
                "Configure your AddOns folder in Settings first.",
            )
            return
        ordered = deps.resolve([addon.id], self.catalog)
        threading.Thread(target=self.do_install, args=(ordered,), daemon=True).start()

    def do_install(self, addon_ids: list[str]) -> None:
        if self.app.addons_folder is None:
            return
        cfg = config.load()
        gh = github.GitHubClient(cache_dir=config.cache_dir(), token=cfg.github_pat)
        for aid in addon_ids:
            addon = self.catalog.addon_by_id(aid)
            if addon is None:
                continue
            self.app.set_status(f"installing {aid}…")
            try:
                result = installer.install_from_url(
                    url=addon.branch_zip_url(),
                    addons_folder=self.app.addons_folder,
                    target_folder_name=addon.folder,
                )
            except installer.InstallError as exc:
                self.app.after(0, lambda e=exc: notification.error("Install failed", str(e)))
                return
            sha = gh.branch_head_sha(addon.github, addon.branch)
            manifest.record(
                self.app.addons_folder,
                manifest.InstallEntry(
                    addon_id=aid,
                    folder=addon.folder,
                    source=f"github:{addon.github}",
                    ref=addon.branch,
                    sha=sha,
                    installed_at=dt.datetime.now(dt.UTC),
                    files=result.files,
                    size_bytes=result.size_bytes,
                ),
            )
        self.app.after(0, lambda: self.app.set_status("Ready."))
        self.app.after(0, lambda: notification.info("Installed", ", ".join(addon_ids)))
