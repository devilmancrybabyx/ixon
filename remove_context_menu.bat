@echo off
title Remove Icon Changer Context Menu
echo =====================================================
echo   Removing "Change Icon" from Windows Context Menu
echo =====================================================
echo.

python "%~dp0run.py" --uninstall

if %ERRORLEVEL% EQU 0 (
    echo.
    echo [SUCCESS] "Change Icon" has been removed from your context menu.
) else (
    echo.
    echo [ERROR] Removal encountered an issue.
)

echo.
pause
