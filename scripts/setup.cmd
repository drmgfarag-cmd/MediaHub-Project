@echo off
REM setup.cmd - Windows setup script for MediaHub Enhanced Final

echo Setting up MediaHub Enhanced Final...

REM Check for Python
where python >nul 2>&1
if %errorlevel% neq 0 (
    echo Python not found. Please install Python 3.9+ and add it to your PATH.
    goto :eof
)

REM Install pip dependencies
echo Installing Python dependencies...
pip install -r requirements.txt
if %errorlevel% neq 0 (
    echo Failed to install Python dependencies.
    goto :eof
)

echo Setup complete. You can now run the application using run.cmd

