"""
PyInstaller build script to compile Icon Changer into a standalone Windows .exe.
Run with: python build_exe.py
"""
import os
import sys
import subprocess
from pathlib import Path

def build() -> None:
    root = Path(__file__).resolve().parent
    entry = root / "run.py"
    
    # Terminate any running IconChanger instances so output exe isn't locked
    try:
        subprocess.run(["taskkill", "/F", "/IM", "IconChanger.exe"], capture_output=True)
    except Exception:
        pass
    
    icon_file = root / "assets" / "app_icon.ico"
    assets_dir = root / "assets"

    cmd = [
        sys.executable,
        "-m", "PyInstaller",
        "--noconsole",
        "--name=IconChanger",
        f"--icon={icon_file}",
        f"--add-data={assets_dir}{os.pathsep}assets",
        "--clean",
        "-y",
        str(entry),
    ]

    print("Building standalone executable with PyInstaller...")
    print("Command:", " ".join(cmd))
    res = subprocess.run(cmd, cwd=str(root))
    if res.returncode == 0:
        dist_exe = root / "dist" / "IconChanger" / "IconChanger.exe"
        print("\n=======================================================")
        print(f" Build succeeded!")
        print(f" Output executable: {dist_exe}")
        print("=======================================================\n")
    else:
        print(f"\nBuild failed with exit code: {res.returncode}")

if __name__ == "__main__":
    build()
