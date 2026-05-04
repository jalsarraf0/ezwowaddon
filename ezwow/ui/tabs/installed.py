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
        super().__init__(master, fg_color="transparent")
        self.app = app
        self._build()

    def _build(self) -> None:
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.pack(fill="x", padx=18, pady=(18, 6))
        ctk.CTkLabel(
            header, text="Installed", font=ctk.CTkFont(size=22, weight="bold")
        ).pack(side="left")
        ctk.CTkButton(
            header, text="↻ Refresh", width=90, command=self._refresh
        ).pack(side="right")

        self.list = ctk.CTkScrollableFrame(self, fg_color="transparent")
        self.list.pack(fill="both", expand=True, padx=12, pady=8)
        self._refresh()

    def _refresh(self) -> None:
        for child in self.list.winfo_children():
            child.destroy()
        if not self.app.addons_folder:
            ctk.CTkLabel(
                self.list,
                text="AddOns folder not set — configure it in Settings.",
                text_color="#9ca3af",
            ).pack(pady=20)
            return
        m = manifest.load(self.app.addons_folder)
        if not m.installs:
            ctk.CTkLabel(
                self.list,
                text="No addons installed yet. Browse to install some.",
                text_color="#9ca3af",
            ).pack(pady=20)
            return
        for inst in sorted(m.installs.values(), key=lambda i: i.addon_id):
            row = ctk.CTkFrame(self.list, corner_radius=8)
            row.pack(fill="x", padx=8, pady=3)
            sha_display = (inst.sha or "?")[:7]
            ctk.CTkLabel(
                row,
                text=inst.addon_id,
                anchor="w",
                font=ctk.CTkFont(size=13, weight="bold"),
            ).pack(side="left", padx=12, pady=8)
            ctk.CTkLabel(
                row,
                text=f"{inst.ref} · {sha_display}",
                anchor="w",
                text_color="#9ca3af",
                font=ctk.CTkFont(size=10),
            ).pack(side="left", padx=4)
            ctk.CTkButton(
                row,
                text="Remove",
                width=90,
                fg_color="#dc2626",
                hover_color="#b91c1c",
                command=lambda i=inst: self._remove(i.addon_id, i.folder),
            ).pack(side="right", padx=12, pady=8)

    def _remove(self, addon_id: str, folder_name: str) -> None:
        if self.app.addons_folder is None:
            return
        if not notification.confirm("Confirm removal", f"Remove {addon_id}?"):
            return
        target = self.app.addons_folder / folder_name
        if target.is_dir():
            shutil.rmtree(target)
        manifest.remove(self.app.addons_folder, addon_id)
        self.app.toast(f"Removed {addon_id}.", level="success")
        self._refresh()
