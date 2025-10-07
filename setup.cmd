
@echo off
title MediaHub Setup
echo Creating virtual environment...
python -m venv .venv
call .venv\Scripts\activate
echo Installing dependencies...
pip install flask requests
echo Done. Starting server...
python server\app.py
echo.
echo Press any key to exit.
pause >nul
