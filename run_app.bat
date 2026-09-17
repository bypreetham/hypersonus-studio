@echo off
title Hypersonus Studio
echo ========================================================
echo             Starting Hypersonus Studio Suite            
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

echo [*] Launching Hypersonus Studio on local web server...
streamlit run app.py
pause
