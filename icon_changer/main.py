import sys
import os
import argparse
import traceback
import time
from pathlib import Path
from typing import Optional

# Ensure the root package is in sys.path
BASE_DIR = Path(__file__).resolve().parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from PyQt5 import QtCore, QtGui, QtWidgets
from icon_changer.core.config import config
from icon_changer.core.shell_manager import ShellManager

def setup_exception_handler() -> None:
    """Catches any unhandled exceptions, logs them to crash.log, and alerts the user."""
    def handle_exception(exc_type, exc_value, exc_traceback):
        if issubclass(exc_type, KeyboardInterrupt):
            sys.__excepthook__(exc_type, exc_value, exc_traceback)
            return

        err_msg = "".join(traceback.format_exception(exc_type, exc_value, exc_traceback))

        log_file = None
        try:
            log_dir = config.CONFIG_DIR
            log_dir.mkdir(parents=True, exist_ok=True)
            log_file = log_dir / "crash.log"
            with open(log_file, "a", encoding="utf-8") as f:
                f.write(f"\n==================== CRASH AT {time.strftime('%Y-%m-%d %H:%M:%S')} ====================\n")
                f.write(err_msg)
        except Exception:
            pass

        try:
            if QtWidgets.QApplication.instance():
                QtWidgets.QMessageBox.critical(
                    None,
                    "IconChanger — Unexpected Error",
                    f"An error occurred:\n\n{exc_value}\n\nCrash log saved to:\n{log_file if log_file else 'crash.log'}"
                )
        except Exception:
            pass

        sys.__excepthook__(exc_type, exc_value, exc_traceback)

    sys.excepthook = handle_exception

def clean_path(raw: Optional[str]) -> Optional[str]:
    """Cleans path strings passed from Windows Explorer command line."""
    if not raw:
        return None
    cleaned = raw.strip().strip('"\' \t\r\n')
    cleaned = cleaned.rstrip('"\'')
    if not cleaned:
        return None

    # Try resolving path
    try:
        p = Path(cleaned).resolve()
        if p.exists():
            return str(p)
    except Exception:
        pass

    # Try stripped trailing slashes
    trimmed = cleaned.rstrip('\\/')
    if trimmed and os.path.exists(trimmed):
        return str(Path(trimmed).resolve())

    if os.path.exists(cleaned):
        return cleaned

    return cleaned

def main() -> None:
    setup_exception_handler()

    parser = argparse.ArgumentParser(description="Windows Icon Customizer")
    parser.add_argument("--quick", "-q", help="Open Quick Picker popup for target path", default=None)
    parser.add_argument("--target", "-t", help="Open Full Program with target selected", default=None)
    parser.add_argument("--settings", "-s", action="store_true", help="Open Settings tab directly")
    parser.add_argument("--install", action="store_true", help="Install context menu entries to Windows Explorer")
    parser.add_argument("--uninstall", action="store_true", help="Uninstall context menu entries from Windows Explorer")
    
    parser.add_argument("--elevated-apply", nargs=2, metavar=("TARGET", "ICO"), help=argparse.SUPPRESS)
    
    # Handle %1 or positional arguments passed by Windows Explorer
    parser.add_argument("positional_target", nargs="?", default=None, help="Target file/folder path")

    args, unknown = parser.parse_known_args()

    # Elevated apply helper (runs silently as admin via UAC when permissions require it)
    if args.elevated_apply:
        from icon_changer.core.icon_applicator import IconApplicator
        elev_target, elev_ico = args.elevated_apply
        success, msg = IconApplicator.apply_icon(elev_target, elev_ico)
        sys.exit(0 if success else 1)

    # CLI actions (no GUI needed)
    if args.install:
        ok, msg = ShellManager.install(menu_label=config.get("context_menu_label", "Change Icon"))
        print(f"[{'SUCCESS' if ok else 'FAILED'}] {msg}")
        sys.exit(0 if ok else 1)

    if args.uninstall:
        ok, msg = ShellManager.uninstall()
        print(f"[{'SUCCESS' if ok else 'FAILED'}] {msg}")
        sys.exit(0 if ok else 1)

    # Initialize Qt Application with High-DPI support
    QtWidgets.QApplication.setAttribute(QtCore.Qt.AA_EnableHighDpiScaling, True)
    QtWidgets.QApplication.setAttribute(QtCore.Qt.AA_UseHighDpiPixmaps, True)
    app = QtWidgets.QApplication(sys.argv)
    app.setApplicationName("IconChanger")
    app.setOrganizationName("IconChangerApp")
    app.setQuitOnLastWindowClosed(True)

    # Set Global Application Icon (Logo)
    app_icon_path = BASE_DIR / "assets" / "app_icon.ico"
    if not app_icon_path.exists():
        app_icon_path = Path(sys.executable).parent / "assets" / "app_icon.ico"
    if app_icon_path.exists():
        app.setWindowIcon(QtGui.QIcon(str(app_icon_path)))

    # Check if configured to always run as administrator
    from icon_changer.core.permissions import PermissionManager
    if config.get("run_as_admin", False) and not PermissionManager.is_running_as_admin():
        PermissionManager.relaunch_as_admin()

    # Determine and sanitize target path if provided
    raw_target = args.quick or args.target or args.positional_target
    target = clean_path(raw_target)

    # Import UI modules after QApplication creation to ensure thread-safe Qt engine init
    from icon_changer.ui.quick_picker import QuickPickerWindow
    from icon_changer.ui.main_window import MainWindow

    if args.quick:
        if target and os.path.exists(target):
            # Open Quick Context Menu Popup
            picker = QuickPickerWindow(target)
            picker.show()
            sys.exit(app.exec_())
        else:
            QtWidgets.QMessageBox.warning(
                None,
                "IconChanger",
                f"Target path does not exist or cannot be accessed:\n\n{raw_target or '(empty)'}"
            )
            sys.exit(1)
    else:
        # Open Full Program UI
        main_win = MainWindow(initial_target=target or "")
        if args.settings:
            main_win.tabs.setCurrentIndex(2)
        main_win.show()
        sys.exit(app.exec_())

if __name__ == "__main__":
    main()
