@echo off
REM Facely Environment Setup Script for Windows

echo ==================================
echo Facely Environment Setup
echo ==================================
echo.

REM Check Python version
echo Checking Python version...
python --version
echo.

REM Create virtual environment if it doesn't exist
if not exist ".venv" (
    echo Creating virtual environment...
    python -m venv .venv
    echo [OK] Virtual environment created
) else (
    echo [OK] Virtual environment already exists
)
echo.

REM Activate virtual environment
echo Activating virtual environment...
call .venv\Scripts\activate.bat

REM Upgrade pip
echo.
echo Upgrading pip...
python -m pip install --upgrade pip

REM Install dependencies
echo.
echo Installing dependencies...
pip install -r requirements.txt

REM Download models
echo.
echo Downloading models...
python scripts\download_models.py

REM Create necessary directories
echo.
echo Creating directories...
if not exist "data" mkdir data
if not exist "logs" mkdir logs
echo [OK] Directories created

REM Initialize database
echo.
echo Initializing database...
python scripts\init_db.py

echo.
echo ==================================
echo Setup Complete!
echo ==================================
echo.
echo To run Facely:
echo   1. Activate the virtual environment:
echo      .venv\Scripts\activate.bat
echo   2. Run the application:
echo      python main.py
echo.
echo See QUICKSTART.md for more information.
echo.
pause