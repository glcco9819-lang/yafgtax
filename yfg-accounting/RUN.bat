@echo off
cd /d "%~dp0"
title YFG Accounting Desk

echo =================================================
echo   YFG Accounting Desk v0.3.0.16
echo =================================================
echo.

REM Step 1: Check Python
echo [1/3] Checking Python...
python --version 2>nul
if errorlevel 1 (
    py -3 --version 2>nul
    if errorlevel 1 (
        echo ERROR: Python not found!
        echo Download from: https://www.python.org/downloads/
        echo Make sure to check "Add Python to PATH" during installation.
        pause
        exit /b 1
    )
    set PYTHON=py -3
) else (
    set PYTHON=python
)

REM Step 2: Install dependencies
echo [2/3] Installing dependencies...
"%PYTHON%" -c "import fastapi" 2>nul
if errorlevel 1 (
    echo Installing from local packages...
    "%PYTHON%" -m pip install --no-index --find-links=packages -r requirements.txt 2>nul
    if errorlevel 1 (
        echo Local install failed. Trying online...
        "%PYTHON%" -m pip install --timeout 300 -r requirements.txt
        if errorlevel 1 (
            echo.
            echo ERROR: Could not install dependencies.
            echo Please run manually:
            echo   pip install fastapi uvicorn python-multipart openpyxl cryptography
            pause
            exit /b 1
        )
    )
    echo Dependencies installed.
) else (
    echo Dependencies already installed.
)

REM Step 3: Create data dirs and start
echo [3/3] Starting server...
if not exist "..\data" mkdir "..\data"
if not exist "..\data\files" mkdir "..\data\files"
if not exist "..\data\attachments" mkdir "..\data\attachments"
if not exist "..\data\documents" mkdir "..\data\documents"
if not exist "..\data\backups" mkdir "..\data\backups"

cd app
echo.
echo =================================================
echo   Server is running!
echo.
echo   Open browser: http://localhost:8000
echo   Username:     admin
echo   Password:     admin123
echo.
echo   Press Ctrl+C to stop.
echo =================================================
echo.

"%PYTHON%" -m uvicorn main:app --host 0.0.0.0 --port 8000 --proxy-headers
pause
