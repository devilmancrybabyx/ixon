import os
import sys
import winreg
import ctypes
from ctypes import wintypes
from pathlib import Path
from typing import Tuple

APP_COMPAT_KEY = r"Software\Microsoft\Windows NT\CurrentVersion\AppCompatFlags\Layers"

class PermissionManager:
    """Manages administrator privilege detection, AppCompatFlags elevation, and process relaunching."""

    @staticmethod
    def is_running_as_admin() -> bool:
        """Checks if current process is running with elevated administrator privileges."""
        try:
            return ctypes.windll.shell32.IsUserAnAdmin() != 0
        except Exception:
            return False

    @staticmethod
    def get_app_executable() -> str:
        """Returns the target executable path to configure for elevation."""
        if getattr(sys, "frozen", False):
            return sys.executable
        # If in project directory, check if compiled exe exists first
        compiled_exe = Path(__file__).resolve().parent.parent.parent / "dist" / "IconChanger" / "IconChanger.exe"
        if compiled_exe.exists():
            return str(compiled_exe)
        return sys.executable

    @classmethod
    def is_full_permission_enabled(cls) -> bool:
        """Checks if RUNASADMIN flag is set in HKCU AppCompatFlags."""
        exe_path = cls.get_app_executable()
        try:
            with winreg.OpenKey(winreg.HKEY_CURRENT_USER, APP_COMPAT_KEY, 0, winreg.KEY_READ) as key:
                val, _ = winreg.QueryValueEx(key, exe_path)
                return "RUNASADMIN" in str(val).upper()
        except (FileNotFoundError, OSError):
            return False

    @classmethod
    def set_full_permission(cls, enabled: bool) -> Tuple[bool, str]:
        """
        Enables or disables automatic Administrator execution (~ RUNASADMIN)
        for the application and context menu in HKCU registry.
        """
        exe_path = cls.get_app_executable()
        try:
            if enabled:
                with winreg.CreateKey(winreg.HKEY_CURRENT_USER, APP_COMPAT_KEY) as key:
                    winreg.SetValueEx(key, exe_path, 0, winreg.REG_SZ, "~ RUNASADMIN")
                # Also update context menu entries to show UAC shield
                cls._set_context_menu_shield(True)
                return True, "Full Administrator permissions enabled for app and context menu."
            else:
                try:
                    with winreg.OpenKey(winreg.HKEY_CURRENT_USER, APP_COMPAT_KEY, 0, winreg.KEY_SET_VALUE) as key:
                        winreg.DeleteValue(key, exe_path)
                except (FileNotFoundError, OSError):
                    pass
                cls._set_context_menu_shield(False)
                return True, "Administrator requirement removed. Running in standard user mode."
        except Exception as e:
            return False, f"Failed to update permission settings: {e}"

    @staticmethod
    def _set_context_menu_shield(enable_shield: bool) -> None:
        """Adds or removes HasLUAShield registry value on context menu entries."""
        reg_keys = [
            r"Software\Classes\Directory\shell\ChangeIcon",
            r"Software\Classes\Directory\Background\shell\ChangeIcon",
            r"Software\Classes\lnkfile\shell\ChangeIcon",
            r"Software\Classes\*\shell\ChangeIcon",
        ]
        for key_path in reg_keys:
            try:
                with winreg.OpenKey(winreg.HKEY_CURRENT_USER, key_path, 0, winreg.KEY_SET_VALUE) as key:
                    if enable_shield:
                        winreg.SetValueEx(key, "HasLUAShield", 0, winreg.REG_SZ, "")
                    else:
                        try:
                            winreg.DeleteValue(key, "HasLUAShield")
                        except (FileNotFoundError, OSError):
                            pass
            except (FileNotFoundError, OSError):
                pass

    @classmethod
    def relaunch_as_admin(cls) -> bool:
        """Relaunches the current application elevated via Windows UAC prompt."""
        if cls.is_running_as_admin():
            return True

        if getattr(sys, "frozen", False):
            exe = sys.executable
            args = " ".join(f'"{a}"' for a in sys.argv[1:])
        else:
            exe = sys.executable
            main_script = Path(__file__).resolve().parent.parent / "main.py"
            args = f'"{main_script}" ' + " ".join(f'"{a}"' for a in sys.argv[1:])

        try:
            hinstance = ctypes.windll.shell32.ShellExecuteW(
                None,
                "runas",
                exe,
                args,
                None,
                1  # SW_SHOWNORMAL
            )
            if hinstance > 32:
                sys.exit(0)
            return False
        except Exception as e:
            print(f"Failed to relaunch as admin: {e}")
            return False
