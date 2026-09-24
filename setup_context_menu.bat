@echo off
title Install Icon Changer Context Menu
echo ===================================================
echo   Installing "Change Icon" to Windows Context Menu
echo ===================================================
echo.

python "%~dp0run.py" --install

if %ERRORLEVEL% EQU 0 (
    echo.
    echo [SUCCESS] "Change Icon" has been added to your right-click context menu!
    echo You can now right-click any Folder, File, or Shortcut to change its icon.
) else (
    echo.
    echo [ERROR] Installation encountered an issue.
)

echo.
pause
