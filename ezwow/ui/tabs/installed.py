"""Installed addons tab."""

from __future__ import annotations

import shutil
from typing import TYPE_CHECKING

import customtkinter as ctk

from ezwow.core import manifest
from ezwow.ui.widgets import notification

if TYPE_CHECKING:
    from ezwow.ui.app import App


class InstalledTab(ctk.CTkFrame):  # type: ignore[misc]
    def __init__(self, *, master: ctk.CTk, app: App) -> None:
        super().__init__(master)
        self.app = app
        self._build()

    def _build(self) -> None:
        ctk.CTkLabel(
            self, text="Installed", font=ctk.CTkFont(size=18, weight="bold")
        ).pack(anchor="w", padx=12, pady=(12, 4))
        ctk.CTkButton(self, text="Refresh", command=self._refresh).pack(
            anchor="w", padx=12
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
        m = manifest.load(self.app.addons_folder)
        if not m.installs:
            ctk.CTkLabel(self.list, text="(no installs tracked)").pack()
            return
        for inst in sorted(m.installs.values(), key=lambda i: i.addon_id):
            row = ctk.CTkFrame(self.list)
            row.pack(fill="x", pady=2)
            sha_display = (inst.sha or "?")[:7]
            ctk.CTkLabel(
                row,
                text=f"{inst.addon_id}   sha={sha_display}",
                anchor="w",
            ).pack(side="left", padx=6)
            ctk.CTkButton(
                row,
                text="Remove",
                width=90,
                command=lambda i=inst: self._remove(i.addon_id, i.folder),
            ).pack(side="right", padx=6)

    def _remove(self, addon_id: str, folder_name: str) -> None:
        if self.app.addons_folder is None:
            return
        if not notification.confirm("Confirm", f"Remove {addon_id}?"):
            return
        target = self.app.addons_folder / folder_name
        if target.is_dir():
            shutil.rmtree(target)
        manifest.remove(self.app.addons_folder, addon_id)
        self._refresh()
