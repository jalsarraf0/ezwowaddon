"""Settings tab."""

from __future__ import annotations

from tkinter import filedialog
from typing import TYPE_CHECKING

import customtkinter as ctk

from ezwow import config
from ezwow.core import detector

if TYPE_CHECKING:
    from ezwow.ui.app import App


class SettingsTab(ctk.CTkFrame):  # type: ignore[misc]
    def __init__(self, *, master: ctk.CTk, app: App) -> None:
        super().__init__(master)
        self.app = app
        self.cfg = config.load()
        self._build()

    def _build(self) -> None:
        ctk.CTkLabel(
            self, text="Settings", font=ctk.CTkFont(size=18, weight="bold")
        ).pack(anchor="w", padx=12, pady=(12, 4))

        self.folder_var = ctk.StringVar(value=self.cfg.addons_folder or "")
        ctk.CTkLabel(self, text="AddOns folder:").pack(
            anchor="w", padx=12, pady=(8, 0)
        )
        row = ctk.CTkFrame(self, fg_color="transparent")
        row.pack(fill="x", padx=12)
        ctk.CTkEntry(row, textvariable=self.folder_var, width=540).pack(
            side="left", padx=4
        )
        ctk.CTkButton(row, text="Browse…", command=self._pick).pack(side="left", padx=4)

        self.pat_var = ctk.StringVar(value=self.cfg.github_pat or "")
        ctk.CTkLabel(
            self, text="GitHub PAT (optional, raises rate limit):"
        ).pack(anchor="w", padx=12, pady=(8, 0))
        ctk.CTkEntry(self, textvariable=self.pat_var, show="*", width=540).pack(
            anchor="w", padx=12
        )

        self.theme_var = ctk.StringVar(value=self.cfg.theme)
        ctk.CTkLabel(self, text="Theme:").pack(anchor="w", padx=12, pady=(8, 0))
        ctk.CTkOptionMenu(
            self, values=["dark", "light", "system"], variable=self.theme_var
        ).pack(anchor="w", padx=12)

        ctk.CTkButton(self, text="Save", command=self._save).pack(
            anchor="w", padx=12, pady=12
        )

    def _pick(self) -> None:
        path = filedialog.askdirectory(title="Pick Interface/AddOns")
        if path:
            self.folder_var.set(path)

    def _save(self) -> None:
        self.cfg.addons_folder = self.folder_var.get() or None
        self.cfg.github_pat = self.pat_var.get() or None
        self.cfg.theme = self.theme_var.get()
        config.save(self.cfg)
        ctk.set_appearance_mode(self.cfg.theme)
        self.app.cfg = self.cfg
        self.app.addons_folder = detector.find_addons_folder(saved=self.cfg.addons_folder)
