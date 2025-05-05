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

✅ Intuitive graphical interface (tabbed layout)  
✅ One-click install of popular addons like **pfQuest**  
✅ Paste any GitHub repo URL to install custom addons  
✅ Auto-detect and remember your Turtle WoW `AddOns` folder  
✅ Update or reinstall mods directly from GitHub  
✅ Clean uninstall of addons  
✅ Beginner-proof: No ZIP handling, no manual file placement  
✅ Can be compiled into a portable `.exe` for offline use  

---

## 🧩 Download

### 🔻 Option 1: Download `.exe` (Recommended for most users)

Visit the [Releases page](https://github.com/jalsarraf0/ezwowaddon/releases) and grab the latest version:

1. Run the `.exe`
2. Select your Turtle WoW `AddOns` folder
3. Click to install pfQuest or paste a GitHub link
4. Done!

No setup, no ZIP files, no terminal required.

---

### 🧠 Option 2: Run from Source (For Developers)

1. Ensure **Python 3.11+** is installed
2. Clone or download this repository
3. From the terminal:

```bash
pip install requests
python ezwow.py
```

You’re now running it from source.

---

## 📦 Built-In Recommended Addons

| Addon Name        | Description                             | GitHub Link                                        |
|------------------|-----------------------------------------|---------------------------------------------------|
| pfQuest           | Quest helper with in-game markers       | [pfQuest](https://github.com/shagu/pfQuest)       |
| pfQuest-Turtle    | Turtle WoW-specific quest data          | [pfQuest-Turtle](https://github.com/shagu/pfQuest-turtle) |
| BigWigs           | Boss warnings and timers                | [BigWigs](https://github.com/CosminPOP/BigWigs)   |
| LunaUnitFrames    | Customizable unit frame replacement     | [LunaUnitFrames](https://github.com/Aviana/LunaUnitFrames) |
| ShaguTweaks       | Quality of life enhancements            | [ShaguTweaks](https://github.com/shagu/ShaguTweaks) |
| AtlasLootClassic  | Loot browser and dungeon drops          | [AtlasLootClassic](https://github.com/AtlasLoot/AtlasLootClassic) |

---

## ❓ FAQ

**Q: Can I use this with Retail or Classic WoW?**  
🛑 No. This tool is made specifically for [Turtle WoW](https://turtle-wow.org/).

**Q: Where is my `AddOns` folder?**  
Usually located at:  
`C:\Games\Turtle WoW\_classic_\Interface\AddOns`

**Q: Is this safe?**  
✅ Yes. It only downloads open-source addons from GitHub and puts them in your AddOns folder.

---

## 🛠 Developer Info

- Language: Python 3.11+
- GUI: Tkinter
- Build Tool: PyInstaller
- Platform: Windows (compiled `.exe`) or cross-platform (via Python)
- License: MIT

To build the executable:

```bash
python -m PyInstaller --noconfirm --onefile --windowed ezwow.py
```

---

## 🤝 Contributing

Pull requests and feedback are always welcome!

- Want to suggest more built-in addons?  
- Want to contribute UI improvements or threading?

Open an issue or PR!

---

## 📜 License

MIT License  
© 2025 Jamal Al-Sarraf  
[https://github.com/jalsarraf0](https://github.com/jalsarraf0)
