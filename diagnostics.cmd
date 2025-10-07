
@echo off
title MediaHub Diagnostics
echo Python: 
python --version
echo.
echo Listing important folders...
dir config
dir data
dir web\page
echo.
echo Launching server for smoke...
python server\app.py
echo.
echo Press any key to exit.
pause >nul
