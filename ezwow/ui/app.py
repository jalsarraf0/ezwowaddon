"""Main CustomTkinter window. Behaviour-thin: delegates to core.*"""

from __future__ import annotations

import logging
from collections.abc import Callable
from typing import TYPE_CHECKING

import customtkinter as ctk

from ezwow import __version__, config
from ezwow.catalog import loader as catalog_loader
from ezwow.core import detector

if TYPE_CHECKING:
    from ezwow.catalog.schema import Catalog


log = logging.getLogger(__name__)


class App(ctk.CTk):  # type: ignore[misc]
    def __init__(self) -> None:
        super().__init__()
        self.title(f"EZWowAddon {__version__}")
        self.geometry("960x640")
        self.minsize(800, 540)

        self.cfg = config.load()
        ctk.set_appearance_mode(self.cfg.theme)
        ctk.set_default_color_theme("blue")

        self.catalog: Catalog = catalog_loader.load_bundled()
        self.addons_folder = detector.find_addons_folder(saved=self.cfg.addons_folder)

        self.tabs: dict[str, ctk.CTkFrame] = {}
        self._build_layout()

    def _build_layout(self) -> None:
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        nav = ctk.CTkFrame(self, width=180, corner_radius=0)
        nav.grid(row=0, column=0, sticky="nsw")
        nav.grid_propagate(False)

        self.content = ctk.CTkFrame(self, corner_radius=0)
        self.content.grid(row=0, column=1, sticky="nsew")
        self.content.grid_columnconfigure(0, weight=1)
        self.content.grid_rowconfigure(0, weight=1)

        self._add_tab(nav, "Browse", self._make_browse)
        self._add_tab(nav, "Installed", self._make_installed)
        self._add_tab(nav, "Updates", self._make_updates)
        self._add_tab(nav, "Client Mods", self._make_client_mods)
        self._add_tab(nav, "Profiles", self._make_profiles)
        self._add_tab(nav, "Settings", self._make_settings)

        self.status = ctk.CTkLabel(self, text="Ready.", anchor="w")
        self.status.grid(row=1, column=0, columnspan=2, sticky="ew", padx=8, pady=4)

        self._show_tab("Browse")

    def _add_tab(
        self,
        parent: ctk.CTkFrame,
        label: str,
        factory: Callable[[], ctk.CTkFrame],
    ) -> None:
        btn = ctk.CTkButton(
            parent,
            text=label,
            anchor="w",
            command=lambda: self._show_tab(label),
        )
        btn.pack(fill="x", padx=8, pady=4)
        self.tabs[label] = factory()

    def _show_tab(self, label: str) -> None:
        for child in self.content.winfo_children():
            child.grid_forget()
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


def launch() -> None:
    app = App()
    app.mainloop()
