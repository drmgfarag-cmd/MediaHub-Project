@echo off
setlocal
set OUT=%~dp0..\..\data\backups
if not exist "%OUT%" mkdir "%OUT%"
if not exist "%~dp0..\..\config\keys.local.json" (
  echo config\keys.local.json not found
  pause >nul
  exit /b 1
)
set TS=%DATE:~10,4%%DATE:~4,2%%DATE:~7,2%_%TIME:~0,2%%TIME:~3,2%%TIME:~6,2%
set TS=%TS: =0%
set ZIP=%OUT%\MediaHub_KEYS_SECURE_%TS%.7z
echo Creating encrypted archive using 7-Zip...
where 7z >nul 2>&1 || (echo 7z not found in PATH. Please install 7-Zip and add to PATH. & pause >nul & exit /b 1)
echo Enter password for the encrypted archive:
set /p PWD=Password: 
7z a -p%PWD% -mhe=on "%ZIP%" "%~dp0..\..\config\keys.local.json"
if errorlevel 1 ( echo Failed. & pause >nul & exit /b 1 )
echo Done: %ZIP%
pause >nul
endlocal