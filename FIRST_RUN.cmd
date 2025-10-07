
@echo off
cd /d "%~dp0"
echo MediaHub first-run checklist...
if not exist storage mkdir storage
if not exist storage\logs mkdir storage\logs
echo Checking dependencies...
echo - 7-Zip: see Tools -> Dependencies to locate or install placeholder
echo - FFmpeg: see Tools -> Dependencies to locate or install placeholder
echo Done. Use RUN_SERVER.cmd to start.
pause
