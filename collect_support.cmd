
@echo off
title Support Pack
call .venv\Scripts\activate
curl -X POST http://localhost:8000/api/support/collect -o NUL
echo If the Support Pack URL was shown in the server log, open it in your browser.
echo.
echo Done. Press any key to close.
pause >nul
