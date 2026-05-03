"""Profiles tab."""

from __future__ import annotations

import pathlib
import threading
from tkinter import filedialog
from typing import TYPE_CHECKING

import customtkinter as ctk

from ezwow.catalog.schema import Catalog
from ezwow.core import deps, manifest, profile
from ezwow.ui.widgets import notification

if TYPE_CHECKING:
    from ezwow.ui.app import App


class ProfilesTab(ctk.CTkFrame):  # type: ignore[misc]
    def __init__(self, *, master: ctk.CTk, catalog: Catalog, app: App) -> None:
        super().__init__(master)
        self.app = app
        self.catalog = catalog
        self._build()

    def _build(self) -> None:
        ctk.CTkLabel(
            self, text="Profiles", font=ctk.CTkFont(size=18, weight="bold")
        ).pack(anchor="w", padx=12, pady=(12, 4))

        for preset_id, preset in self.catalog.presets.items():
            row = ctk.CTkFrame(self)
            row.pack(fill="x", padx=12, pady=4)
            ctk.CTkLabel(
                row,
                text=f"{preset.label} — {len(preset.addons)} addons",
                anchor="w",
            ).pack(side="left", padx=6)
            ctk.CTkButton(
                row,
                text="Apply",
                width=90,
                command=lambda pid=preset_id: self._apply_preset(pid),
            ).pack(side="right", padx=6)

        ctk.CTkLabel(self, text="Custom profile:").pack(
            anchor="w", padx=12, pady=(12, 0)
        )
        bar = ctk.CTkFrame(self, fg_color="transparent")
        bar.pack(fill="x", padx=12)
        ctk.CTkButton(bar, text="Import…", command=self._import).pack(side="left", padx=4)
        ctk.CTkButton(bar, text="Export…", command=self._export).pack(side="left", padx=4)

    def _apply_preset(self, preset_id: str) -> None:
        threading.Thread(target=self._do_apply, args=(preset_id,), daemon=True).start()

    def _do_apply(self, preset_id: str) -> None:
        from ezwow.ui.tabs.browse import BrowseTab

        resolved = profile.resolve_preset(preset_id, self.catalog)
        try:
            ordered = deps.resolve(resolved.addon_ids, self.catalog)
        except (deps.CycleError, KeyError) as exc:
            self.app.after(0, lambda e=exc: notification.error("Preset error", str(e)))
            return
        browse_tab = self.app.tabs.get("Browse")
        if isinstance(browse_tab, BrowseTab):
            browse_tab.do_install(ordered)

    def _import(self) -> None:
        path = filedialog.askopenfilename(filetypes=[("JSON", "*.json")])
        if not path:
            return
        p = profile.import_profile(pathlib.Path(path))
        threading.Thread(target=self._do_apply_ids, args=(p.addons,), daemon=True).start()

    def _do_apply_ids(self, ids: list[str]) -> None:
        from ezwow.ui.tabs.browse import BrowseTab

        try:
            ordered = deps.resolve(ids, self.catalog)
        except (deps.CycleError, KeyError) as exc:
            self.app.after(0, lambda e=exc: notification.error("Profile error", str(e)))
            return
        browse_tab = self.app.tabs.get("Browse")
        if isinstance(browse_tab, BrowseTab):
            browse_tab.do_install(ordered)

    def _export(self) -> None:
        if not self.app.addons_folder:
            return
        path = filedialog.asksaveasfilename(defaultextension=".json")
        if not path:
            return
        m = manifest.load(self.app.addons_folder)
        profile.export_profile(
            out_path=pathlib.Path(path),
            addon_ids=sorted(m.installs.keys()),
            client_mod_ids=[],
            label="user-export",
        )
        notification.info("Exported", path)
