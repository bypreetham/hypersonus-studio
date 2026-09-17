# Hypersonus Studio Desktop PowerShell Launcher
Write-Host "========================================================" -ForegroundColor Cyan
Write-Host "       Starting Hypersonus Studio Desktop App           " -ForegroundColor Cyan
Write-Host "========================================================" -ForegroundColor Cyan

if (-not (Test-Path ".venv\Scripts\Activate.ps1")) {
    Write-Host "[!] Virtual environment not found. Initializing .venv..." -ForegroundColor Yellow
    py -3.11 -m venv .venv
    & .\.venv\Scripts\Activate.ps1
    Write-Host "[*] Installing dependencies..." -ForegroundColor Yellow
    pip install -r requirements.txt
} else {
    & .\.venv\Scripts\Activate.ps1
}

Write-Host "[*] Launching Native Desktop Window..." -ForegroundColor Green
python desktop\main.py
