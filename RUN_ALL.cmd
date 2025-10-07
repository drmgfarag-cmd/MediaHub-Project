
@echo off
setlocal enableextensions
title MediaHub — Start Engines + Server
if not exist ".venv\Scripts\activate.bat" ( echo .venv missing. Run FIRST_RUN.cmd first. & pause & exit /b 1 )
call ".venv\Scripts\activate.bat"

rem Optional engines
set ARIA2=bin\aria2c.exe
set QB=bin\qbittorrent.exe

if exist "%ARIA2%" (
  echo Starting aria2 (optional)...
  start "aria2" "%ARIA2%" --enable-rpc=true --rpc-listen-port=6800 --dir=downloads --max-concurrent-downloads=5 --summary-interval=10
) else (
  echo aria2 not found in bin\aria2c.exe (skipping). You can still use remote aria2 via Settings.
)

if exist "%QB%" (
  echo Starting qBittorrent (optional)...
  start "qBittorrent" "%QB%"
) else (
  echo qBittorrent not found in bin\qbittorrent.exe (skipping). You can still use a remote qB WebUI via Settings.
)

echo Launching server...
python server\app.py
echo.
echo Server exited with code %ERRORLEVEL%
pause
