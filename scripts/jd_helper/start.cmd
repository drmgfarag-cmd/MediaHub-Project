@echo off
setlocal
title MediaHub JD Helper (auto-download + headless launch + auto-pair)
echo.
echo Checking Java...
java -version >nul 2>&1
if errorlevel 1 (
  echo Java not found. Attempting to install Temurin 17 JRE via winget...
  winget install -e --id EclipseAdoptium.Temurin.17.JRE -h >nul 2>&1
  if errorlevel 1 (
    echo winget not available or failed. Trying Chocolatey...
    choco -v >nul 2>&1 || (echo Chocolatey not found. Install manually from https://chocolatey.org/install && goto :CONT)
    choco install -y temurin17jre
  )
)
:CONT
set JD_DIR=%~dp0
cd /d "%JD_DIR%"
if not exist JDownloader.jar (
  echo Downloading JDownloader.jar ...
  powershell -NoProfile -ExecutionPolicy Bypass -Command "try { iwr -UseBasicParsing -Uri 'https://installer.jdownloader.org/JDownloader.jar' -OutFile 'JDownloader.jar' } catch { exit 1 }"
  if errorlevel 1 (
    echo Download failed. Please download JDownloader.jar manually and place it here.
    pause
    exit /b 1
  )
)
echo Launching JDownloader headless...
start "JD2 Headless" cmd /c "java -jar JDownloader.jar -norestart -debug > jd2_headless.log 2>&1"
echo Waiting for JD2 to initialize...
timeout /t 10 >nul
echo Attempting auto-pair via myjdapi (requires credentials in config\\myjd.json)...
python "%~dp0\auto_pair.py"
echo Done. Check jd2_headless.log and auto_pair.log for details.
echo.
echo Press any key to exit.
pause >nul
endlocal