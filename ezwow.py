"""
EZWowAddon – v1.0.0
Light‑weight addon manager for Turtle WoW (1.12 client)
Author:  Jamal Al-Sarraf

Python 3.11+ ‑ Requires: requests, tkinter (std‑lib)

Key features in this release
────────────────────────────
• New **“Settings”** tab that replaces the old *File → Select Folder* menu.
• **Recommended Addons** list expanded to 6 popular GitHub projects and
  auto‑detects whether each addon is already installed.
• Clear status labels showing **Installed / Not Installed** next to every addon and
  the install button text changes dynamically.
• Clean, modular design that keeps GUI logic separate from filesystem/network
  logic and makes future extensions (threaded downloads, update checks, etc.)
  trivial.
"""

from __future__ import annotations

import io
import json
import pathlib
import shutil
import zipfile
from functools import partial
from typing import Dict, List, Tuple

import requests
import tkinter as tk
from tkinter import filedialog, messagebox, ttk

######################################################################
# Static data – curated list of popular Turtle WoW / vanilla‑1.12 addons
######################################################################
# Each entry: (Display‑Name, GitHub‑ZIP‑URL, Folder‑Name‑When‑Installed)
RECOMMENDED_ADDONS: List[Tuple[str, str, str]] = [
    (
        "pfQuest",
        "https://github.com/shagu/pfQuest/archive/refs/heads/master.zip",
        "pfQuest",
    ),  # :contentReference[oaicite:0]{index=0}
    (
        "pfQuest‑Turtle",
        "https://github.com/shagu/pfQuest-turtle/archive/refs/heads/master.zip",
        "pfQuest-turtle",
    ),  # :contentReference[oaicite:1]{index=1}
    (
        "BigWigs",
        "https://github.com/CosminPOP/BigWigs/archive/refs/heads/master.zip",
        "BigWigs",
    ),  # :contentReference[oaicite:2]{index=2}
    (
        "LunaUnitFrames",
        "https://github.com/Aviana/LunaUnitFrames/archive/refs/heads/master.zip",
        "LunaUnitFrames",
    ),
    (
        "ShaguTweaks",
        "https://github.com/shagu/ShaguTweaks/archive/refs/heads/master.zip",
        "ShaguTweaks",
    ),
    (
        "AtlasLootClassic",
        "https://github.com/AtlasLoot/AtlasLootClassic/archive/refs/heads/master.zip",
        "AtlasLootClassic",
    ),
]

CONFIG_FILE = "ezwow_config.json"


######################################################################
# Helper functions – configuration, download, extraction
######################################################################
def load_config() -> str | None:
    try:
        with open(CONFIG_FILE, "r", encoding="utf‑8") as fp:
            return json.load(fp).get("addons_folder")
    except FileNotFoundError:
        return None


def save_config(path: str) -> None:
    try:
        with open(CONFIG_FILE, "w", encoding="utf‑8") as fp:
            json.dump({"addons_folder": path}, fp)
    except OSError as exc:
        print(f"[WARN] Could not save config: {exc}")


def find_default_addons_folder() -> pathlib.Path | None:
    """Try to auto‑locate Turtle WoW AddOns folder on Windows."""
    candidate = (
        pathlib.Path.home()
        / "Games"
        / "Turtle WoW"
        / "_classic_"
        / "Interface"
        / "AddOns"
    )
    return candidate if candidate.exists() else None


def download_and_extract(
    url: str, target_folder: pathlib.Path, subfolder_name: str
) -> None:
    """
    Download a GitHub ZIP and extract *subfolder_name* to target_folder.

    Raises RuntimeError on failure so the GUI can display a message.
    """
    try:
        resp = requests.get(url, timeout=45)
        resp.raise_for_status()
    except Exception as exc:
        raise RuntimeError(f"Download failed: {exc}") from exc

    try:
        with zipfile.ZipFile(io.BytesIO(resp.content)) as zf:
            top_level = zf.namelist()[0].split("/")[0]  # repo‑master folder
            for member in zf.namelist():
                inner = member.split("/", 1)[1] if "/" in member else ""
                if not inner:
                    continue  # skip directory placeholders
                dest_path = target_folder / inner
                if member.endswith("/"):
                    dest_path.mkdir(parents=True, exist_ok=True)
                else:
                    dest_path.parent.mkdir(parents=True, exist_ok=True)
                    with zf.open(member) as src, open(dest_path, "wb") as dst:
                        shutil.copyfileobj(src, dst)
    except Exception as exc:
        raise RuntimeError(f"Extraction failed: {exc}") from exc

    # Ensure final folder has expected name (rename if needed)
    extracted_root = target_folder / top_level
    expected_root = target_folder / subfolder_name
    if extracted_root.exists() and extracted_root != expected_root:
        if expected_root.exists():
            shutil.rmtree(expected_root)
        extracted_root.rename(expected_root)


######################################################################
# Main Application class
######################################################################
class AddonManagerApp(tk.Tk):
    def __init__(self) -> None:
        super().__init__()
        self.title("EZWowAddon – Turtle WoW Addon Manager")
        self.geometry("600x430")
        self.resizable(False, False)

        # ── state ────────────────────────────────────────────────────
        self.addons_folder: pathlib.Path | None = None
        self.status_var = tk.StringVar()

        # ── try to bootstrap path from config or default ─────────────
        cfg_path = load_config()
        if cfg_path and pathlib.Path(cfg_path).is_dir():
            self.addons_folder = pathlib.Path(cfg_path)
        else:
            self.addons_folder = find_default_addons_folder()

        # ── build UI ─────────────────────────────────────────────────
        self._build_notebook()

        # final status update
        self._update_status("Ready.")

    # ══════════════════════════════════════════════════════════════
    # UI Construction
    # ══════════════════════════════════════════════════════════════
    def _build_notebook(self) -> None:
        notebook = ttk.Notebook(self)
        notebook.pack(fill="both", expand=True, padx=8, pady=8)

        # Tab – Settings / Folder
        tab_settings = ttk.Frame(notebook)
        notebook.add(tab_settings, text="Settings")
        self._build_settings_tab(tab_settings)

        # Tab – Recommended Addons
        tab_recommended = ttk.Frame(notebook)
        notebook.add(tab_recommended, text="Recommended Addons")
        self._build_recommended_tab(tab_recommended)

        # Tab – Install from URL
        tab_custom = ttk.Frame(notebook)
        notebook.add(tab_custom, text="Install from URL")
        self._build_custom_tab(tab_custom)

        # Tab – Manage Installed
        tab_manage = ttk.Frame(notebook)
        notebook.add(tab_manage, text="Manage Installed")
        self._build_manage_tab(tab_manage)

    # ───────────────────────── Settings Tab ───────────────────────
    def _build_settings_tab(self, parent: ttk.Frame) -> None:
        ttk.Label(parent, text="Turtle WoW AddOns folder:", font=("Segoe UI", 10)).pack(
            pady=(12, 4)
        )

        self.folder_var = tk.StringVar(
            value=str(self.addons_folder) if self.addons_folder else ""
        )
        entry = ttk.Entry(parent, textvariable=self.folder_var, width=70)
        entry.pack(padx=16)

        browse_btn = ttk.Button(parent, text="Browse …", command=self._select_folder)
        browse_btn.pack(pady=10)

        if not self.addons_folder:
            ttk.Label(
                parent,
                text="(Select your AddOns folder to enable install buttons.)",
                foreground="red",
            ).pack()

    def _select_folder(self) -> None:
        new_path = filedialog.askdirectory(
            title="Select Turtle WoW › Interface › AddOns folder"
        )
        if new_path:
            self.addons_folder = pathlib.Path(new_path)
            self.folder_var.set(new_path)
            save_config(new_path)
            self._update_status("AddOns folder set.")
            self._refresh_recommended_status()
            self._refresh_installed_list()

    # ─────────────────── Recommended Addons Tab ───────────────────
    def _build_recommended_tab(self, parent: ttk.Frame) -> None:
        ttk.Label(
            parent,
            text="Popular AddOns (GitHub)",
            font=("Segoe UI", 10, "bold"),
        ).pack(pady=5)

        self.reco_rows: Dict[str, Dict[str, tk.Variable]] = {}
        container = ttk.Frame(parent)
        container.pack(padx=10, fill="x")

        for name, url, folder in RECOMMENDED_ADDONS:
            row = ttk.Frame(container)
            row.pack(fill="x", pady=2)

            status_var = tk.StringVar()
            btn_var = tk.StringVar()

            ttk.Label(row, text=name, width=24, anchor="w").pack(side="left")
            ttk.Label(row, textvariable=status_var, width=14).pack(side="left")

            ttk.Button(
                row,
                textvariable=btn_var,
                command=partial(self._install_recommended, name, url, folder),
                width=14,
            ).pack(side="right")

            self.reco_rows[name] = {"status": status_var, "btn": btn_var}

        self._refresh_recommended_status()

    def _refresh_recommended_status(self) -> None:
        """Update Installed/Not Installed labels and button captions."""
        for name, _, folder in RECOMMENDED_ADDONS:
            row = self.reco_rows[name]
            if self.addons_folder and (self.addons_folder / folder).exists():
                row["status"].set("Installed")
                row["btn"].set("Reinstall")
            else:
                row["status"].set("Not Installed")
                row["btn"].set("Install")

    def _install_recommended(self, name: str, url: str, folder: str) -> None:
        if not self._ensure_folder():  # verify path
            return
        try:
            self._update_status(f"Installing {name} …")
            download_and_extract(url, self.addons_folder, folder)
            messagebox.showinfo("Success", f"{name} installed successfully.")
        except RuntimeError as exc:
            messagebox.showerror("Error", str(exc))
        finally:
            self._refresh_recommended_status()
            self._refresh_installed_list()
            self._update_status("Ready.")

    # ───────────────────── Install‑from‑URL Tab ───────────────────
    def _build_custom_tab(self, parent: ttk.Frame) -> None:
        desc = (
            "Paste a GitHub repository URL below "
            "and click **Install** to download the latest `master` ZIP."
        )
        ttk.Label(parent, text=desc, wraplength=500).pack(pady=6)

        self.url_var = tk.StringVar()
        ttk.Entry(parent, textvariable=self.url_var, width=70).pack(padx=16)
        ttk.Button(parent, text="Install", command=self._install_from_url).pack(pady=8)

    def _install_from_url(self) -> None:
        if not self._ensure_folder():
            return
        url = self.url_var.get().strip().rstrip("/")
        if not url:
            messagebox.showwarning("No URL", "Please enter a GitHub repository URL.")
            return
        if not url.endswith(".zip"):
            url += "/archive/refs/heads/master.zip"
        name = url.split("/")[-3]  # repo name segment
        try:
            self._update_status(f"Installing {name} …")
            download_and_extract(url, self.addons_folder, name)
            messagebox.showinfo("Success", f"{name} installed successfully.")
        except RuntimeError as exc:
            messagebox.showerror("Error", str(exc))
        finally:
            self._refresh_recommended_status()
            self._refresh_installed_list()
            self._update_status("Ready.")

    # ─────────────────── Manage Installed Tab ─────────────────────
    def _build_manage_tab(self, parent: ttk.Frame) -> None:
        ttk.Label(parent, text="Installed AddOns:", font=("Segoe UI", 10)).pack(pady=5)

        self.listbox = tk.Listbox(parent, height=14)
        self.listbox.pack(fill="both", expand=True, padx=10)

        btn_frame = ttk.Frame(parent)
        btn_frame.pack(pady=6)
        ttk.Button(btn_frame, text="Refresh", command=self._refresh_installed_list).pack(
            side="left", padx=4
        )
        ttk.Button(btn_frame, text="Remove Selected", command=self._remove_selected).pack(
            side="left", padx=4
        )

        self._refresh_installed_list()

    def _refresh_installed_list(self) -> None:
        self.listbox.delete(0, tk.END)
        if not self.addons_folder:
            return
        for folder in sorted(self.addons_folder.iterdir()):
            if folder.is_dir():
                self.listbox.insert(tk.END, folder.name)

    def _remove_selected(self) -> None:
        if not self._ensure_folder():
            return
        sel = self.listbox.curselection()
        if not sel:
            return
        name = self.listbox.get(sel[0])
        if messagebox.askyesno("Confirm Delete", f"Delete addon '{name}'?"):
            try:
                shutil.rmtree(self.addons_folder / name)
                self._refresh_installed_list()
                self._refresh_recommended_status()
            except OSError as exc:
                messagebox.showerror("Error", f"Could not delete: {exc}")

    # ────────────────────────── Helpers ───────────────────────────
    def _ensure_folder(self) -> bool:
        if not self.addons_folder:
            messagebox.showwarning("AddOns Folder Needed", "Set your AddOns folder first.")
            return False
        return True

    def _update_status(self, msg: str) -> None:
        self.status_var.set(msg)
        print(msg)  # For debugging; could be a status‑bar widget.

    # end class


######################################################################
# Launch application
######################################################################
if __name__ == "__main__":
    app = AddonManagerApp()
    ttk.Label(app, textvariable=app.status_var).pack(side="bottom", pady=4)
    app.mainloop()
