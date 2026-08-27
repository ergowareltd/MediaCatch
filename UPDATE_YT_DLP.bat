@echo off
setlocal
cd /d "%~dp0"

if exist "yt-dlp.exe" (
    echo Updating local yt-dlp.exe...
    yt-dlp.exe -U
    goto :done
)

if exist ".venv\Scripts\python.exe" (
    echo Updating yt-dlp in the Python environment...
    ".venv\Scripts\python.exe" -m pip install -U "yt-dlp[default]"
    goto :done
)

echo The local environment has not been created yet.
echo Run START_APP.bat first.
goto :end

:done
echo.
echo Update completed.

:end
pause
