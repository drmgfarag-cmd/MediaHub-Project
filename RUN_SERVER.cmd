
@echo off
setlocal ENABLEDELAYEDEXPANSION
title MediaHub — Server (Flask)
cd /d "%~dp0"
echo Launching MediaHub (log: storage\logs\app.log) ...
if not exist storage\logs mkdir storage\logs
set PY_CMD=python
where %PY_CMD% >nul 2>nul || set PY_CMD=py
%PY_CMD% -u -c "import sys,os;from pathlib import Path;Path('storage/logs').mkdir(parents=True,exist_ok=True);open('storage/logs/app.log','a',encoding='utf-8').write('--- RUN %s ---\n'%__import__('time').ctime());" 
%PY_CMD% -u server/app.py
echo.
echo Server exited. Press any key to close.
pause >nul
