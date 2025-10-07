
@echo off
docker compose up --build -d
if errorlevel 1 ( echo Failed. Ensure Docker Desktop is running. & pause )
