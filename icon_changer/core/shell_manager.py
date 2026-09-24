import os
import sys
import winreg
from pathlib import Path
from typing import List, Tuple

REG_KEY_BASES = [
    r"Directory\shell\ChangeIcon",
    r"Directory\Background\shell\ChangeIcon",
    r"lnkfile\shell\ChangeIcon",
    r"*\shell\ChangeIcon",
]

class ShellManager:
    """Manages Windows Explorer Context Menu integration via HKCU registry."""

    @staticmethod
    def get_command_string() -> str:
        """Determines the launch command for the context menu."""
        # If running as compiled exe (PyInstaller)
        if getattr(sys, "frozen", False):
            exe_path = sys.executable
            return f'"{exe_path}" --quick "%1"'
        else:
            # Running as Python script
            # Use pythonw.exe to avoid flashing console window
            python_exe = sys.executable
            pythonw = os.path.join(os.path.dirname(python_exe), "pythonw.exe")
            if not os.path.exists(pythonw):
                pythonw = python_exe

            main_script = Path(__file__).resolve().parent.parent / "main.py"
            return f'"{pythonw}" "{main_script}" --quick "%1"'

    @staticmethod
    def get_bg_command_string() -> str:
        """Launch command for Directory Background (uses %V)."""
        cmd = ShellManager.get_command_string()
        return cmd.replace('"%1"', '"%V"')

    @classmethod
    def is_installed(cls) -> bool:
        """Checks if the context menu keys exist in HKCU."""
        key_path = rf"Software\Classes\{REG_KEY_BASES[0]}"
        try:
            with winreg.OpenKey(winreg.HKEY_CURRENT_USER, key_path, 0, winreg.KEY_READ):
                return True
        except (FileNotFoundError, OSError):
            return False

    @classmethod
    def install(cls, menu_label: str = "Change Icon", icon_path: str = "") -> Tuple[bool, str]:
        """
        Installs context menu entries into HKCU for Directory, Background, lnkfile, and *.
        """
        cmd_str = cls.get_command_string()
        bg_cmd_str = cls.get_bg_command_string()

        # If no custom icon specified, look for app_icon.ico or exe
        if not icon_path or not os.path.exists(icon_path):
            if getattr(sys, "frozen", False):
                icon_path = sys.executable
            else:
                assets_ico = Path(__file__).resolve().parent.parent.parent / "assets" / "app_icon.ico"
                if assets_ico.exists():
                    icon_path = str(assets_ico)
                else:
                    icon_path = "imageres.dll,-1001"

        default_menu_icon = icon_path

        from icon_changer.core.permissions import PermissionManager
        has_shield = PermissionManager.is_full_permission_enabled()

        try:
            for subkey in REG_KEY_BASES:
                full_path = rf"Software\Classes\{subkey}"
                with winreg.CreateKey(winreg.HKEY_CURRENT_USER, full_path) as key:
                    # Context menu label
                    label = "Change Folder Icon" if "Background" in subkey else menu_label
                    winreg.SetValueEx(key, "", 0, winreg.REG_SZ, label)
                    # Menu Icon
                    winreg.SetValueEx(key, "Icon", 0, winreg.REG_SZ, default_menu_icon)
                    # UAC shield if full permissions enabled
                    if has_shield:
                        winreg.SetValueEx(key, "HasLUAShield", 0, winreg.REG_SZ, "")
                    else:
                        try:
                            winreg.DeleteValue(key, "HasLUAShield")
                        except (FileNotFoundError, OSError):
                            pass

                # Set command
                cmd_path = rf"{full_path}\command"
                with winreg.CreateKey(winreg.HKEY_CURRENT_USER, cmd_path) as cmd_key:
                    target_cmd = bg_cmd_str if "Background" in subkey else cmd_str
                    winreg.SetValueEx(cmd_key, "", 0, winreg.REG_SZ, target_cmd)

            return True, "Context menu successfully installed for Folders, Files, and Shortcuts."
        except Exception as e:
            return False, f"Failed to install context menu: {e}"

    @classmethod
    def uninstall(cls) -> Tuple[bool, str]:
        """Removes context menu entries from HKCU."""
        try:
            for subkey in REG_KEY_BASES:
                full_path = rf"Software\Classes\{subkey}"
                # Recursively delete command subkey then main key
                try:
                    winreg.DeleteKey(winreg.HKEY_CURRENT_USER, rf"{full_path}\command")
                except OSError:
                    pass
                try:
                    winreg.DeleteKey(winreg.HKEY_CURRENT_USER, full_path)
                except OSError:
                    pass
            return True, "Context menu entries successfully removed."
        except Exception as e:
            return False, f"Failed to uninstall context menu: {e}"
