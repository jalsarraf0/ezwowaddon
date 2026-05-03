"""Client mods tab — installs to Data/ folder (manual for v2.0)."""

from __future__ import annotations

from typing import TYPE_CHECKING

import customtkinter as ctk

from ezwow.catalog.schema import Catalog
from ezwow.core import detector
from ezwow.ui.widgets import notification

if TYPE_CHECKING:
    from ezwow.ui.app import App


class ClientModsTab(ctk.CTkFrame):  # type: ignore[misc]
    def __init__(self, *, master: ctk.CTk, catalog: Catalog, app: App) -> None:
        super().__init__(master)
        self.app = app
        self.catalog = catalog
        self._build()

    def _build(self) -> None:
        ctk.CTkLabel(
            self, text="Client Mods", font=ctk.CTkFont(size=18, weight="bold")
        ).pack(anchor="w", padx=12, pady=(12, 4))
        ctk.CTkLabel(
            self,
            text="Mods that go in Data/ (DLLs, MPQ patches). Requires Data folder.",
            anchor="w",
            wraplength=700,
        ).pack(anchor="w", padx=12)

        scroll = ctk.CTkScrollableFrame(self)
        scroll.pack(fill="both", expand=True, padx=12, pady=8)

        for mod in self.catalog.client_mods:
            row = ctk.CTkFrame(scroll)
            row.pack(fill="x", pady=2)
            ctk.CTkLabel(
                row, text=f"{mod.name} — {mod.description}", anchor="w"
            ).pack(side="left", padx=6)
            ctk.CTkButton(
                row,
                text="Install",
                width=90,
                command=lambda m=mod: self._install(m.name),
            ).pack(side="right", padx=6)

    def _install(self, name: str) -> None:
        data = detector.find_data_folder(addons=self.app.addons_folder)
        if data is None:
            notification.error(
                "Data folder missing",
                "Cannot find Data/ next to your AddOns folder.",
            )
            return
        notification.info(
            "Manual step",
            f"Client mod install will place files into {data}. "
            f"Auto-install for {name} ships in v2.1; for now, see homepage.",
        )
