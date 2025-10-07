
@echo off
title 5x Smoke
call .venv\Scripts\activate
pip install requests >nul
python tools\smoke5.py
echo.
echo Done. Press any key to close.
pause >nul
