@echo off
REM SurfaceMap Studio - Launcher for Windows

cd /d "%~dp0"

IF NOT EXIST "venv" (
    echo Creating Python virtual environment...
    python -m venv venv
    call venv\Scripts\activate.bat
    echo Installing dependencies...
    pip install -r requirements.txt
) ELSE (
    call venv\Scripts\activate.bat
)

python main.py %*
pause
