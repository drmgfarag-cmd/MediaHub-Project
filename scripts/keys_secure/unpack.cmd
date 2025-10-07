@echo off
setlocal
if "%~1"=="" (
  echo Usage: unpack.cmd <path-to-secure-7z>
  pause >nul
  exit /b 1
)
set SRC=%~1
set DST=%~dp0..\..\config
where 7z >nul 2>&1 || (echo 7z not found in PATH. Please install 7-Zip and add to PATH. & pause >nul & exit /b 1)
echo Enter password to decrypt:
set /p PWD=Password: 
7z x -p%PWD% -o"%DST%" "%SRC%" -y
if errorlevel 1 ( echo Failed. & pause >nul & exit /b 1 )
echo Extracted to %DST%
pause >nul
endlocal