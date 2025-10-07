@echo off
echo Checking for 7-Zip and helpers...
where 7z >nul 2>nul || echo 7-Zip not found. Please install or place 7z.exe in PATH.
pause

echo Installing optional Python deps for casting/HLS... && python -m pip install --upgrade pip && pip install websocket-client requests ffmpeg-python

echo (Optional) Install Caddy via winget for HTTPS reverse proxy... && (winget install -e --id CaddyServer.Caddy || echo Skipping)

echo Installing IMDb/Smart Collections deps... && pip install requests beautifulsoup4 myjdapi
