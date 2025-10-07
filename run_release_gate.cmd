
@echo off
title Release Gate
call .venv\Scripts\activate
pip install requests >nul
python tools\release_gate.py
echo.
echo Done. Press any key to close.
pause >nul
