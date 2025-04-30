import os
import json
import re
import io
import shutil
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from urllib.request import Request, urlopen
import zipfile

# Configuration file path (stored in the user's home directory for persistence across sessions)
CONFIG_FILE = os.path.join(os.path.expanduser("~"), "twow_mod_manager_config.json")

# Load configuration if it exists, otherwise use defaults.
config = {"addons_folder": "", "mods": {}}  # mods: mapping of mod_folder_name -> info (URL, type, etc.)
if os.path.exists(CONFIG_FILE):
    try:
        with open(CONFIG_FILE, 'r') as f:
            config.update(json.load(f))
    except Exception as e:
        # If config fails to load, continue with default (and inform user)
        print(f"Warning: Could not load config file: {e}")

# Save configuration to file (called after any changes like folder selection, mod install/uninstall)
def save_config():
    try:
        with open(CONFIG_FILE, 'w') as f:
            json.dump(config, f, indent=4)
    except Exception as e:
        # If GUI is running, show error; otherwise, just print
        messagebox.showerror("Error", f"Could not save configuration: {e}")

# --- GitHub API Helper Functions ---
def get_latest_release_info(user, repo):
    """
    Retrieve the latest release info for a GitHub repo.
    Returns a tuple (download_url, tag_name) for the latest release, or (None, None) if no release exists or on error.
    """
    api_url = f"https://api.github.com/repos/{user}/{repo}/releases/latest"
    try:
        req = Request(api_url, headers={"User-Agent": "TWOW-ModMgr"})
        with urlopen(req) as resp:
            if resp.status != 200:
                return None, None  # No release found (GitHub returns 404 for no releases)
            data = json.loads(resp.read().decode('utf-8'))
        tag_name = data.get("tag_name")
        assets = data.get("assets", [])
        download_url = None
        if assets:
            # If release has assets, prefer a .zip asset if available
            for asset in assets:
                asset_url = asset.get("browser_download_url")
                if asset_url and asset_url.endswith(".zip"):
                    download_url = asset_url
                    break
            # If no .zip asset found, fall back to the first asset (if any)
            if download_url is None and len(assets) > 0:
                download_url = assets[0].get("browser_download_url")
        if download_url is None:
            # No assets or none chosen, use GitHub's auto-generated source zip for the release
            download_url = data.get("zipball_url")
        return download_url, tag_name
    except Exception as e:
        return None, None  # On any error (network issue, etc.), treat as no release info available

def get_default_branch(user, repo):
    """
    Get the default branch name of the repository (e.g., 'main' or 'master').
    Returns 'master' if unable to determine.
    """
    api_url = f"https://api.github.com/repos/{user}/{repo}"
    try:
        req = Request(api_url, headers={"User-Agent": "TWOW-ModMgr"})
        with urlopen(req) as resp:
            if resp.status != 200:
                return "master"
            data = json.loads(resp.read().decode('utf-8'))
        return data.get("default_branch", "master")
    except Exception:
        return "master"

def get_latest_commit_sha(user, repo, branch):
    """
    Get the latest commit SHA for the specified branch of a GitHub repo.
    Returns the commit SHA string, or None on error.
    """
    api_url = f"https://api.github.com/repos/{user}/{repo}/branches/{branch}"
    try:
        req = Request(api_url, headers={"User-Agent": "TWOW-ModMgr"})
        with urlopen(req) as resp:
            if resp.status != 200:
                return None
            data = json.loads(resp.read().decode('utf-8'))
        commit_info = data.get("commit")
        if commit_info:
            return commit_info.get("sha")
    except Exception:
        pass
    return None

# --- Mod Installation Function ---
def install_mod(url):
    """
    Install a mod from a given GitHub URL (repository URL or direct .zip URL).
    This handles downloading the mod (latest release or main branch) and extracting it to the AddOns folder.
    """
    url = url.strip()
    if not url:
        messagebox.showwarning("No URL Provided", "Please enter a GitHub URL for the mod.")
        return
    # Ensure the AddOns folder is set
    addons_dir = config.get("addons_folder", "")
    if not addons_dir:
        messagebox.showwarning("AddOns Folder Not Set", "Please select the Turtle WoW AddOns folder in the Settings tab before installing mods.")
        return

    # Determine GitHub user/repo from the URL if possible (for GitHub links)
    user = repo = None
    download_url = None
    release_tag = None
    branch = None

    # Identify if URL is a direct zip file link
    if url.lower().endswith(".zip"):
        download_url = url
        # Try to parse user and repo from the URL (if it's a GitHub zip link)
        m = re.match(r'https?://github\.com/([^/]+)/([^/]+)', url)
        if m:
            user, repo = m.group(1), m.group(2)
    else:
        # Likely a GitHub repository URL (possibly with branch)
        url_base = url.rstrip('/')  # strip trailing slash if any
        if url_base.endswith(".git"):
            url_base = url_base[:-4]  # remove .git suffix if present
        # Check for branch in URL (e.g., .../tree/<branch_name>)
        branch_match = re.search(r'/tree/([^/]+)', url_base)
        if branch_match:
            branch = branch_match.group(1)
            # Remove the branch path from URL to get base repo URL
            url_base = url_base.split('/tree/')[0]
        # Extract user and repo from the base URL
        m = re.match(r'https?://github\.com/([^/]+)/([^/]+)', url_base)
        if m:
            user, repo = m.group(1), m.group(2)
        else:
            messagebox.showerror("Invalid URL", "The URL provided is not a valid GitHub repository link.")
            return

        # Determine the appropriate download URL (try latest release first, fall back to branch zip)
        rel_url, rel_tag = get_latest_release_info(user, repo)
        if rel_url:
            download_url = rel_url
            release_tag = rel_tag  # store tag name of the release
        else:
            # No releases found, use the repository's branch (default branch if none specified in URL)
            if not branch:
                branch = get_default_branch(user, repo)
            download_url = f"https://github.com/{user}/{repo}/archive/refs/heads/{branch}.zip"

    if not download_url:
        messagebox.showerror("Download Error", "Could not determine a valid download link for the provided URL.")
        return

    # Determine intended mod folder name (defaults to repo name if known)
    mod_folder_name = repo or "NewMod"

    # Download the mod ZIP file
    try:
        req = Request(download_url, headers={"User-Agent": "TWOW-ModMgr"})
        with urlopen(req) as resp:
            if resp.status != 200:
                raise Exception(f"HTTP {resp.status}")
            zip_data = resp.read()
    except Exception as e:
        messagebox.showerror("Download Error", f"Failed to download mod from GitHub: {e}")
        return

    # Extract the ZIP into the AddOns directory
    try:
        with zipfile.ZipFile(io.BytesIO(zip_data)) as z:
            # Determine top-level structure of the zip to handle naming
            top_level_items = set()
            for info in z.infolist():
                # Ignore the archive itself; gather top-level folder/file names
                if info.filename.endswith('/'):
                    # directory entry
                    top_name = info.filename.split('/')[0]
                    if top_name:
                        top_level_items.add(top_name)
                else:
                    top_name = info.filename.split('/')[0]
                    if top_name:
                        top_level_items.add(top_name)
            # Remove any empty string from the set (just in case)
            top_level_items.discard('')

            # Check if archive has a single top-level folder
            single_folder = (len(top_level_items) == 1)
            root_folder = list(top_level_items)[0] if single_folder else None

            # Prepare final install path for the mod
            install_path = os.path.join(addons_dir, mod_folder_name)

            # If the mod folder already exists, confirm with the user about overwriting (this covers updates)
            if os.path.isdir(install_path):
                confirm = messagebox.askyesno("Overwrite Existing Mod",
                                              f"The add-on '{mod_folder_name}' is already installed. Do you want to overwrite it with the new version?")
                if not confirm:
                    return  # user chose not to overwrite
                # Remove the existing folder to clean up old files before installing the new version
                try:
                    shutil.rmtree(install_path)
                except Exception as e:
                    messagebox.showerror("Error", f"Failed to remove old version of the mod: {e}")
                    return

            if single_folder and root_folder:
                # The zip contains a single root folder (common for GitHub archives)
                z.extractall(addons_dir)  # extract the root folder directly under AddOns
                extracted_path = os.path.join(addons_dir, root_folder)
                # Rename the extracted folder to the desired mod_folder_name if different
                if os.path.exists(extracted_path):
                    if root_folder != mod_folder_name:
                        os.rename(extracted_path, install_path)
                    else:
                        install_path = extracted_path  # names match, use as-is
            else:
                # The zip has multiple top-level files or folders; extract all contents into the new mod folder
                os.makedirs(install_path, exist_ok=True)
                for info in z.infolist():
                    name = info.filename
                    if name.endswith('/'):
                        # It's a directory; create it inside install_path
                        dir_path = os.path.join(install_path, name)
                        os.makedirs(dir_path, exist_ok=True)
                    else:
                        # It's a file; extract it to the appropriate location inside install_path
                        dest_path = os.path.join(install_path, name)
                        os.makedirs(os.path.dirname(dest_path), exist_ok=True)
                        with open(dest_path, 'wb') as f_out:
                            f_out.write(z.read(name))
        # If extraction is successful, notify user
        messagebox.showinfo("Installation Complete", f"Mod '{mod_folder_name}' has been installed successfully!")
    except Exception as e:
        messagebox.showerror("Installation Error", f"An error occurred while installing the mod:\n{e}")
        return

    # Update the internal config for this installed mod (store its source info for future updates)
    mod_info = {"url": url}
    if release_tag:
        mod_info["type"] = "release"
        mod_info["tag"] = release_tag
    else:
        mod_info["type"] = "branch"
        mod_info["branch"] = branch or "master"
        # For branch installs, record the latest commit SHA to help check for updates
        if user and repo:
            latest_sha = get_latest_commit_sha(user, repo, mod_info["branch"])
            if latest_sha:
                mod_info["commit"] = latest_sha
    config["mods"][mod_folder_name] = mod_info
    save_config()
    refresh_installed_mods_list()  # refresh the list of installed mods in the GUI

# --- Mod Uninstallation Function ---
def uninstall_mod():
    """
    Uninstall the selected mod by deleting its folder from the AddOns directory.
    Updates the config to remove the mod entry.
    """
    addons_dir = config.get("addons_folder", "")
    if not addons_dir:
        messagebox.showwarning("AddOns Folder Not Set", "Please select the AddOns folder in Settings first.")
        return
    # Get the selected mod from the listbox
    selection = installed_listbox.curselection()
    if not selection:
        messagebox.showwarning("No Selection", "Please select a mod to uninstall from the list.")
        return
    mod_name = installed_listbox.get(selection[0])
    mod_path = os.path.join(addons_dir, mod_name)
    if not os.path.isdir(mod_path):
        messagebox.showerror("Error", f"Mod folder '{mod_name}' not found. It may have already been removed.")
        refresh_installed_mods_list()
        return
    # Confirm uninstallation with the user
    if not messagebox.askyesno("Confirm Uninstall", f"Are you sure you want to uninstall the mod '{mod_name}'?"):
        return
    # Attempt to delete the mod directory
    try:
        shutil.rmtree(mod_path)
    except Exception as e:
        messagebox.showerror("Error", f"Failed to uninstall '{mod_name}': {e}")
        return
    # Remove the mod from our config (if it was installed via the manager)
    if mod_name in config["mods"]:
        config["mods"].pop(mod_name, None)
        save_config()
    messagebox.showinfo("Mod Uninstalled", f"The mod '{mod_name}' has been uninstalled.")
    refresh_installed_mods_list()

# --- Mod Update Function ---
def update_mod():
    """
    Update the selected mod by checking GitHub for a newer version and reinstalling it if available.
    If the mod is up-to-date or was not installed via this manager, appropriate messages are shown.
    """
    addons_dir = config.get("addons_folder", "")
    if not addons_dir:
        messagebox.showwarning("AddOns Folder Not Set", "Please select the AddOns folder in Settings.")
        return
    selection = installed_listbox.curselection()
    if not selection:
        messagebox.showwarning("No Selection", "Please select a mod to update.")
        return
    mod_name = installed_listbox.get(selection[0])
    if mod_name not in config["mods"]:
        messagebox.showwarning("Not Managed", "Update information is not available for this mod (it may not have been installed via this tool).")
        return

    mod_info = config["mods"][mod_name]
    source_url = mod_info.get("url")
    if not source_url:
        messagebox.showerror("Error", "No source URL available for this mod to check for updates.")
        return

    # Determine if an update is needed by comparing release tag or commit SHA
    update_available = True  # default to True, will adjust below
    if mod_info.get("type") == "release":
        # Check latest release tag on GitHub
        m = re.match(r'https?://github\.com/([^/]+)/([^/]+)', source_url)
        if m:
            user, repo = m.group(1), m.group(2)
            _, latest_tag = get_latest_release_info(user, repo)
            current_tag = mod_info.get("tag")
            if latest_tag and current_tag:
                if latest_tag == current_tag:
                    update_available = False  # already up-to-date
                else:
                    release_msg = f"New version available: {latest_tag} (currently installed: {current_tag})"
                    messagebox.showinfo("Update Found", f"Updating '{mod_name}' to the latest version.\n{release_msg}")
                    # We will proceed to reinstall the mod below
            # If we couldn't get release info, we'll attempt to update anyway.
    elif mod_info.get("type") == "branch":
        # Check latest commit on GitHub for the branch
        m = re.match(r'https?://github\.com/([^/]+)/([^/]+)', source_url)
        if m:
            user, repo = m.group(1), m.group(2)
            branch = mod_info.get("branch", "master")
            latest_sha = get_latest_commit_sha(user, repo, branch)
            current_sha = mod_info.get("commit")
            if latest_sha and current_sha:
                if latest_sha == current_sha:
                    update_available = False  # already up-to-date
                else:
                    messagebox.showinfo("Update Found", f"A new update for '{mod_name}' is available. It will now be updated to the latest version.")
            # If no SHA info (either current or latest), proceed with update (cannot verify, so assume needed)

    if not update_available:
        messagebox.showinfo("No Update Needed", f"'{mod_name}' is already up-to-date.")
        return

    # Reinstall the mod (this will effectively update it)
    install_mod(source_url)

# --- Utility: Refresh Installed Mods List ---
def refresh_installed_mods_list():
    """
    Refresh the Listbox that displays installed mods by scanning the AddOns directory.
    """
    installed_listbox.delete(0, tk.END)
    addons_dir = config.get("addons_folder", "")
    if not addons_dir or not os.path.isdir(addons_dir):
        return
    try:
        for name in os.listdir(addons_dir):
            full_path = os.path.join(addons_dir, name)
            if os.path.isdir(full_path):
                # Skip internal Blizzard add-on folders if any (in WoW, these start with Blizzard_)
                if name.lower().startswith("blizzard_"):
                    continue
                installed_listbox.insert(tk.END, name)
    except Exception as e:
        messagebox.showerror("Error", f"Could not list AddOns folder:\n{e}")

# --- Settings: Browse for AddOns Folder ---
def browse_folder():
    """
    Open a dialog for the user to select the Turtle WoW AddOns folder. Update config and UI accordingly.
    """
    path = filedialog.askdirectory(title="Select Turtle WoW AddOns Folder")
    if path:
        config["addons_folder"] = path
        save_config()
        # Update the folder entry field
        folder_entry.config(state="normal")
        folder_entry.delete(0, tk.END)
        folder_entry.insert(0, path)
        folder_entry.config(state="readonly")
        refresh_installed_mods_list()

# --- GUI Setup ---
root = tk.Tk()
root.title("Turtle WoW Mod Manager")
root.resizable(False, False)  # fix window size for simplicity

# Create Notebook (tabbed interface)
notebook = ttk.Notebook(root)
notebook.pack(expand=True, fill="both", padx=5, pady=5)

# Define frames for each tab
tab_install = ttk.Frame(notebook)
tab_installed = ttk.Frame(notebook)
tab_settings = ttk.Frame(notebook)
notebook.add(tab_install, text="Install Mod")
notebook.add(tab_installed, text="Installed Mods")
notebook.add(tab_settings, text="Settings")

## Install Mod tab ##
# URL input and install button
url_label = ttk.Label(tab_install, text="GitHub Repository URL:")
url_label.pack(pady=(10, 0))
url_entry = ttk.Entry(tab_install, width=50)
url_entry.pack(pady=5)
install_btn = ttk.Button(tab_install, text="Install from URL", command=lambda: install_mod(url_entry.get()))
install_btn.pack(pady=5)

# Recommended mods section
recomm_label = ttk.Label(tab_install, text="Built-in Recommended Mods:")
recomm_label.pack(pady=(15, 5))
# Two example recommended mods for one-click install (pfQuest and pfQuest-turtle)
recommended_mods = [
    ("pfQuest (Quest Helper)", "https://github.com/shagu/pfQuest"),
    ("pfQuest-Turtle (Turtle WoW Database)", "https://github.com/shagu/pfQuest-turtle")
]
for mod_name, mod_url in recommended_mods:
    btn = ttk.Button(tab_install, text=f"Install {mod_name}", command=lambda url=mod_url: install_mod(url))
    btn.pack(pady=2)

## Installed Mods tab ##
inst_label = ttk.Label(tab_installed, text="Installed Mods:")
inst_label.pack(pady=(10, 0))
# Frame to hold listbox and scrollbar side by side
list_frame = ttk.Frame(tab_installed)
list_frame.pack(expand=True, fill="both", padx=10, pady=5)
scrollbar = ttk.Scrollbar(list_frame, orient=tk.VERTICAL)
installed_listbox = tk.Listbox(list_frame, yscrollcommand=scrollbar.set, height=10)
scrollbar.config(command=installed_listbox.yview)
# Pack listbox and scrollbar into the frame
installed_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
# Buttons for update/uninstall below the list
btn_frame = ttk.Frame(tab_installed)
btn_frame.pack(pady=5)
update_btn = ttk.Button(btn_frame, text="Update Selected", command=update_mod)
update_btn.pack(side=tk.LEFT, padx=5)
uninstall_btn = ttk.Button(btn_frame, text="Uninstall Selected", command=uninstall_mod)
uninstall_btn.pack(side=tk.LEFT, padx=5)
refresh_btn = ttk.Button(btn_frame, text="Refresh List", command=refresh_installed_mods_list)
refresh_btn.pack(side=tk.LEFT, padx=5)

## Settings tab ##
folder_label = ttk.Label(tab_settings, text="Turtle WoW AddOns Folder:")
folder_label.pack(pady=(10, 0))
folder_entry = ttk.Entry(tab_settings, width=50)
folder_entry.pack(pady=5)
browse_btn = ttk.Button(tab_settings, text="Browse...", command=browse_folder)
browse_btn.pack(pady=5)
# Initialize the folder_entry with current config value, set to read-only
if config.get("addons_folder"):
    folder_entry.insert(0, config["addons_folder"])
folder_entry.config(state="readonly")

# Populate the installed mods list at startup
refresh_installed_mods_list()

# Start the GUI event loop
root.mainloop()
