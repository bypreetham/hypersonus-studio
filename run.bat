@echo off
title Hypersonus Studio
echo ========================================================
echo             Starting Hypersonus Studio                  
echo ========================================================
echo.

if not exist ".venv\Scripts\activate.bat" (
    echo [!] Initializing virtual environment...
    py -3.11 -m venv .venv
    call .venv\Scripts\activate.bat
    echo [*] Installing dependencies...
    pip install -r requirements.txt
) else (
    call .venv\Scripts\activate.bat
)

echo [*] Launching Hypersonus Studio...
python main.py %*
