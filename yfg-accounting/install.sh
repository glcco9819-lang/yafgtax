#!/bin/bash
echo "================================================="
echo "  YFG Accounting Desk - نصب وابستگی‌ها"
echo "================================================="
echo ""

# روش ۱: نصب از پوشه محلی
if [ -d "../yfg-packages" ]; then
    echo "[روش ۱] نصب از پوشه محلی (آفلاین)..."
    pip install --no-index --find-links=../yfg-packages -r requirements.txt
    if [ $? -eq 0 ]; then
        echo "✓ نصب از پوشه محلی موفق بود"
        exit 0
    fi
    echo "✗ نصب از پوشه محلی ناموفق بود، تلاش با روش آنلاین..."
fi

# روش ۲: نصب آنلاین
echo "[روش ۲] نصب آنلاین (با تایم‌اوت ۱۲۰ ثانیه)..."
pip install --timeout 120 -r requirements.txt
if [ $? -ne 0 ]; then
    echo "✗ نصب ناموفق بود"
    echo "راه‌حل: pip install fastapi uvicorn python-multipart openpyxl cryptography"
    exit 1
fi

echo "✓ همه وابستگی‌ها نصب شد"
