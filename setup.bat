@echo off
echo ================================================================
echo TDRMCD - Tribal Districts Resource Management Setup
echo ================================================================
echo.

echo Checking Python installation...
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo Error: Python is not installed or not in PATH
    echo Please install Python 3.8+ from https://python.org
    pause
    exit /b 1
)

echo Creating virtual environment...
if not exist "venv" (
    python -m venv venv
    echo Virtual environment created successfully
) else (
    echo Virtual environment already exists
)

echo.
echo Activating virtual environment and installing dependencies...
call venv\Scripts\activate.bat

echo Installing required packages...
pip install --upgrade pip
pip install -r requirements.txt

echo.
echo Creating environment file...
if not exist ".env" (
    echo SECRET_KEY=dev-secret-key-change-in-production > .env
    echo FLASK_ENV=development >> .env
    echo FLASK_DEBUG=True >> .env
    echo DATABASE_URL=sqlite:///tdrmcd.db >> .env
    echo Environment file created
) else (
    echo Environment file already exists
)

echo.
echo ================================================================
echo Setup completed successfully!
echo ================================================================
echo.
echo To start the application:
echo 1. Run: venv\Scripts\activate.bat
echo 2. Run: python run.py
echo.
echo Or simply run: start_app.bat
echo.
echo Default admin credentials:
echo Username: admin
echo Password: admin123
echo.
echo Application will be available at: http://127.0.0.1:5000
echo ================================================================
pause
