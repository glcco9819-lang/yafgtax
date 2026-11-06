#!/bin/bash
echo "================================================="
echo "  YFG Accounting Desk v0.3.0.16"
echo "================================================="

echo "[1/4] Checking Python..."
PYTHON=python3
command -v python3 &>/dev/null || PYTHON=python
$PYTHON --version || { echo "ERROR: Python not found"; exit 1; }

echo "[2/4] Checking dependencies..."
$PYTHON -c "import fastapi" 2>/dev/null || {
    echo "Installing dependencies..."
    pip install --timeout 300 -r requirements.txt || { echo "ERROR: Install failed"; exit 1; }
}

echo "[3/4] Creating data directories..."
mkdir -p ../data/files ../data/attachments ../data/documents ../data/backups

echo "[4/4] Starting server..."
echo ""
echo "================================================="
echo "  Server started!"
echo "  URL:  http://localhost:8000/static/index.html"
echo "  User: admin"
echo "  Pass: admin123"
echo "================================================="
echo ""

cd app
$PYTHON -m uvicorn main:app --host 0.0.0.0 --port 8000 --proxy-headers
