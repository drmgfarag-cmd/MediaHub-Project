
@echo off
title Self-Audit
call .venv\Scripts\activate
pip install requests >nul
python tools\self_audit.py
echo.
echo Done. Press any key to close.
pause >nul
