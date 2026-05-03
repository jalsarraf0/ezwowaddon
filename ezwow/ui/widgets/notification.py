"""Modal notification helper."""

from __future__ import annotations

from tkinter import messagebox


def info(title: str, msg: str) -> None:
    messagebox.showinfo(title, msg)


def error(title: str, msg: str) -> None:
    messagebox.showerror(title, msg)


def confirm(title: str, msg: str) -> bool:
    return bool(messagebox.askyesno(title, msg))
