<div align="center">

  <img src="assets/app_icon.png" width="128" height="128" alt="ixon logo" style="border-radius: 28px; box-shadow: 0 10px 30px rgba(124, 92, 252, 0.35);" />

  # ixon

  ### Modern Windows Icon Customizer & Shell Integration Tool

  <p align="center">
    <b>Instantly search, customize, and apply high-definition transparent icons to folders, shortcuts, and files with zero lag.</b>
  </p>

  <p align="center">
    <a href="https://github.com/devilmancrybabyx/ixon/releases/latest"><img src="https://img.shields.io/github/v/release/devilmancrybabyx/ixon?style=for-the-badge&color=7c5cfc&logo=windows&logoColor=white" alt="Latest Release" /></a>
    <a href="https://github.com/devilmancrybabyx/ixon/releases"><img src="https://img.shields.io/github/downloads/devilmancrybabyx/ixon/total?style=for-the-badge&color=00d26a&logo=github" alt="Downloads" /></a>
    <img src="https://img.shields.io/badge/Platform-Windows%2010%20%7C%2011-0078d4?style=for-the-badge&logo=windows11&logoColor=white" alt="Platform Windows" />
    <img src="https://img.shields.io/badge/Memory%20Footprint-%3C%2010%20MB-purple?style=for-the-badge&logo=speedtest&logoColor=white" alt="Memory Footprint" />
    <a href="LICENSE"><img src="https://img.shields.io/badge/License-MIT-blue?style=for-the-badge" alt="License MIT" /></a>
    <img src="https://img.shields.io/badge/Build-Passing-brightgreen?style=for-the-badge&logo=checkmarx&logoColor=white" alt="Build Status" />
  </p>

  <p align="center">
    <a href="#-quick-download"><b>📥 Download Release</b></a> •
    <a href="#-key-features"><b>✨ Features</b></a> •
    <a href="#-visual-previews"><b>📸 Previews</b></a> •
    <a href="#-quick-start"><b>🚀 Quick Start</b></a> •
    <a href="#-keyboard-shortcuts"><b>⌨ Shortcuts</b></a> •
    <a href="#-architecture--performance"><b>🧠 Architecture</b></a>
  </p>

  <br />

  <img src="assets/preview.png" width="820" alt="ixon Quick Picker Context Menu UI" style="border-radius: 16px; box-shadow: 0 16px 40px rgba(0,0,0,0.6);" />

</div>

---

## ⚡ Highlights

**ixon** replaces the clunky 1990s Windows "Change Icon" dialog with an ultra-responsive, neumorphic popup right at your mouse cursor. Right-click any folder or shortcut, choose from live high-res transparent web results or vector icon libraries, and apply instantly with automated multi-size `.ico` generation.

- 🪄 **Pristine Edge Defringing**: Proprietary vectorized edge erosion and color un-matting completely eliminates ugly white halo outlines around transparent icons.
- 🚀 **Zero-Lag Explorer Refresh**: Uses Windows Shell notification (`SHChangeNotify`) and window broadcasting (`WM_COMMAND`) to update icons immediately without restarting `explorer.exe`.
- 🪶 **Ultra-Lightweight (<10 MB RAM)**: Active working set memory trimmer purges resident memory down to ~5 MB (idle <1 MB). Single-process enforcement prevents zombie background tasks.
- 🛡 **Zero UAC Annoyances**: Installs cleanly into `HKEY_CURRENT_USER\Software\Classes` without requesting admin privileges or triggering elevation prompts for regular folders.

---

## 📸 Visual Previews

<div align="center">

### 1. Minimalist Quick Context-Menu Picker
*Frameless floating card, animated hamburger menu, instant provider switching, and vector icons.*

<img src="assets/preview.png" width="760" alt="Quick Picker Popup" style="border-radius: 12px; margin-bottom: 24px;" />

### 2. Full Application Workspace & History
*Drag-and-drop customization, multi-source search query templates, and 1-click restore for all customized items.*

<img src="assets/preview_main.png" width="760" alt="Full Desktop Application" style="border-radius: 12px;" />

</div>

---

## ✨ Key Features

| Feature | Description |
| :--- | :--- |
| **Instant Right-Click Popup** | Right-click any folder, shortcut (`.lnk`), or file in Explorer and select **"Change Icon"**. |
| **Multi-Engine Search** | Search across **Google & Web Images**, **Icons8 (1.5M+ Vector Icons)**, and official **Google Custom Search API**. |
| **Pristine Transparency** | Automatic background floodfill + vectorized defringing removes halos, artifacts, and anti-aliasing white borders. |
| **Multi-Resolution .ICO** | Packs 256×256, 128×128, 64×64, 48×48, 32×32, and 16×16 bitmaps so icons stay razor-sharp in every Explorer view mode. |
| **Local File Support** | Extract high-res icons from `.exe`, `.dll`, `.ico`, `.png`, `.jpg`, and `.webp` files. |
| **1-Click Restore** | Restore default Windows folder or shortcut icons with a single click. |
| **Animated Feedback** | Smooth checkmark overlay animation confirms customization upon selection. |

---

## 📥 Quick Download

Grab the latest standalone release from the [GitHub Releases page](https://github.com/devilmancrybabyx/ixon/releases/latest):

| Asset | Format | Description |
| :--- | :--- | :--- |
| **[IconChanger-v1.0.0-Windows-x64.zip](https://github.com/devilmancrybabyx/ixon/releases/latest)** | `.zip` | Portable release bundle. Extract anywhere and launch immediately. |
| **[IconChanger.exe](https://github.com/devilmancrybabyx/ixon/releases/latest)** | `.exe` | Standalone executable binary. |

---

## 🚀 Quick Start

### 1. Enable Windows Explorer Context Menu (1-Click)
Run `IconChanger.exe` with the `--install` flag, or click **Install** in the Settings tab:
```cmd
IconChanger.exe --install
```
> *Installs to `HKCU:\Software\Classes` without requiring administrator privileges or UAC popups.*

### 2. Customize an Icon
1. In Windows Explorer or on your Desktop, **right-click** any folder or shortcut.
2. Select **"Change Icon"**.
3. Type a keyword (or use the auto-populated folder name).
4. Click your desired icon — it converts, applies to `desktop.ini` / `IShellLink`, refreshes the desktop, and closes automatically!

---

## ⌨ Keyboard Shortcuts

| Shortcut | Action |
| :---: | :--- |
| `Arrow Keys` | Navigate through search result cards |
| `Enter` / `Return` | Apply selected icon card (or trigger search if input focused) |
| `Esc` | Close Quick Picker |
| `F5` | Refresh current search query |

---

## 🛠 Running from Source

If you prefer building or running from Python source:

### Prerequisites
- Windows 10 or 11 (64-bit)
- Python 3.10+ (Python 3.12 recommended)

### Setup
```bash
# Clone the repository
git clone https://github.com/devilmancrybabyx/ixon.git
cd ixon

# Install dependencies
pip install -r requirements.txt

# Run Quick Picker for a target folder
python run.py --quick "C:\path\to\your\folder"

# Or run the full desktop program
python run.py
```

### Compiling with PyInstaller
```bash
python build_exe.py
```
Compiled output will be placed in `dist/IconChanger/IconChanger.exe`.

---

## 🧠 Architecture & Performance

```mermaid
flowchart TD
    A[Explorer Context Menu] -->|--quick target| B[QuickPickerWindow]
    B -->|Async Search| C[Web / Icons8 / Google CSE Provider]
    C -->|Raw Image Bytes| D[Pristine Defringe Engine]
    D -->|Transparent RGBA| E[Multi-Res ICO Generator]
    E -->|Write desktop.ini / IShellLink| F[Windows Shell]
    F -->|SHChangeNotify + WM_COMMAND| G[Explorer & Desktop Instant Refresh]
    B -->|Automatic Purge| H[Working Set Trim < 10MB RAM]
```

- **Folder Customization**: Uses Windows `SHGetSetFolderCustomSettings` with UTF-16LE `desktop.ini` and applies `FILE_ATTRIBUTE_SYSTEM | FILE_ATTRIBUTE_READONLY`.
- **Shortcut Customization**: Leverages Windows COM `IShellLinkW` / `WScript.Shell` for instant shortcut icon redirection.
- **Defringing Algorithm**: Evaluates boundary pixels touching transparency channels, strips outer white halos (`r > 185, g > 185, b > 185`), and un-mattes anti-aliased edge blends using `(color - (1 - alpha) * 255) / alpha`.
- **Memory Optimization**: Leverages `kernel32.SetProcessWorkingSetSize` with `-1` purge flags to keep active RAM below 10 MB, alongside single-instance process cleanup.

---

## 📄 License

Distributed under the **MIT License**. See [`LICENSE`](LICENSE) for more details.

<div align="center">
  <sub>Built with ❤️ for Windows customization enthusiasts by <a href="https://github.com/devilmancrybabyx">@devilmancrybabyx</a></sub>
</div>
