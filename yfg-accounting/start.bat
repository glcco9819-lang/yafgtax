@echo off
echo =================================================
echo   YFG Accounting Desk v0.3.0.16
echo   Starting Server...
echo =================================================
echo.

REM Check Python
echo [1/4] Checking Python...
python --version 2>nul
if errorlevel 1 (
    echo ERROR: Python is not installed
    echo Please install Python 3.9+ from: https://python.org/downloads
    pause
    exit /b 1
)

REM Install dependencies if needed
echo [2/4] Checking dependencies...
python -c "import fastapi" 2>nul
if errorlevel 1 (
    echo Dependencies not found. Running install.bat first...
    call install.bat
    if errorlevel 1 (
        echo ERROR: Failed to install dependencies
        pause
        exit /b 1
    )
)

REM Create data directories
echo [3/4] Creating data directories...
if not exist "..\data\files" mkdir "..\data\files"
if not exist "..\data\attachments" mkdir "..\data\attachments"
if not exist "..\data\documents" mkdir "..\data\documents"
if not exist "..\data\backups" mkdir "..\data\backups"

REM Start server
echo [4/4] Starting server...
echo.
echo =================================================
echo   Server started successfully!
echo.
echo   URL:   http://localhost:8000/static/index.html
echo   User:  admin
echo   Pass:  admin123
echo.
echo   Press Ctrl+C to stop
echo =================================================
echo.

cd app
python -m uvicorn main:app --host 0.0.0.0 --port 8000 --proxy-headers
pause
