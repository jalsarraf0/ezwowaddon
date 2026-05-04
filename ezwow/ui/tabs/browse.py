"""Browse tab: categorized addon catalog with search + state-aware cards."""

from __future__ import annotations

import threading
from typing import TYPE_CHECKING

import customtkinter as ctk

from ezwow import config
from ezwow.catalog.schema import Addon, Catalog
from ezwow.core import deps, github, installer, manifest, pipeline
from ezwow.ui.widgets.addon_card import AddonCard, AddonState

if TYPE_CHECKING:
    from ezwow.ui.app import App


_CATEGORY_ICONS: dict[str, str] = {
    "ui":         "🖼️",
    "quest":      "📜",
    "combat":     "⚔️",
    "auction":    "💰",
    "inventory":  "🎒",
    "raid":       "🐉",
    "social":     "💬",
    "utility":    "🔧",
    "client-mod": "⚙️",
}


class BrowseTab(ctk.CTkFrame):  # type: ignore[misc]
    def __init__(self, *, master: ctk.CTk, catalog: Catalog, app: App) -> None:
        super().__init__(master, fg_color="transparent")
        self.app = app
        self.catalog = catalog
        self.search_var = ctk.StringVar()
        self.search_var.trace_add("write", lambda *_: self._refresh())
        self._cards: dict[str, AddonCard] = {}
        self._build()

    def _build(self) -> None:
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.pack(fill="x", padx=18, pady=(18, 6))
        ctk.CTkLabel(
            header,
            text="Browse",
            font=ctk.CTkFont(size=22, weight="bold"),
        ).pack(side="left")
        ctk.CTkLabel(
            header,
            text=f"{len(self.catalog.addons)} addons",
            text_color="#9ca3af",
            font=ctk.CTkFont(size=12),
        ).pack(side="left", padx=(10, 0), pady=(8, 0))

        bar = ctk.CTkFrame(self, fg_color="transparent")
        bar.pack(fill="x", padx=18, pady=(0, 8))
        ctk.CTkEntry(
            bar,
            textvariable=self.search_var,
            placeholder_text="Search addons by name, description, or tag…",
            height=36,
        ).pack(fill="x", expand=True)

        self.scroll = ctk.CTkScrollableFrame(self, fg_color="transparent")
        self.scroll.pack(fill="both", expand=True, padx=12, pady=(0, 8))
        self._refresh()

    def _state_for(self, addon: Addon) -> AddonState:
        if self.app.addons_folder is None:
            return "available"
        m = manifest.load(self.app.addons_folder)
        if addon.id in m.installs:
            return "installed"
        return "available"

    def _refresh(self) -> None:
        for child in self.scroll.winfo_children():
            child.destroy()
        self._cards.clear()

        query = self.search_var.get().lower().strip()
        by_cat: dict[str, list[Addon]] = {}
        for a in self.catalog.addons:
            if query and not (
                query in a.name.lower()
                or query in a.description.lower()
                or any(query in t for t in a.tags)
            ):
                continue
            by_cat.setdefault(a.category, []).append(a)

        cat_label = {c.id: c.label for c in self.catalog.categories}
        for cat_id in sorted(by_cat):
            section = ctk.CTkLabel(
                self.scroll,
                text=f"{_CATEGORY_ICONS.get(cat_id, '•')}  {cat_label.get(cat_id, cat_id)}",
                font=ctk.CTkFont(size=15, weight="bold"),
                anchor="w",
            )
            section.pack(anchor="w", padx=8, pady=(14, 4), fill="x")
            for addon in sorted(by_cat[cat_id], key=lambda a: a.name):
                card = AddonCard(
                    self.scroll,
                    addon=addon,
                    state=self._state_for(addon),
                    on_action=self._install,
                )
                card.pack(fill="x", padx=8, pady=4)
                self._cards[addon.id] = card

    def _install(self, addon: Addon) -> None:
        if self.app.addons_folder is None:
            self.app.toast("Set your AddOns folder in Settings first.", level="warning")
            return
        ordered = deps.resolve([addon.id], self.catalog)
        for aid in ordered:
            if aid in self._cards:
                self._cards[aid].set_state("installing")
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
                pipeline.install_addon(
                    addon=addon, addons_folder=self.app.addons_folder, gh_client=gh
                )
            except installer.InstallError as exc:
                self.app.after(0, lambda e=exc: self.app.toast(f"Install failed: {e}", level="error"))
                return
        self.app.after(0, lambda: self.app.set_status("Ready."))
        self.app.after(0, lambda: self.app.toast(f"Installed {len(addon_ids)} addon(s).", level="success"))
        self.app.after(0, self._refresh)
