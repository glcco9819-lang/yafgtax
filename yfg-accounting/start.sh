#!/bin/bash
# YFG Accounting Desk - Startup Script
# ====================================

echo "═══════════════════════════════════════════"
echo "  YFG Accounting Desk v0.3.0.16"
echo "  راه‌اندازی سامانه"
echo "═══════════════════════════════════════════"

# Step 1: Check Python
echo ""
echo "[۱/۵] بررسی Python..."
if command -v python3 &> /dev/null; then
    PYTHON=python3
elif command -v python &> /dev/null; then
    PYTHON=python
else
    echo "✗ Python نصب نیست. ابتدا Python 3.9+ نصب کنید:"
    echo "  Ubuntu/Debian: sudo apt install python3 python3-pip"
    echo "  CentOS/RHEL: sudo yum install python3 python3-pip"
    echo "  Windows: https://python.org/downloads"
    exit 1
fi
echo "✓ Python: $($PYTHON --version)"

# Step 2: Install dependencies
echo ""
echo "[۲/۵] نصب وابستگی‌ها..."
$PYTHON -m pip install --upgrade pip -q
$PYTHON -m pip install -r requirements.txt -q
if [ $? -ne 0 ]; then
    echo "✗ نصب وابستگی‌ها ناموفق بود"
    echo "  دستور دستی: pip install -r requirements.txt"
    exit 1
fi
echo "✓ وابستگی‌ها نصب شد"

# Step 3: Create data directory
echo ""
echo "[۳/۵] ساخت پوشه داده..."
mkdir -p data/files
mkdir -p data/attachments
mkdir -p data/documents
mkdir -p data/backups
mkdir -p data/imports
echo "✓ پوشه‌های داده ساخته شد"

# Step 4: Initialize database
echo ""
echo "[۴/۵] راه‌اندازی دیتابیس..."
cd app
$PYTHON -c "
import sys
sys.path.insert(0, '.')
from main import init_db
init_db()
print('✓ دیتابیس آماده')
"
if [ $? -ne 0 ]; then
    echo "✗ راه‌اندازی دیتابیس ناموفق بود"
    exit 1
fi

# Step 5: Start server
echo ""
echo "[۵/۵] اجرای سرور..."
echo ""
echo "═══════════════════════════════════════════"
echo "  ✓ سامانه راه‌اندازی شد!"
echo ""
echo "  آدرس: http://localhost:8000/static/index.html"
echo "  کاربر: admin"
echo "  رمز:   admin123"
echo ""
echo "  برای توقف: Ctrl+C"
echo "═══════════════════════════════════════════"
echo ""

$PYTHON -m uvicorn main:app --host 0.0.0.0 --port 8000 --proxy-headers
