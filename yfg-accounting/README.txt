YFG Accounting Desk v0.3.0.16
=============================

HOW TO RUN:
1. Extract this ZIP file
2. Open the yfg-accounting folder
3. Double-click RUN.bat
4. Wait for install + server start
5. Open browser: http://localhost:8000
6. Login: admin / admin123

REQUIREMENTS:
- Python 3.9+ (https://www.python.org/downloads/)
- Make sure to check "Add Python to PATH" during Python installation

IF RUN.bat FAILS:
  Open Command Prompt and type:
  cd yfg-accounting
  pip install --timeout 300 fastapi uvicorn python-multipart openpyxl cryptography
  cd app
  python -m uvicorn main:app --host 0.0.0.0 --port 8000

TO UPDATE LATER:
  Login to the app > Settings > System Update > Download from GitHub

REPOSITORY:
  https://github.com/glcco9819-lang/yafgtax.git
