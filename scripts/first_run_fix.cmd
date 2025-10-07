@echo off
title MediaHub First-Run Fix (keys, deps, JD helper, profiles)
echo == Keys check ==
python "%~dp0first_run_fix.py" --check-keys
echo.
echo == Install optional dependencies (requests, bs4, myjdapi, qrcode) ==
call "%~dp0fetch_deps.cmd"
echo.
echo == Apply default profiles and feature flags ==
python "%~dp0first_run_fix.py" --apply-profiles --apply-flags
echo.
echo == (Optional) Launch JD helper for DLC ==
if exist "%~dp0jd_helper\start.cmd" (
  echo Starting JD helper in background ...
  start "" "%~dp0jd_helper\start.cmd"
) else (
  echo JD helper script not found (unexpected)
)
echo.
echo == Run self-tests and rules audit ==
python "%~dp0first_run_fix.py" --self-tests
echo All done. Press any key to exit.
pause >nul