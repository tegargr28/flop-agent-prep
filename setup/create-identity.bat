@echo off
REM Double-click this file to create (or show) my FLOP Agent identity.
REM It runs setup_identity.py from this same folder.
cd /d "%~dp0"

where py >nul 2>nul
if %errorlevel%==0 (
    py -3 setup_identity.py
    goto done
)
where python >nul 2>nul
if %errorlevel%==0 (
    python setup_identity.py
    goto done
)

echo Python is not installed yet.
echo.
echo 1. The Python download page will open in your browser.
echo 2. Download and install Python.
echo 3. IMPORTANT: tick the box "Add python.exe to PATH" during install.
echo 4. When the install is finished, double-click this file again.
echo.
start https://www.python.org/downloads/

:done
echo.
pause
