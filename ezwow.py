import os
import pathlib
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import requests  # assuming requests is used for simplicity
import zipfile
import io
import json

# Data structure for recommended addons (Name -> GitHub ZIP URL)
RECOMMENDED_ADDONS = {
    "pfQuest": "https://github.com/shagu/pfQuest/archive/refs/heads/master.zip",
    "pfQuest-Turtle": "https://github.com/shagu/pfQuest-turtle/archive/refs/heads/master.zip",
    # ... more addons can be added here easily
}

CONFIG_FILE = "ezwow_config.json"  # to remember selected AddOns folder

def find_turtlewow_addons_folder():
    """Attempt to auto-detect Turtle WoW AddOns folder on Windows."""
    # Typical path: C:/Games/Turtle WoW/_classic_/Interface/AddOns
    default = pathlib.Path.home() / "Games" / "Turtle WoW" / "_classic_" / "Interface" / "AddOns"
    return default if default.exists() else None

def load_config():
    """Load stored configuration (e.g., last selected AddOns folder) from file."""
    try:
        with open(CONFIG_FILE, 'r') as f:
            cfg = json.load(f)
            return cfg.get("addons_folder")
    except FileNotFoundError:
        return None

def save_config(addons_folder):
    """Save the AddOns folder path to config file."""
    try:
        with open(CONFIG_FILE, 'w') as f:
            json.dump({"addons_folder": str(addons_folder)}, f)
    except Exception as e:
        print(f"Warning: Could not save config: {e}")

def download_and_install(addon_name, url, install_path):
    """
    Download the addon zip from GitHub and install it into the AddOns folder.
    Returns True on success, False on failure.
    """
    try:
        # Download the zip file
        resp = requests.get(url)
        resp.raise_for_status()
    except Exception as e:
        messagebox.showerror("Download Error", f"Failed to download {addon_name}: {e}")
        return False

    # Extract zip content in-memory and write to install_path
    try:
        with zipfile.ZipFile(io.BytesIO(resp.content)) as zf:
            # Typically GitHub zip has a top-level folder like 'addon-master/'
            # We extract its contents into the AddOns folder
            for member in zf.namelist():
                filename = member.split('/', 1)[-1]  # remove the top-level folder name
                if filename:  # not an empty string (which would be a directory)
                    target_path = pathlib.Path(install_path) / filename
                    if member.endswith('/'):
                        # Directory - create it
                        target_path.mkdir(parents=True, exist_ok=True)
                    else:
                        # File - extract
                        with zf.open(member) as source, open(target_path, 'wb') as target:
                            target.write(source.read())
        return True
    except Exception as e:
        messagebox.showerror("Install Error", f"Failed to install {addon_name}: {e}")
        return False

class AddonManagerApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("EZWowAddon - Turtle WoW Addon Manager")
        self.geometry("500x400")
        self.resizable(False, False)
        
        # State
        self.addons_folder = None
        # Try loading last used AddOns folder or auto-detect
        self.addons_folder = load_config() or find_turtlewow_addons_folder()
        
        # Build UI
        self._create_widgets()
        # If we have a detected AddOns folder, show it
        if self.addons_folder:
            self.folder_path_var.set(self.addons_folder)
        else:
            messagebox.showinfo("Welcome", 
                "Please select your Turtle WoW AddOns folder to get started.")
        
    def _create_widgets(self):
        """Initialize and layout all GUI components."""
        notebook = ttk.Notebook(self)
        notebook.pack(fill='both', expand=True, padx=10, pady=10)
        
        # Tab 1: Install Recommended Addons
        tab_recommend = ttk.Frame(notebook)
        notebook.add(tab_recommend, text="Recommended Addons")
        self._create_recommended_tab(tab_recommend)
        
        # Tab 2: Install from URL (custom addon)
        tab_custom = ttk.Frame(notebook)
        notebook.add(tab_custom, text="Install from URL")
        self._create_custom_tab(tab_custom)
        
        # Tab 3: Manage Installed (optional enhancement)
        tab_manage = ttk.Frame(notebook)
        notebook.add(tab_manage, text="Manage Installed")
        self._create_manage_tab(tab_manage)
        
    def _create_recommended_tab(self, parent):
        """Create the UI for the Recommended Addons tab."""
        info_label = ttk.Label(parent, text="Select an addon to install:")
        info_label.pack(pady=5)
        for name, url in RECOMMENDED_ADDONS.items():
            btn = ttk.Button(parent, text=f"Install {name}", 
                              command=lambda n=name, u=url: self.install_addon(n, u))
            btn.pack(fill='x', pady=2, padx=20)
    
    def _create_custom_tab(self, parent):
        """Create the UI for installing an addon from a custom GitHub URL."""
        desc = ("Paste a GitHub repository URL below (e.g. https://github.com/author/RepoName) "
                "and click Install to download the addon.")
        lbl = ttk.Label(parent, text=desc, wraplength=400)
        lbl.pack(pady=5)
        self.url_var = tk.StringVar()
        url_entry = ttk.Entry(parent, textvariable=self.url_var)
        url_entry.pack(fill='x', padx=10)
        install_btn = ttk.Button(parent, text="Install from URL", command=self.install_from_url)
        install_btn.pack(pady=5)
    
    def _create_manage_tab(self, parent):
        """Create the UI for managing installed addons (list and remove)."""
        lbl = ttk.Label(parent, text="Installed Addons:")
        lbl.pack(pady=5)
        # For simplicity, list folders in the AddOns directory
        listbox = tk.Listbox(parent)
        listbox.pack(fill='both', expand=True, padx=10, pady=5)
        refresh_btn = ttk.Button(parent, text="Refresh List", command=lambda: self._refresh_installed(listbox))
        refresh_btn.pack(pady=2)
        remove_btn = ttk.Button(parent, text="Uninstall Selected", command=lambda: self._uninstall_selected(listbox))
        remove_btn.pack(pady=2)
        # Populate initial list
        self._refresh_installed(listbox)
    
    def _refresh_installed(self, listbox):
        """Refresh the list of installed addons in the listbox."""
        listbox.delete(0, tk.END)
        if not self.addons_folder or not os.path.isdir(self.addons_folder):
            return
        for item in os.listdir(self.addons_folder):
            # Each addon is typically a folder with a .toc file inside; list all folders
            addon_path = pathlib.Path(self.addons_folder) / item
            if addon_path.is_dir():
                listbox.insert(tk.END, item)
    
    def _uninstall_selected(self, listbox):
        """Delete the selected addon folder from the AddOns directory."""
        selection = listbox.curselection()
        if not selection:
            return
        addon_name = listbox.get(selection[0])
        confirm = messagebox.askyesno("Confirm Removal", f"Remove addon '{addon_name}'?")
        if confirm:
            addon_path = pathlib.Path(self.addons_folder) / addon_name
            try:
                # remove the folder recursively
                import shutil
                shutil.rmtree(addon_path)
                self._refresh_installed(listbox)
            except Exception as e:
                messagebox.showerror("Error", f"Could not remove {addon_name}: {e}")
    
    def select_folder(self):
        """Prompt user to select the Turtle WoW AddOns folder."""
        folder = filedialog.askdirectory(title="Select Turtle WoW AddOns Folder")
        if folder:
            self.addons_folder = folder
            self.folder_path_var.set(folder)
            save_config(folder)
    
    def install_addon(self, name, url):
        """Install a recommended addon by name (calls download_and_install)."""
        if not self._ensure_folder_selected():
            return
        # Provide feedback to user
        self._set_status(f"Installing {name}...")
        success = download_and_install(name, url, self.addons_folder)
        if success:
            messagebox.showinfo("Success", f"{name} has been installed successfully!")
        self._set_status("")  # clear status
    
    def install_from_url(self):
        """Install an addon from a user-provided GitHub URL."""
        if not self._ensure_folder_selected():
            return
        repo_url = self.url_var.get().strip()
        if not repo_url:
            messagebox.showwarning("No URL", "Please enter a GitHub repository URL.")
            return
        # Convert repo URL to zip URL if needed
        # e.g., https://github.com/author/Repo -> https://github.com/author/Repo/archive/refs/heads/master.zip
        zip_url = repo_url.rstrip('/')
        if not zip_url.endswith(".zip"):
            zip_url += "/archive/refs/heads/master.zip"
        name = repo_url.split('/')[-1]  # use repo name as addon name
        self._set_status(f"Installing {name}...")
        success = download_and_install(name, zip_url, self.addons_folder)
        if success:
            messagebox.showinfo("Success", f"{name} has been installed successfully!")
        self._set_status("")
    
    def _ensure_folder_selected(self):
        """Ensure the addons folder is selected, if not prompt the user."""
        if not self.addons_folder:
            messagebox.showwarning("AddOns Folder Required", "Please select your AddOns folder first.")
            return False
        return True
    
    def _set_status(self, message):
        """(Optional) Update a status bar or label with a message (could be extended)."""
        print(message)  # In a real UI, update a status label instead of print.
        
# Launch the application
if __name__ == "__main__":
    app = AddonManagerApp()
    # Create a simple menu or button to select folder
    menubar = tk.Menu(app)
    app.config(menu=menubar)
    file_menu = tk.Menu(menubar, tearoff=0)
    file_menu.add_command(label="Select AddOns Folder...", command=app.select_folder)
    menubar.add_cascade(label="File", menu=file_menu)
    app.mainloop()
