"""Visual card for a single catalog addon with state-aware styling."""

from __future__ import annotations

from collections.abc import Callable
from typing import Literal

import customtkinter as ctk

from ezwow.catalog.schema import Addon

AddonState = Literal["available", "installed", "outdated", "installing"]

_STATE_ACCENT: dict[AddonState, str] = {
    "available":  "#3b82f6",  # blue
    "installed":  "#16a34a",  # green
    "outdated":   "#d97706",  # amber
    "installing": "#6b7280",  # neutral
}

_STATE_LABEL: dict[AddonState, str] = {
    "available":  "Available",
    "installed":  "✓ Installed",
    "outdated":   "● Update",
    "installing": "Installing…",
}

_STATE_BUTTON: dict[AddonState, str] = {
    "available":  "Install",
    "installed":  "Reinstall",
    "outdated":   "Update",
    "installing": "Installing…",
}


class AddonCard(ctk.CTkFrame):  # type: ignore[misc]
    """Card with title, description, state pill, and action button."""

    def __init__(
        self,
        master: ctk.CTkBaseClass,
        *,
        addon: Addon,
        state: AddonState,
        on_action: Callable[[Addon], None],
    ) -> None:
        super().__init__(master, corner_radius=10, border_width=1)
        self.addon = addon
        self.on_action = on_action

        self.grid_columnconfigure(0, weight=1)

        title_row = ctk.CTkFrame(self, fg_color="transparent")
        title_row.grid(row=0, column=0, columnspan=2, sticky="ew", padx=14, pady=(10, 0))
        title_row.grid_columnconfigure(0, weight=1)

        title = ctk.CTkLabel(
            title_row,
            text=addon.name,
            font=ctk.CTkFont(size=14, weight="bold"),
            anchor="w",
        )
        title.grid(row=0, column=0, sticky="w")

        self.state_pill = ctk.CTkLabel(
            title_row,
            text=_STATE_LABEL[state],
            text_color="#ffffff",
            fg_color=_STATE_ACCENT[state],
            corner_radius=10,
            font=ctk.CTkFont(size=10, weight="bold"),
            padx=8,
            pady=2,
        )
        self.state_pill.grid(row=0, column=1, padx=(8, 0))

        author = ctk.CTkLabel(
            self,
            text=f"by {addon.author}  ·  {addon.github}",
            text_color="#9ca3af",
            font=ctk.CTkFont(size=10),
            anchor="w",
        )
        author.grid(row=1, column=0, columnspan=2, sticky="w", padx=14)

        desc = ctk.CTkLabel(
            self,
            text=addon.description,
            anchor="w",
            justify="left",
            wraplength=520,
        )
        desc.grid(row=2, column=0, columnspan=2, sticky="ew", padx=14, pady=(4, 8))

        self.action = ctk.CTkButton(
            self,
            text=_STATE_BUTTON[state],
            width=110,
            command=self._clicked,
            fg_color=_STATE_ACCENT[state],
            hover_color=_STATE_ACCENT[state],
        )
        self.action.grid(row=3, column=0, columnspan=2, sticky="e", padx=14, pady=(0, 12))

        self._state = state

    def _clicked(self) -> None:
        self.on_action(self.addon)

    def set_state(self, state: AddonState) -> None:
        """Update visual state — useful for in-place 'Installing…' feedback."""
        self._state = state
        self.state_pill.configure(text=_STATE_LABEL[state], fg_color=_STATE_ACCENT[state])
        self.action.configure(
            text=_STATE_BUTTON[state],
            fg_color=_STATE_ACCENT[state],
            hover_color=_STATE_ACCENT[state],
            state="normal" if state != "installing" else "disabled",
        )
