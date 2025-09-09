@echo off
echo ================================================================
echo Starting TDRMCD Application...
echo ================================================================
echo.

if not exist "venv\Scripts\activate.bat" (
    echo Error: Virtual environment not found!
    echo Please run setup.bat first
    pause
    exit /b 1
)

echo Activating virtual environment...
call venv\Scripts\activate.bat

echo Starting Flask application...
python run.py

pause
