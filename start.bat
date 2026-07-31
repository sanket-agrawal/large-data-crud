@echo off
chcp 65001 >nul
title Universal Data Search and Management Engine (DuckDB)
color 0A

echo ================================================================
echo   Starting Universal Data Search and Management Engine
echo   Supports 700,000+ Records across Multi-Sheet Excel Files
echo ================================================================
echo.

:: Check Python installation
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python is not installed or not added to PATH.
    echo Please install Python 3.10+ from https://www.python.org/
    pause
    exit /b 1
)

echo Checking backend dependencies...
python -m pip install -r backend\requirements.txt --quiet --disable-pip-version-check

:: Check if frontend dist exists, otherwise build it if node exists
if not exist "frontend\dist" (
    echo Building frontend dashboard...
    where node >nul 2>&1
    if not errorlevel 1 (
        cd frontend
        call npm install --quiet
        call npm run build
        cd ..
    ) else (
        echo Node.js not detected. Starting backend API on port 8000.
    )
)

echo.
echo ================================================================
echo   Server is starting! Opening http://localhost:8000 in browser...
echo   Keep this window open while using the application.
echo   Press Ctrl+C to stop the application server.
echo ================================================================
echo.

:: Schedule browser auto-open after 2 seconds to ensure Python server is ready
start /b cmd /c "ping -n 3 127.0.0.1 >nul && start http://localhost:8000" >nul 2>&1

python backend\main.py

pause
