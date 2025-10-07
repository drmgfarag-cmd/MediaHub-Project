@echo off
title MediaHub Reverse Proxy (Caddy) - HTTPS :8443 -> 127.0.0.1:5000
echo Checking for Caddy...
where caddy >nul 2>&1
if %errorlevel% neq 0 (
  echo Caddy not found. Attempting install via winget (requires Windows 10+).
  winget install -e --id CaddyServer.Caddy
)
where caddy >nul 2>&1
if %errorlevel% neq 0 (
  echo Still no caddy in PATH. Place caddy.exe into scripts\caddy\ or install manually.
  if exist "%~dp0caddy\caddy.exe" (
    set CADDY_BIN="%~dp0caddy\caddy.exe"
  ) else (
    echo Press any key to exit.
    pause >nul
    exit /b 1
  )
) else (
  for /f "usebackq tokens=*" %%i in (`where caddy`) do set CADDY_BIN="%%i"
)
echo Using %CADDY_BIN%
echo Starting Caddy reverse proxy with internal TLS on https://localhost:8443
%CADDY_BIN% run --config "%~dp0caddy\Caddyfile"
echo Caddy exited. Press any key to close...
pause >nul