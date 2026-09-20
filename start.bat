@echo off
title Roblox Anti-AFK Bot Launcher
color 0A

echo ========================================================
echo         ROBLOX ANTI-AFK BOT (WALK ^& JUMP)
echo ========================================================
echo.

:: Periksa apakah Python terpasang di sistem
python --version >nul 2>&1
if %errorlevel% neq 0 (
    color 0C
    echo [ERROR] Python tidak terdeteksi di komputer Anda!
    echo Silakan unduh dan install Python dari https://www.python.org/
    echo Pastikan mencentang opsi "Add Python to PATH" saat instalasi.
    echo.
    pause
    exit /b
)

:: Pastikan dependensi sudah terpasang
echo [1/2] Memeriksa dependensi (pydirectinput, keyboard)...
pip install -r requirements.txt --quiet --disable-pip-version-check

:: Jalankan Bot GUI
echo [2/2] Membuka Antarmuka Bot...
echo.
python main.py

if %errorlevel% neq 0 (
    echo.
    echo Program ditutup dengan kode error %errorlevel%.
    pause
)
