@echo off
echo Creating keys.local.json with provided API keys...
python "%~dp0\set_keys.py"
echo.
echo Done. Press any key to exit.
pause >nul