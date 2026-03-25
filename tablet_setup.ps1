# tablet_setup.ps1
# RLS Logistics — GNN Sidecar Launcher (Windows/Testing Version)

Write-Host "--- RLS Logistics: GNN Sidecar Local Testing ---" -ForegroundColor Cyan

# 1. Unpack Sidecar
if (Test-Path "gnn_sidecar.zip") {
    Write-Host "[+] Extracting gnn_sidecar.zip..." -ForegroundColor Green
    Expand-Archive -Path "gnn_sidecar.zip" -DestinationPath "." -Force
} else {
    Write-Host "[!] gnn_sidecar.zip not found! Please ensure it is in the current directory." -ForegroundColor Red
    exit
}

# 2. Setup Virtual Environment
if (-not (Test-Path ".venv_tablet")) {
    Write-Host "[+] Creating Python virtual environment..." -ForegroundColor Green
    python -m venv .venv_tablet
}

# 3. Install Requirements
Write-Host "[+] Installing GNN dependencies..." -ForegroundColor Green
& .venv_tablet/Scripts/pip install -r gnn_requirements.txt

# 4. Start GNN Sidecar
Write-Host "[+] Starting GNN Sidecar on port 8000..." -ForegroundColor Green
Write-Host "[i] Tip: Close this terminal or press Ctrl+C to stop." -ForegroundColor Yellow
& .venv_tablet/Scripts/python gnn_service.py
