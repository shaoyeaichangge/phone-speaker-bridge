@echo off
setlocal
cd /d "%~dp0"
title Phone Speaker Bridge
echo ============================================
echo   Phone Speaker Bridge - WiFi Audio
echo ============================================
if not exist ".venv\Scripts\python.exe" (
    echo Creating a Python environment...
    python -m venv .venv
    if errorlevel 1 goto :setup_failed
)
if not exist ".venv\.bridge-ready" (
    ".venv\Scripts\python.exe" -m pip install -r requirements.txt
    if errorlevel 1 goto :setup_failed
    type nul > ".venv\.bridge-ready"
)
echo Open the printed LAN URL on your phone and tap START.
echo Keep the page in the foreground. Press Ctrl+C to stop.
".venv\Scripts\python.exe" server.py %*
set "BRIDGE_EXIT=%ERRORLEVEL%"
echo.
echo Server exited with code %BRIDGE_EXIT%.
pause
exit /b %BRIDGE_EXIT%

:setup_failed
echo Setup failed. Install Python 3.12 and review the error above.
pause
exit /b 1
