#!/bin/bash
echo "================================================="
echo "  YFG Accounting Desk - Install Dependencies"
echo "================================================="

if [ -d "../yfg-packages" ]; then
    echo "[Method 1] Installing from local packages (offline)..."
    pip install --no-index --find-links=../yfg-packages -r requirements.txt
    if [ $? -eq 0 ]; then
        echo "SUCCESS: Installed from local packages"
        exit 0
    fi
    echo "FAILED: Local install failed, trying online..."
fi

echo "[Method 2] Installing online (timeout=300s)..."
pip install --timeout 300 -r requirements.txt
if [ $? -ne 0 ]; then
    echo "FAILED: Online install also failed"
    echo "Try: pip install fastapi uvicorn python-multipart openpyxl cryptography"
    exit 1
fi

echo "SUCCESS: All dependencies installed!"
