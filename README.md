# Icon Changer — Windows Icon Customizer 🎨

A fast, lightweight, and modern Windows desktop application that lets you customize the icon for any **folder**, **shortcut (.lnk)**, or **file** on your PC directly from the Windows right-click context menu or via a full-featured desktop interface.

---

## ✨ Features

- **Right-Click Context Menu Integration**: Right-click any Folder, File, or Shortcut (.lnk) in Windows Explorer and select **"Change Icon"**.
- **Quick Popup Picker**:
  - Pops up in under **400ms** right next to your mouse cursor.
  - Automatically searches for transparent icons based on your item name (e.g., `gta v "icon png"`).
  - **Click any icon to instantly set it!**
  - **In-Popup Shortcuts & Controls**:
    - **Search Box**: Refine search keywords on the fly without going to Settings.
    - **Provider Selector**: Switch between *Google & Web Images*, *Icons8*, and *Google Custom Search API*.
    - **Resolution Selector**: Choose from `256x256`, `128x128`, `64x64`, `48x48`, `32x32`, `16x16`, or `Multi-Size .ICO`.
    - **Browse Local**: Select local `.ico`, `.png`, `.jpg`, `.dll`, or `.exe` files.
    - **Restore Default**: 1-click restore default Windows icon.
    - **Keyboard Controls**: `Arrow keys` to move selection, `Enter` to set, `Esc` to exit, `F5` to refresh.
- **Full Desktop Program with Settings**:
  - **Customizer Workspace**: Drag & drop any folder, file, or shortcut to customize.
  - **Customization History**: Browse all previously customized items on your PC with 1-click "Restore Default" or "Change Icon".
  - **Settings & Context Menu**:
    - Customize search suffix (e.g. change `"icon png"` to `"logo png"`, `"transparent icon"`, etc.).
    - Customize search query template (`{name} {suffix}`).
    - Optional Google Custom Search API credentials (API Key + CX).
    - Context menu 1-click install/uninstall with status badge.
    - Cache management and Windows shell refresh (`SHChangeNotify`).
- **High-Quality Transparent ICO Conversion**:
  - Fetches transparent PNG images and converts them directly to multi-resolution Windows `.ico` files preserving the alpha transparency channel (no black or ugly borders).
- **Lightweight & Zero Background Footprint**:
  - **0% CPU and 0 MB RAM** when idle (no persistent background daemon).
  - Native PyQt5 + Windows Win32 API. Uses ~40MB RAM only when opened.

---

## 🚀 Getting Started

### 1. Requirements
- Windows 10 or Windows 11
- Python 3.10+ (Python 3.12 recommended)

### 2. Install Dependencies
```bash
pip install -r requirements.txt
```

### 3. Add to Windows Context Menu (1-Click)
Double-click `setup_context_menu.bat` or run:
```bash
python run.py --install
```
> **Note**: Installs to `HKEY_CURRENT_USER\Software\Classes`, so **no Administrator privileges or UAC prompts** are required!

### 4. Launch Full Program
Double-click `run.py` or run:
```bash
python run.py
```

---

## 🎯 How to Use

### Method A: From the Windows Context Menu (Quickest)
1. In Windows Explorer or on your Desktop, **right-click** any folder, shortcut, or file.
2. Click **"Change Icon"**.
3. The Quick Picker window pops up displaying transparent icons.
4. **Click an icon** — it downloads, converts to `.ico`, applies it to your item, notifies Windows Explorer, and closes!

### Method B: From the Full Program
1. Launch `python run.py`.
2. Drag and drop any folder, shortcut, or file into the top drop zone (or click **Browse**).
3. Search icons or browse local icon files.
4. Preview the icon on a transparent checkerboard.
5. Click **"Apply Selected Icon"**.

### Restoring Default Icons
- In the Quick Picker: Click **"Restore Default"**.
- In the Full Program: Select the target and click **"Restore Default Icon"**, or go to the **Customization History** tab and click **"Restore"** next to any item.

---

## ⚙ Search Options & Settings

You can customize how icons are searched in the **Settings** tab:
- **Search Suffix**: Change the default `icon png` to anything you prefer (e.g. `gta v "icon png"`, `transparent icon`, `logo png`).
- **Query Template**: Format how queries are constructed (`{name} {suffix}`).
- **Default Resolution**:
  - `256x256 (Crisp)`: High-definition icon for extra large views.
  - `Multi-Size .ICO`: Bundles 16x16, 24x24, 32x32, 48x48, 64x64, 128x128, and 256x256 into a single ICO so Windows Explorer renders crisply at every view size (Details, List, Tiles, Small, Medium, Large, Extra Large).
- **Icon Providers**:
  1. **Google & Web Images**: Searches and downloads high-res transparent PNGs directly from web sources.
  2. **Icons8**: Access to over 1.5 million clean, transparent vector and raster icons.
  3. **Google Custom Search API**: For users who prefer official Google Images API (requires free API Key and CX).

---

## 📁 Project Architecture

```
icon/
├── icon_changer/
│   ├── core/
│   │   ├── config.py           # Configuration manager & AppData paths
│   │   ├── icon_engine.py      # Transparent PNG to multi-res ICO converter
│   │   ├── icon_applicator.py  # Windows desktop.ini, .lnk WScript.Shell, SHChangeNotify
│   │   ├── shell_manager.py    # HKCU context menu registration
│   │   └── history.py          # Customization history database
│   ├── providers/
│   │   ├── base.py             # IconResult & BaseProvider interface
│   │   ├── web_search.py       # Google & Web transparent PNG scraper
│   │   ├── icons8_search.py    # Icons8 API integration
│   │   └── google_cse.py       # Google Custom Search API integration
│   ├── ui/
│   │   ├── styles.py           # Fluent dark theme QSS
│   │   ├── widgets.py          # IconCard with checkerboard & responsive IconGrid
│   │   ├── quick_picker.py     # Context menu popup window
│   │   ├── settings_tab.py     # Full settings & context menu manager
│   │   └── main_window.py      # Main workspace & history interface
│   └── main.py                 # CLI and GUI entrypoint
├── tests/                      # Full unit and GUI test suite (10/10 passing)
├── run.py                      # Root launcher
├── build_exe.py                # Standalone executable compiler
├── setup_context_menu.bat      # 1-click context menu installer
├── remove_context_menu.bat     # 1-click context menu uninstaller
└── requirements.txt            # Python dependencies
```

---

## 🛠 Standalone Executable Build

To compile a standalone `.exe` that does not require Python:
```bash
python build_exe.py
```
The resulting executable will be in `dist/IconChanger/IconChanger.exe`.
