
@echo off
setlocal enableextensions
title Get FFmpeg (Windows)
set URL=https://www.gyan.dev/ffmpeg/builds/ffmpeg-release-essentials.zip
set OUT=bin\ffmpeg-win.zip
mkdir bin 2>nul
echo Downloading FFmpeg...
powershell -Command "Invoke-WebRequest -Uri %URL% -OutFile %OUT%"
if errorlevel 1 ( echo Download failed & pause & exit /b 1 )
echo Extracting...
powershell -Command "Add-Type -AssemblyName System.IO.Compression.FileSystem; [IO.Compression.ZipFile]::ExtractToDirectory('%OUT%','bin\ffmpeg_tmp')"
for /f "delims=" %%a in ('dir /b /ad bin\ffmpeg_tmp') do set D=bin\ffmpeg_tmp\%%a
copy /Y "%D%\bin\ffmpeg.exe" bin\ffmpeg.exe >nul
copy /Y "%D%\bin\ffprobe.exe" bin\ffprobe.exe >nul
rmdir /S /Q bin\ffmpeg_tmp
del /Q %OUT%
echo Done. ffmpeg.exe is in bin\
pause
