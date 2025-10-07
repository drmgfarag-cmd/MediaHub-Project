
@echo off
setlocal enableextensions
title MediaHub — Server (Debug)
if not exist ".venv\Scripts\activate.bat" ( echo .venv missing. Run FIRST_RUN.cmd first. & pause & exit /b 1 )
call ".venv\Scripts\activate.bat"
set FLASK_APP=server/app.py
set FLASK_RUN_PORT=5000
set PYTHONFAULTHANDLER=1
set PYTHONWARNINGS=default
echo Starting server (debug) on http://localhost:5000
python -X dev server\app.py
echo.
echo [Debug] Server exited with code %ERRORLEVEL%
echo Press any key to keep this window open and review logs...
pause >nul
cmd /k
