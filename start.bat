@echo off
title SecurePay - Digital Payment Gateway
echo ========================================================
echo           SecurePay - Starting System
echo ========================================================
echo.

cd /d "%~dp0backend"
echo [1/3] Checking demo database...
python seed.py
if %ERRORLEVEL% NEQ 0 (
    echo [Warning] Failed to run seed script. Proceeding anyway...
)

echo.
echo [2/3] Launching Flask Backend on http://localhost:5000 ...
start "SecurePay Backend (Flask:5000)" cmd /k "cd /d ""%~dp0backend"" && python run.py"

timeout /t 2 /nobreak >nul

echo.
echo [3/3] Launching React Frontend on http://localhost:3000 ...
start "SecurePay Frontend (Vite:3000)" cmd /k "cd /d ""%~dp0frontend"" && npm run dev"

echo.
echo ========================================================
echo System launched!
echo - Web UI:  http://localhost:3000
echo - API:     http://localhost:5000/api
echo.
echo Demo Accounts (Password for all: password123):
echo   Customer: customer1@securepay.com
echo   Merchant: merchant1@securepay.com
echo   Admin:    admin@securepay.com
echo ========================================================
echo.
pause
