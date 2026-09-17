# Hypersonus Studio PowerShell Launcher
Write-Host "========================================================" -ForegroundColor Cyan
Write-Host "            Starting Hypersonus Studio                  " -ForegroundColor Cyan
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

Write-Host "[*] Launching Streamlit Studio..." -ForegroundColor Green
streamlit run app.py
