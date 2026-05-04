"""Main CustomTkinter window. Behaviour-thin: delegates to core.*"""

from __future__ import annotations

import logging
from collections.abc import Callable
from typing import TYPE_CHECKING

import customtkinter as ctk

from ezwow import __version__, config
from ezwow.catalog import loader as catalog_loader
from ezwow.core import detector
from ezwow.ui.widgets.toast import ToastManager

if TYPE_CHECKING:
    from ezwow.catalog.schema import Catalog


log = logging.getLogger(__name__)

_NAV_LABELS = ("Browse", "Installed", "Updates", "Client Mods", "Profiles", "Settings")


class App(ctk.CTk):  # type: ignore[misc]
    def __init__(self) -> None:
        super().__init__()
        self.title(f"EZWowAddon {__version__}")
        self.geometry("1080x720")
        self.minsize(900, 600)

        self.cfg = config.load()
        ctk.set_appearance_mode(self.cfg.theme)
        ctk.set_default_color_theme("blue")

        self.catalog: Catalog = catalog_loader.load_bundled()
        self.addons_folder = detector.find_addons_folder(saved=self.cfg.addons_folder)

        self.tabs: dict[str, ctk.CTkFrame] = {}
        self.nav_buttons: dict[str, ctk.CTkButton] = {}
        self.toasts = ToastManager(self)

        self._build_layout()

    def _build_layout(self) -> None:
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        nav = ctk.CTkFrame(self, width=200, corner_radius=0)
        nav.grid(row=0, column=0, sticky="nsw")
        nav.grid_propagate(False)

        ctk.CTkLabel(
            nav,
            text="EZWowAddon",
            font=ctk.CTkFont(size=18, weight="bold"),
        ).pack(padx=14, pady=(18, 4), anchor="w")
        ctk.CTkLabel(
            nav,
            text=f"v{__version__}",
            text_color="#9ca3af",
            font=ctk.CTkFont(size=10),
        ).pack(padx=14, pady=(0, 16), anchor="w")

        self.content = ctk.CTkFrame(self, corner_radius=0, fg_color="transparent")
        self.content.grid(row=0, column=1, sticky="nsew")
        self.content.grid_columnconfigure(0, weight=1)
        self.content.grid_rowconfigure(0, weight=1)

        factories = {
            "Browse": self._make_browse,
            "Installed": self._make_installed,
            "Updates": self._make_updates,
            "Client Mods": self._make_client_mods,
            "Profiles": self._make_profiles,
            "Settings": self._make_settings,
        }
        for label in _NAV_LABELS:
            self._add_nav_button(nav, label, factories[label])

        self.status = ctk.CTkLabel(
            self,
            text="Ready.",
            anchor="w",
            text_color="#9ca3af",
            font=ctk.CTkFont(size=11),
        )
        self.status.grid(row=1, column=0, columnspan=2, sticky="ew", padx=12, pady=6)

        self._show_tab("Browse")

    def _add_nav_button(
        self,
        parent: ctk.CTkFrame,
        label: str,
        factory: Callable[[], ctk.CTkFrame],
    ) -> None:
        btn = ctk.CTkButton(
            parent,
            text=label,
            anchor="w",
            height=36,
            corner_radius=6,
            fg_color="transparent",
            text_color=("#1f2937", "#e5e7eb"),
            hover_color=("#e5e7eb", "#374151"),
            command=lambda: self._show_tab(label),
        )
        btn.pack(fill="x", padx=10, pady=2)
        self.nav_buttons[label] = btn
        self.tabs[label] = factory()

    def _show_tab(self, label: str) -> None:
        for child in self.content.winfo_children():
            child.grid_forget()
        for k, btn in self.nav_buttons.items():
            btn.configure(
                fg_color="#2563eb" if k == label else "transparent",
                text_color=("#ffffff", "#ffffff") if k == label else ("#1f2937", "#e5e7eb"),
            )
        frame = self.tabs[label]
        frame.grid(in_=self.content, row=0, column=0, sticky="nsew")

    def _make_browse(self) -> ctk.CTkFrame:
        from ezwow.ui.tabs.browse import BrowseTab

        return BrowseTab(master=self, catalog=self.catalog, app=self)

    def _make_installed(self) -> ctk.CTkFrame:
        from ezwow.ui.tabs.installed import InstalledTab

        return InstalledTab(master=self, app=self)

    def _make_updates(self) -> ctk.CTkFrame:
        from ezwow.ui.tabs.updates import UpdatesTab

        return UpdatesTab(master=self, app=self)

    def _make_client_mods(self) -> ctk.CTkFrame:
        from ezwow.ui.tabs.client_mods import ClientModsTab

        return ClientModsTab(master=self, catalog=self.catalog, app=self)

    def _make_profiles(self) -> ctk.CTkFrame:
        from ezwow.ui.tabs.profiles import ProfilesTab

        return ProfilesTab(master=self, catalog=self.catalog, app=self)

    def _make_settings(self) -> ctk.CTkFrame:
        from ezwow.ui.tabs.settings import SettingsTab

        return SettingsTab(master=self, app=self)

    def set_status(self, msg: str) -> None:
        self.status.configure(text=msg)
        self.update_idletasks()

    def toast(self, msg: str, *, level: str = "info") -> None:
        """Show a non-blocking toast. level ∈ info|success|warning|error."""
        self.toasts.show(msg, level=level)  # type: ignore[arg-type]


def launch() -> None:
    app = App()
    app.mainloop()
