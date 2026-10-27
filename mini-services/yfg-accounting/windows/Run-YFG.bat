@echo off
setlocal
cd /d "%~dp0.."
set "YFG_DATA_DIR=%LOCALAPPDATA%\YFG\AccountingDesk"
if not exist "%YFG_DATA_DIR%\files" mkdir "%YFG_DATA_DIR%\files"
if not exist ".venv\Scripts\python.exe" (
  echo First run: preparing YFG Accounting Desk...
  py -3.12 -m venv .venv 2>nul || py -3.11 -m venv .venv 2>nul || py -3 -m venv .venv
  if errorlevel 1 (
    echo Python 3.11 or newer is required. Install it from python.org and retry.
    pause
    exit /b 1
  )
  .venv\Scripts\python.exe -m pip install --upgrade pip
  .venv\Scripts\python.exe -m pip install -r requirements.txt
  if errorlevel 1 (
    echo Dependency installation failed. Check your network connection and retry.
    pause
    exit /b 1
  )
)
start "" /min cmd /c "timeout /t 2 /nobreak >nul ^& start http://127.0.0.1:8090"
.venv\Scripts\python.exe -m uvicorn app.main:app --host 127.0.0.1 --port 8090
pause
