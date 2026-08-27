@echo off
setlocal

echo =============================================
echo   Install FFmpeg with WinGet
echo =============================================

where winget >nul 2>nul
if errorlevel 1 (
    echo.
    echo winget is not available on this PC.
    echo Install FFmpeg manually and add it to PATH.
    echo Recommended builds: https://github.com/yt-dlp/FFmpeg-Builds
    pause
    exit /b 1
)

winget install --id Gyan.FFmpeg -e --accept-package-agreements --accept-source-agreements

echo.
echo If installation succeeded, close and restart MediaCatch.
pause
