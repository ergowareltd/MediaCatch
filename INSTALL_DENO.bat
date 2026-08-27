@echo off
setlocal
cd /d "%~dp0"

echo =============================================
echo   Install Deno - JavaScript runtime for yt-dlp
echo =============================================
echo.

where deno >nul 2>nul
if %errorlevel%==0 (
    echo Deno is already installed:
    deno --version
    echo.
    echo Close and restart MediaCatch to use it.
    pause
    exit /b 0
)

where winget >nul 2>nul
if errorlevel 1 (
    echo ERROR: winget was not found.
    echo Install Deno manually from https://deno.com/
    pause
    exit /b 1
)

echo Installing Deno with WinGet...
winget install --id DenoLand.Deno -e --accept-package-agreements --accept-source-agreements
if errorlevel 1 (
    echo.
    echo Installation failed. Try this command manually in PowerShell:
    echo winget install --id DenoLand.Deno -e
    pause
    exit /b 1
)

echo.
echo Installation completed.
echo IMPORTANT: close and restart MediaCatch so it can detect Deno.
pause
