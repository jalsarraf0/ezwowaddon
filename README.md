# 🐢 EZWowAddon - Turtle WoW Addon Manager

**EZWowAddon** is a lightweight, beginner-friendly addon manager for [Turtle WoW](https://turtle-wow.org/).  
Designed with ease-of-use in mind, this app lets you install, update, and remove WoW addons directly from GitHub — without needing to touch ZIP files or game folders.

> 💡 No tech skills needed. Just point, click, and play.

---

## 💸 Donations

If you find this tool helpful, consider supporting development:

- **Bitcoin (BTC):** `bc1ql8c04fwcz8fxmqzcr3mnaarn0auajw7jswy6hq`
- **Ethereum (ETH):** `0xdc0c587e811330C11e3E80caaB1961FA85Cadd81`
- **Litecoin (LTC):** `ltc1q5mme730eyw9lrsjfclwafmvz76tv0n3vn5h6xn.`
- **Ethereum (ETH) on Base:** `0xdc0c587e811330C11e3E80caaB1961FA85Cadd81`
- **XRP:** `rUyRSXTFNfC8mHtxNMA2MRy7MPWHf5gSWm`

If you like my work and want to keep me motivated, send a buck or two — anything helps!

---

## 🎯 Features

✅ Beginner-friendly graphical interface with tabs  
✅ One-click install of popular addons like **pfQuest**  
✅ Paste any GitHub repo URL to install custom addons  
✅ Auto-detect and remember your Turtle WoW `AddOns` folder  
✅ Detects already-installed addons and updates button labels  
✅ View and cleanly uninstall installed addons  
✅ Fully self-contained executable for Windows (.exe)

---

## 🧩 Download
### 🪟 Option 1: Prebuilt Binaries (Recommended)

Go to the [Releases page](https://github.com/jalsarraf0/ezwowaddon/releases) and download the latest assets for your platform, or use the command-line instructions below:

- **Windows:** `ezwow.exe`
- **Linux:** `ezwow` (make executable and run)
- **macOS:** `ezwow` (or app bundle if available)

#### Download via command-line

##### Linux/macOS
```bash
curl -fsSL https://github.com/jalsarraf0/ezwowaddon/releases/latest/download/ezwow -o ezwow && chmod +x ezwow
```

##### Windows (PowerShell)
```powershell
Invoke-WebRequest -Uri https://github.com/jalsarraf0/ezwowaddon/releases/latest/download/ezwow.exe -OutFile ezwow.exe
```

1. Run the downloaded binary
2. Select your Turtle WoW AddOns folder
3. Click to install a recommended addon or paste a GitHub URL
4. Enjoy!

---

### 🐧 Option 2: Run from Python (Developers or Linux/macOS users)

1. Install Python 3.11+ and `requests`
2. Clone this repo:
   ```bash
   git clone https://github.com/jalsarraf0/ezwowaddon.git
   cd ezwowaddon
   pip install requests
   python ezwow.py
   ```

---

## 📦 Built-In Recommended Addons

| Addon Name      | Description                            | GitHub Link                                                   |
|-----------------|----------------------------------------|----------------------------------------------------------------|
| pfQuest          | Quest helper with in-game markers      | [shagu/pfQuest](https://github.com/shagu/pfQuest)             |
| pfQuest-Turtle   | Turtle WoW-specific quest data         | [shagu/pfQuest-turtle](https://github.com/shagu/pfQuest-turtle) |
| BigWigs          | Boss warnings and timers               | [CosminPOP/BigWigs](https://github.com/CosminPOP/BigWigs)     |
| ShaguTweaks      | QoL enhancements for 1.12              | [shagu/ShaguTweaks](https://github.com/shagu/ShaguTweaks)     |
| Auctionator      | Simple auction house UI improvements   | [nimeral/AuctionatorVanilla](https://github.com/nimeral/AuctionatorVanilla) |
| Aux              | Advanced AH addon for Vanilla          | [gwetchen/aux-addon](https://github.com/gwetchen/aux-addon)   |

> 🆕 **Auctionator** and **Aux** were added in version 1.0.0.  
> ❌ **AtlasLootClassic** and **LunaUnitFrames** were removed for a more focused user experience.

---

## ❓ FAQ

**Q: Can I use this with Retail or Classic WoW?**  
🛑 No. This tool is made specifically for [Turtle WoW](https://turtle-wow.org/).

**Q: Where is my AddOns folder?**  
Default Windows path:  
`C:\Games\Turtle WoW\_classic_\Interface\AddOns`

**Q: Is this safe?**  
✅ Yes. It installs open-source addons directly from GitHub. No external binaries.

---

## 🛠 Developer Info

- Language: Python 3.11+
- GUI: Tkinter
- Packaging: PyInstaller
- License: MIT
- Platform: Windows/Linux/macOS

**Note:** Prebuilt binaries for Windows, Linux, and macOS are automatically built and attached to each GitHub release via CI.

To build the executable locally:

```bash
pip install requests pyinstaller
pyinstaller --noconfirm --onefile --windowed ezwow.py
```

---

## 🤝 Contributing

Pull requests and feedback are welcome!

Have a suggested addon or want to improve the interface?  
Open a GitHub issue or submit a PR!

---

## 📜 License

MIT License  
© 2025 Jamal Al-Sarraf  
[https://github.com/jalsarraf0](https://github.com/jalsarraf0)
