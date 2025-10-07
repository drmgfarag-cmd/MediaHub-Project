
@echo off
setlocal enableextensions
title Get 7-Zip (Windows, portable)
set URLZ= https://www.7-zip.org/a/7zr.exe
set URLA= https://www.7-zip.org/a/7z2301-extra.7z
mkdir bin 2>nul
echo Downloading 7zr bootstrap...
powershell -Command "Invoke-WebRequest -Uri https://www.7-zip.org/a/7zr.exe -OutFile bin\7zr.exe"
if errorlevel 1 ( echo Download failed & pause & exit /b 1 )
echo Downloading 7-Zip extra...
powershell -Command "Invoke-WebRequest -Uri https://www.7-zip.org/a/7z2301-extra.7z -OutFile bin\7z-extra.7z"
echo Extracting 7-Zip...
bin\7zr.exe x -y bin\7z-extra.7z -obin >nul
copy /Y bin\7z.exe bin\7z.exe >nul
copy /Y bin\7za.exe bin\7za.exe >nul
copy /Y bin\7zz.exe bin\7zz.exe >nul
del /Q bin\7zr.exe bin\7z-extra.7z
echo Done. 7z binaries are in bin\
pause
