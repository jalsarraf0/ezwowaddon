"""Non-modal slide-in toast notifications.

Replaces blocking messagebox popups. Toasts queue at the bottom-right of the
parent window, auto-dismiss after a short delay, and don't steal focus.
"""

from __future__ import annotations

import contextlib
from typing import Literal

import customtkinter as ctk

ToastLevel = Literal["info", "success", "warning", "error"]

_LEVEL_COLORS: dict[ToastLevel, tuple[str, str]] = {
    # (background, text)
    "info":    ("#2563eb", "#ffffff"),
    "success": ("#16a34a", "#ffffff"),
    "warning": ("#d97706", "#ffffff"),
    "error":   ("#dc2626", "#ffffff"),
}

_DEFAULT_TTL_MS = 4000


class Toast(ctk.CTkFrame):  # type: ignore[misc]
    """A single toast frame. Stack via ToastManager."""

    def __init__(
        self,
        master: ctk.CTkBaseClass,
        *,
        text: str,
        level: ToastLevel = "info",
    ) -> None:
        bg, fg = _LEVEL_COLORS[level]
        super().__init__(master, fg_color=bg, corner_radius=8, border_width=0)
        ctk.CTkLabel(
            self,
            text=text,
            text_color=fg,
            font=ctk.CTkFont(size=13, weight="bold"),
            anchor="w",
            justify="left",
            wraplength=420,
        ).pack(padx=14, pady=10, anchor="w", fill="x")


class ToastManager:
    """Stacks toasts at the bottom-right of a host window. One per app."""

    def __init__(self, host: ctk.CTk) -> None:
        self.host = host
        self._stack: list[Toast] = []

    def show(
        self, text: str, *, level: ToastLevel = "info", ttl_ms: int = _DEFAULT_TTL_MS
    ) -> None:
        toast = Toast(self.host, text=text, level=level)
        self._stack.append(toast)
        self._reflow()
        self.host.after(ttl_ms, lambda t=toast: self._dismiss(t))

    def _dismiss(self, toast: Toast) -> None:
        if toast in self._stack:
            self._stack.remove(toast)
        with contextlib.suppress(Exception):
            toast.destroy()
        self._reflow()

    def _reflow(self) -> None:
        margin_x = 16
        margin_y_bottom = 56  # leave space for status bar
        gap = 8
        try:
            self.host.update_idletasks()
            host_w = self.host.winfo_width()
            host_h = self.host.winfo_height()
        except Exception:  # Tk teardown raises various; ignore
            return

        y = host_h - margin_y_bottom
        for toast in reversed(self._stack):
            toast.update_idletasks()
            tw = toast.winfo_reqwidth()
            th = toast.winfo_reqheight()
            x = host_w - tw - margin_x
            y -= th + gap
            toast.place(x=x, y=y)
