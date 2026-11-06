@echo off
echo =================================================
echo   YFG Accounting Desk - Install Dependencies
echo =================================================
echo.

REM Method 1: Install from local packages (offline)
if exist "..\yfg-packages" (
    echo [Method 1] Installing from local packages (offline)...
    pip install --no-index --find-links=..\yfg-packages -r requirements.txt
    if not errorlevel 1 (
        echo.
        echo SUCCESS: All dependencies installed from local packages
        goto :done
    )
    echo FAILED: Local install failed, trying online...
    echo.
)

REM Method 2: Install online with long timeout
echo [Method 2] Installing online (timeout=300s)...
pip install --timeout 300 -r requirements.txt
if errorlevel 1 (
    echo.
    echo FAILED: Online install also failed
    echo.
    echo Alternative solutions:
    echo   1. Use a VPN
    echo   2. Install manually one by one:
    echo      pip install fastapi
    echo      pip install uvicorn
    echo      pip install python-multipart
    echo      pip install openpyxl
    echo      pip install cryptography
    echo   3. Use longer timeout:
    echo      pip install --timeout 600 -r requirements.txt
    echo.
    pause
    exit /b 1
)

:done
echo.
echo SUCCESS: All dependencies installed!
echo.
echo Now run start.bat to launch the application
echo.
pause
