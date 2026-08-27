@echo off
setlocal
cd /d "%~dp0"

echo =============================================
echo   MediaCatch - yt-dlp + Authenticated Browser
echo =============================================

where py >nul 2>nul
if %errorlevel%==0 (
    set "PY=py"
) else (
    where python >nul 2>nul
    if errorlevel 1 (
        echo.
        echo ERROR: Python was not found.
        echo Install Python 3.11 or newer and try again.
        pause
        exit /b 1
    )
    set "PY=python"
)

if not exist ".venv\Scripts\python.exe" (
    echo Creating virtual environment...
    %PY% -m venv .venv
    if errorlevel 1 goto :error
)

echo Updating pip and installing requirements...
".venv\Scripts\python.exe" -m pip install --upgrade pip
".venv\Scripts\python.exe" -m pip install -r requirements.txt
if errorlevel 1 goto :error

echo.
echo Starting MediaCatch...
".venv\Scripts\python.exe" -m streamlit run app.py
exit /b 0

:error
echo.
echo An error occurred during installation or startup.
pause
exit /b 1
