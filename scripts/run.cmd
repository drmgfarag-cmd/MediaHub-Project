@echo off
REM run.cmd - Windows run script for MediaHub Enhanced Final

echo Starting MediaHub Enhanced Final...

REM Activate virtual environment if it exists
if exist .venv\Scripts\activate.bat (
    call .venv\Scripts\activate.bat
)

python app.py --host 0.0.0.0 --port 5000

