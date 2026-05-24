@echo off
title translatorTdev

echo Starting translatorTdev...
echo.

REM Check Python
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python 3.12+ not found.
    echo Install Python from:
    echo https://python.org
    pause
    exit /b 1
)

REM Create virtual environment if missing
if not exist "venv\" (
    echo Creating virtual environment...
    python -m venv venv
    echo.
)

REM Activate virtual environment
call venv\Scripts\activate

REM Upgrade pip
python -m pip install --upgrade pip -q

REM Install dependencies only once
if not exist "venv\installed.flag" (
    echo Installing dependencies...
    pip install -r requirements.txt

    echo done>venv\installed.flag
)

echo.
echo Launching translatorTdev...
echo.

python main.py

pause