@echo off
title Hypersonus Studio Desktop
echo ========================================================
echo          Starting Hypersonus Studio Desktop App         
echo ========================================================
echo.

if not exist ".venv\Scripts\activate.bat" (
    echo [!] Virtual environment not found. Initializing .venv...
    py -3.11 -m venv .venv
    call .venv\Scripts\activate.bat
    echo [*] Installing dependencies from requirements.txt...
    pip install -r requirements.txt
) else (
    call .venv\Scripts\activate.bat
)

echo [*] Launching Native Flet Desktop Window...
python desktop\main.py
