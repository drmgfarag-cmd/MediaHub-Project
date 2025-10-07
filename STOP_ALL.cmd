
@echo off
title MediaHub — Stop
echo Attempting to stop server and engines...
for /f "tokens=2 delims=," %%a in ('tasklist /FI "IMAGENAME eq python.exe" /FO CSV ^| findstr /I "server\\app.py"') do taskkill /PID %%~a /F >nul 2>&1
taskkill /FI "WINDOWTITLE eq aria2" /F >nul 2>&1
taskkill /FI "WINDOWTITLE eq qBittorrent" /F >nul 2>&1
echo Done.
pause
