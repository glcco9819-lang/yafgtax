@echo off
chcp 65001 >nul
echo =================================================
echo   YFG Accounting Desk - نصب وابستگی‌ها
echo =================================================
echo.

REM روش ۱: نصب از پوشه محلی (آفلاین)
if exist "..\yfg-packages" (
    echo [روش ۱] نصب از پوشه محلی (آفلاین)...
    pip install --no-index --find-links=..\yfg-packages -r requirements.txt
    if not errorlevel 1 (
        echo ✓ نصب از پوشه محلی موفق بود
        goto :done
    )
    echo ✗ نصب از پوشه محلی ناموفق بود، تلاش با روش آنلاین...
)

REM روش ۲: نصب آنلاین با تایم‌اوت بلند
echo [روش ۲] نصب آنلاین (با تایم‌اوت ۱۲۰ ثانیه)...
pip install --timeout 120 -r requirements.txt
if errorlevel 1 (
    echo ✗ نصب ناموفق بود
    echo.
    echo راه‌حل‌های جایگزین:
    echo   1. از VPN یا پراکسی استفاده کنید
    echo   2. دستی نصب کنید:
    echo      pip install fastapi
    echo      pip install "uvicorn"
    echo      pip install python-multipart
    echo      pip install openpyxl
    echo      pip install cryptography
    echo   3. از آینه ایرانی استفاده کنید:
    echo      pip install -i https://mirror.py encountered.org/pypi/simple -r requirements.txt
    pause
    exit /b 1
)

:done
echo.
echo ✓ همه وابستگی‌ها نصب شد
echo.
echo حالا می‌توانید start.bat را اجرا کنید
pause
