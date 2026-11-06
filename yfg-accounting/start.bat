@echo off
chcp 65001 >nul
echo =================================================
echo   YFG Accounting Desk v0.3.0.16
echo   راه‌اندازی سامانه
echo =================================================

echo.
echo [1/5] بررسی Python...
python --version 2>nul
if errorlevel 1 (
    echo ✗ Python نصب نیست. ابتدا Python 3.9+ نصب کنید:
    echo   https://python.org/downloads
    pause
    exit /b 1
)

echo.
echo [2/5] نصب وابستگی‌ها...
python -m pip install --upgrade pip -q
python -m pip install -r requirements.txt -q
if errorlevel 1 (
    echo ✗ نصب وابستگی‌ها ناموفق بود
    pause
    exit /b 1
)

echo.
echo [3/5] ساخت پوشه داده...
mkdir data\files 2>nul
mkdir data\attachments 2>nul
mkdir data\documents 2>nul
mkdir data\backups 2>nul

echo.
echo [4/5] راه‌اندازی دیتابیس...
cd app
python -c "import sys; sys.path.insert(0,'.'); from main import init_db; init_db(); print('OK')"

echo.
echo [5/5] اجرای سرور...
echo.
echo =================================================
echo   ✓ سامانه راه‌اندازی شد!
echo.
echo   آدرس: http://localhost:8000/static/index.html
echo   کاربر: admin
echo   رمز:   admin123
echo.
echo   برای توقف: Ctrl+C
echo =================================================
echo.

python -m uvicorn main:app --host 0.0.0.0 --port 8000 --proxy-headers
pause
