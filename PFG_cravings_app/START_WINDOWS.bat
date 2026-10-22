@echo off
setlocal
cd /d "%~dp0"
if not exist ".venv\Scripts\python.exe" (
  echo Creating Python virtual environment...
  py -3 -m venv .venv
  if errorlevel 1 (echo Install Python 3.11 or newer first.& pause & exit /b 1)
)
".venv\Scripts\python.exe" -c "import fastapi,uvicorn,reportlab,tzdata,multipart" >nul 2>&1
if errorlevel 1 (
  echo Installing required libraries...
  ".venv\Scripts\python.exe" -m pip install -r requirements.txt
  if errorlevel 1 (echo Dependency installation failed.& pause & exit /b 1)
)
echo.
echo Starting PFG Cravings on the office network...
echo Buyer: http://localhost:8000/
echo Seller: http://localhost:8000/admin
echo If admin has not been configured, run:
echo   .venv\Scripts\python.exe -m app.manage setup-admin
echo.
".venv\Scripts\python.exe" run.py
pause
