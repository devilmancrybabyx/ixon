import os
import sys
import ctypes
from ctypes import wintypes
from pathlib import Path
from typing import Optional, Tuple
import win32com.client
import pythoncom
import win32gui
import win32con

# Windows File Attribute Constants
FILE_ATTRIBUTE_READONLY = 0x01
FILE_ATTRIBUTE_HIDDEN = 0x02
FILE_ATTRIBUTE_SYSTEM = 0x04
FILE_ATTRIBUTE_NORMAL = 0x80

# Shell Change Notification Constants
SHCNE_ATTRIBUTES = 0x00000800
SHCNE_UPDATEDIR = 0x00001000
SHCNE_UPDATEITEM = 0x00002000
SHCNE_ASSOCCHANGED = 0x08000000
SHCNF_IDLIST = 0x0000
SHCNF_PATHW = 0x0005
SHCNF_FLUSH = 0x1000  # Synchronous shell delivery flag

# ShellExecuteEx structure for waiting on elevated child process
class SHELLEXECUTEINFOW(ctypes.Structure):
    _fields_ = [
        ("cbSize", wintypes.DWORD),
        ("fMask", wintypes.ULONG),
        ("hwnd", wintypes.HWND),
        ("lpVerb", wintypes.LPCWSTR),
        ("lpFile", wintypes.LPCWSTR),
        ("lpParameters", wintypes.LPCWSTR),
        ("lpDirectory", wintypes.LPCWSTR),
        ("nShow", ctypes.c_int),
        ("hInstApp", wintypes.HINSTANCE),
        ("lpIDList", wintypes.LPVOID),
        ("lpClass", wintypes.LPCWSTR),
        ("hkeyClass", wintypes.HKEY),
        ("dwHotKey", wintypes.DWORD),
        ("hIconOrMonitor", wintypes.HANDLE),
        ("hProcess", wintypes.HANDLE),
    ]

# Windows Shell Folder Custom Settings structure
class SHFOLDERCUSTOMSETTINGS(ctypes.Structure):
    _fields_ = [
        ("dwSize", wintypes.DWORD),
        ("dwMask", wintypes.DWORD),
        ("pvid", ctypes.c_void_p),
        ("pszWebViewTemplate", wintypes.LPWSTR),
        ("cchWebViewTemplate", wintypes.DWORD),
        ("pszWebViewTemplateVersion", wintypes.LPWSTR),
        ("pszInfoTip", wintypes.LPWSTR),
        ("cchInfoTip", wintypes.DWORD),
        ("pclsid", ctypes.c_void_p),
        ("dwFlags", wintypes.DWORD),
        ("pszIconFile", wintypes.LPWSTR),
        ("cchIconFile", wintypes.DWORD),
        ("iIconIndex", ctypes.c_int),
        ("pszLogo", wintypes.LPWSTR),
        ("cchLogo", wintypes.DWORD),
    ]

FCSM_ICONFILE = 0x00000010
FCS_FORCEWRITE = 0x00000002


class IconApplicator:
    """Applies and resets custom icons for Windows folders, shortcuts, and files with instant refresh."""

    @staticmethod
    def refresh_explorer_windows() -> None:
        """
        Sends WM_COMMAND (41504 / View Refresh) to all open File Explorer windows
        and the Windows Desktop, forcing them to immediately re-render items.
        """
        try:
            def _enum_callback(hwnd, _):
                try:
                    cname = win32gui.GetClassName(hwnd)
                    if cname in ("CabinetWClass", "ExploreWClass", "Progman", "WorkerW"):
                        win32gui.PostMessage(hwnd, win32con.WM_COMMAND, 41504, 0)
                except Exception:
                    pass

            win32gui.EnumWindows(_enum_callback, None)
        except Exception as e:
            print(f"Error refreshing explorer windows: {e}")

    @classmethod
    def notify_shell(cls, target_path: Optional[str] = None) -> None:
        """
        Forces Windows Explorer to flush its icon cache and refresh immediately
        across all open windows and the desktop.
        """
        try:
            flush_flag = SHCNF_PATHW | SHCNF_FLUSH

            if target_path and os.path.exists(target_path):
                p = Path(target_path).resolve()
                p_str = str(p)

                # Notify item change
                ctypes.windll.shell32.SHChangeNotify(SHCNE_UPDATEITEM, flush_flag, p_str, None)

                # Notify directory and parent directory if applicable
                if p.is_dir():
                    ctypes.windll.shell32.SHChangeNotify(SHCNE_UPDATEDIR, flush_flag, p_str, None)
                    if p.parent and p.parent.exists():
                        ctypes.windll.shell32.SHChangeNotify(SHCNE_UPDATEDIR, flush_flag, str(p.parent), None)

                # Notify attribute change
                ctypes.windll.shell32.SHChangeNotify(SHCNE_ATTRIBUTES, flush_flag, p_str, None)

            # Invalidate global icon associations synchronously
            ctypes.windll.shell32.SHChangeNotify(SHCNE_ASSOCCHANGED, SHCNF_IDLIST | SHCNF_FLUSH, None, None)

            # Broadcast setting change
            try:
                ctypes.windll.user32.SendMessageTimeoutW(0xFFFF, 0x001A, 0, "Environment", 2, 250, None)
            except Exception:
                pass

            # Force immediate redraw on all open Explorer windows and Desktop
            cls.refresh_explorer_windows()

        except Exception as e:
            print(f"Shell notification error: {e}")

    @classmethod
    def apply_with_elevation(cls, target_path: str, ico_path: str) -> bool:
        """
        Runs the elevated apply command synchronously via Windows UAC prompt.
        Waits for the elevated process to finish and verifies exit code before returning.
        """
        try:
            if getattr(sys, "frozen", False):
                exe = sys.executable
                args = f'--elevated-apply "{target_path}" "{ico_path}"'
            else:
                exe = sys.executable
                main_script = Path(__file__).resolve().parent.parent / "main.py"
                args = f'"{main_script}" --elevated-apply "{target_path}" "{ico_path}"'

            sei = SHELLEXECUTEINFOW()
            sei.cbSize = ctypes.sizeof(SHELLEXECUTEINFOW)
            sei.fMask = 0x00000040  # SEE_MASK_NOCLOSEPROCESS
            sei.hwnd = None
            sei.lpVerb = "runas"
            sei.lpFile = exe
            sei.lpParameters = args
            sei.lpDirectory = None
            sei.nShow = 1  # SW_SHOWNORMAL

            res = ctypes.windll.shell32.ShellExecuteExW(ctypes.byref(sei))
            if not res or not sei.hProcess:
                return False

            # Wait synchronously for up to 30 seconds for UAC approval and execution
            wait_res = ctypes.windll.kernel32.WaitForSingleObject(sei.hProcess, 30000)
            exit_code = wintypes.DWORD()
            ctypes.windll.kernel32.GetExitCodeProcess(sei.hProcess, ctypes.byref(exit_code))
            ctypes.windll.kernel32.CloseHandle(sei.hProcess)

            return (wait_res == 0) and (exit_code.value == 0)

        except Exception as e:
            print(f"Elevation error: {e}")
            return False

    @classmethod
    def apply_to_folder(cls, folder_path: str, ico_path: str) -> bool:
        """
        Sets custom icon for a Windows directory using the official Windows Shell API
        and desktop.ini specification, ensuring immediate Explorer refresh.
        """
        folder = Path(folder_path).resolve()
        if not folder.is_dir():
            raise ValueError(f"Path is not a valid directory: {folder_path}")

        ico = Path(ico_path).resolve()
        if not ico.exists():
            raise FileNotFoundError(f"Icon file not found: {ico_path}")

        desktop_ini = folder / "desktop.ini"

        # If standard write access is not present, use elevation immediately
        if not os.access(folder, os.W_OK):
            if cls.apply_with_elevation(str(folder), str(ico)):
                cls.notify_shell(str(folder))
                return True
            raise PermissionError(f"Administrative permission required to customize folder: {folder}")

        try:
            # Step 1: Use official Windows Shell API SHGetSetFolderCustomSettingsW
            fcs = SHFOLDERCUSTOMSETTINGS()
            fcs.dwSize = ctypes.sizeof(SHFOLDERCUSTOMSETTINGS)
            fcs.dwMask = FCSM_ICONFILE
            fcs.pszIconFile = str(ico)
            fcs.cchIconFile = 0
            fcs.iIconIndex = 0

            hr = ctypes.windll.shell32.SHGetSetFolderCustomSettings(
                ctypes.byref(fcs),
                str(folder),
                FCS_FORCEWRITE
            )

            # Step 2: Ensure desktop.ini has full compatibility keys
            # If desktop.ini exists, clear attributes temporarily to write UTF-16LE content
            if desktop_ini.exists():
                ctypes.windll.kernel32.SetFileAttributesW(str(desktop_ini), FILE_ATTRIBUTE_NORMAL)

            ini_content = (
                "[.ShellClassInfo]\r\n"
                f"IconResource={str(ico)},0\r\n"
                f"IconFile={str(ico)}\r\n"
                "IconIndex=0\r\n"
                "[ViewState]\r\n"
                "Mode=\r\n"
                "Vid=\r\n"
                "FolderType=Generic\r\n"
            )
            raw_ini = ("\ufeff" + ini_content).encode("utf-16le")
            with open(desktop_ini, "wb") as f:
                f.write(raw_ini)

            # Set desktop.ini to HIDDEN | SYSTEM
            ctypes.windll.kernel32.SetFileAttributesW(str(desktop_ini), FILE_ATTRIBUTE_HIDDEN | FILE_ATTRIBUTE_SYSTEM)

            # Ensure folder is marked as system folder / READONLY
            try:
                ctypes.windll.shlwapi.PathMakeSystemFolderW(str(folder))
            except Exception:
                pass

            folder_attrs = ctypes.windll.kernel32.GetFileAttributesW(str(folder))
            if folder_attrs != -1:
                # Toggle readonly to trigger Explorer directory change event
                ctypes.windll.kernel32.SetFileAttributesW(str(folder), folder_attrs & ~FILE_ATTRIBUTE_READONLY)
                ctypes.windll.kernel32.SetFileAttributesW(str(folder), folder_attrs | FILE_ATTRIBUTE_READONLY)
            else:
                ctypes.windll.kernel32.SetFileAttributesW(str(folder), FILE_ATTRIBUTE_READONLY)

            # Touch timestamp
            try:
                os.utime(str(folder), None)
            except Exception:
                pass

        except (PermissionError, OSError) as e:
            # Fall back to synchronous elevation if access was denied
            if cls.apply_with_elevation(str(folder), str(ico)):
                cls.notify_shell(str(folder))
                return True
            raise

        cls.notify_shell(str(folder))
        return True

    @classmethod
    def restore_folder_icon(cls, folder_path: str) -> bool:
        """Restores default Windows folder icon by removing desktop.ini and unsetting system attributes."""
        folder = Path(folder_path).resolve()
        desktop_ini = folder / "desktop.ini"

        if not os.access(folder, os.W_OK):
            # Try elevation for restore
            cls.apply_with_elevation(str(folder), "")
            cls.notify_shell(str(folder))
            return True

        if desktop_ini.exists():
            ctypes.windll.kernel32.SetFileAttributesW(str(desktop_ini), FILE_ATTRIBUTE_NORMAL)
            try:
                desktop_ini.unlink()
            except Exception as e:
                print(f"Failed to remove desktop.ini: {e}")

        try:
            ctypes.windll.shlwapi.PathUnmakeSystemFolderW(str(folder))
        except Exception:
            pass

        folder_attrs = ctypes.windll.kernel32.GetFileAttributesW(str(folder))
        if folder_attrs != -1:
            ctypes.windll.kernel32.SetFileAttributesW(str(folder), folder_attrs & ~FILE_ATTRIBUTE_READONLY)

        try:
            os.utime(str(folder), None)
        except Exception:
            pass

        cls.notify_shell(str(folder))
        return True

    @classmethod
    def apply_to_shortcut(cls, lnk_path: str, ico_path: str) -> bool:
        """
        Sets custom icon for a .lnk shortcut using Windows Script Host COM.
        Automatically elevates via UAC if target is in a protected path (e.g., C:\\Users\\Public\\Desktop).
        """
        lnk = Path(lnk_path).resolve()
        if not str(lnk).lower().endswith(".lnk"):
            raise ValueError(f"Path is not a .lnk shortcut: {lnk_path}")

        ico = Path(ico_path).resolve()
        if not ico.exists():
            raise FileNotFoundError(f"Icon file not found: {ico_path}")

        pythoncom.CoInitialize()
        try:
            shell = win32com.client.Dispatch("WScript.Shell")
            shortcut = shell.CreateShortcut(str(lnk))
            shortcut.IconLocation = f"{str(ico)},0"
            shortcut.Save()
        except Exception as e:
            err_str = str(e)
            if "-2147024891" in err_str or "Access is denied" in err_str or not os.access(lnk, os.W_OK):
                if cls.apply_with_elevation(str(lnk), str(ico)):
                    cls.notify_shell(str(lnk))
                    return True
            raise
        finally:
            try:
                pythoncom.CoUninitialize()
            except Exception:
                pass

        cls.notify_shell(str(lnk))
        return True

    @classmethod
    def restore_shortcut_icon(cls, lnk_path: str) -> bool:
        """Restores default icon for shortcut by resetting IconLocation."""
        lnk = Path(lnk_path).resolve()
        if not str(lnk).lower().endswith(".lnk"):
            raise ValueError(f"Path is not a .lnk shortcut: {lnk_path}")

        pythoncom.CoInitialize()
        try:
            shell = win32com.client.Dispatch("WScript.Shell")
            shortcut = shell.CreateShortcut(str(lnk))
            target = shortcut.TargetPath
            shortcut.IconLocation = f"{target},0" if target else ",0"
            shortcut.Save()
        except Exception as e:
            err_str = str(e)
            if "-2147024891" in err_str or "Access is denied" in err_str or not os.access(lnk, os.W_OK):
                if cls.apply_with_elevation(str(lnk), ""):
                    cls.notify_shell(str(lnk))
                    return True
            raise
        finally:
            try:
                pythoncom.CoUninitialize()
            except Exception:
                pass

        cls.notify_shell(str(lnk))
        return True

    @classmethod
    def create_shortcut_for_file(
        cls,
        file_path: str,
        ico_path: str,
        destination_dir: Optional[str] = None
    ) -> str:
        """
        Creates a custom-icon shortcut for an arbitrary file.
        Returns the path to the created shortcut.
        """
        src = Path(file_path).resolve()
        if not src.exists():
            raise FileNotFoundError(f"File not found: {file_path}")

        dest_folder = Path(destination_dir) if destination_dir else src.parent
        dest_folder.mkdir(parents=True, exist_ok=True)

        shortcut_name = f"{src.stem}.lnk"
        lnk_path = dest_folder / shortcut_name

        pythoncom.CoInitialize()
        try:
            shell = win32com.client.Dispatch("WScript.Shell")
            shortcut = shell.CreateShortcut(str(lnk_path))
            shortcut.TargetPath = str(src)
            shortcut.WorkingDirectory = str(src.parent)
            shortcut.IconLocation = f"{str(ico_path)},0"
            shortcut.Save()
        finally:
            try:
                pythoncom.CoUninitialize()
            except Exception:
                pass

        cls.notify_shell(str(lnk_path))
        return str(lnk_path)

    @classmethod
    def apply_icon(cls, target_path: str, ico_path: str) -> Tuple[bool, str]:
        """
        Detects target type and applies icon appropriately.
        Returns (success: bool, message: str).
        """
        target = Path(target_path).resolve()
        if not target.exists():
            return False, f"Target path does not exist: {target_path}"

        if target.is_dir():
            cls.apply_to_folder(str(target), str(ico_path))
            return True, f"Successfully customized folder icon for: {target.name}"
        elif target.suffix.lower() == ".lnk":
            cls.apply_to_shortcut(str(target), str(ico_path))
            return True, f"Successfully customized shortcut icon for: {target.name}"
        else:
            # File: create or update shortcut
            lnk = cls.create_shortcut_for_file(str(target), str(ico_path))
            return True, f"Created customized shortcut: {Path(lnk).name}"
