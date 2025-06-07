@echo off
title GitHub PR Auto-Fix Flask Backend

echo.
echo ========================================
echo  GitHub PR Auto-Fix Flask Backend
echo  Windows Startup Script
echo ========================================
echo.

REM Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python is not installed or not in PATH
    echo Please install Python 3.7+ from https://python.org
    pause
    exit /b 1
)

REM Install packages if needed
echo Checking Python packages...
pip install flask flask-cors requests python-dotenv >nul 2>&1

REM Check if app.py exists
if not exist "app.py" (
    echo ERROR: app.py not found in current directory
    echo Please make sure you're running this from the backend folder
    pause
    exit /b 1
)

REM Load environment variables if .env exists
if exist ".env" (
    echo Found .env file - environment variables will be loaded
) else (
    echo No .env file found - using demo configuration
    echo Create .env file from .env.example for GitHub integration
)

echo.
echo Starting Flask server...
echo Server will be available at: http://localhost:5000
echo API health check: http://localhost:5000/api/health
echo.
echo Press Ctrl+C to stop the server
echo.

REM Start the Flask application
python run.py

echo.
echo Server stopped.
pause