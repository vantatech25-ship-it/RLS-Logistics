# RLS Logistics — ONE-CLICK MASTER LAUNCHER
# Global Command Centre v1.4.0

Write-Host "--- RLS LOGISTICS: NEURAL COMMAND CENTRE INITIALISING ---" -ForegroundColor Cyan

# 1. Environment Check
if (-not (Test-Path ".env")) {
    Write-Host "[!] Secrets missing. Please add your PINECONE_API_KEY to .env" -ForegroundColor Red
    # For demo purposes, we will continue, but real prod needs this.
}

# 2. Kill existing processes to prevent port conflicts
Write-Host "[+] Clearing neural pathways (Cleaning up old ports)..." -ForegroundColor Gray
Get-Process -Name "python" -ErrorAction SilentlyContinue | Where-Object { $_.MainWindowTitle -eq "" } | Stop-Process -Force -ErrorAction SilentlyContinue

# 3. Start Master Backend (Port 8000) - The Brain
Write-Host "[+] Awakening Neural Core (Master Backend on :8000)..." -ForegroundColor Yellow
Start-Process -FilePath "powershell.exe" -ArgumentList "-Command & 'C:\Users\ASUS\REAL TIME LOGISTICS\.venv\Scripts\python.exe' -m uvicorn main:app --app-dir 'C:\Users\ASUS\REAL TIME LOGISTICS\dashboard' --port 8000" -WindowStyle Hidden

# 4. Start Orchestration API (Port 8002) - The Agent
Write-Host "[+] Initialising LangGraph Orchestrator (Orchestration on :8002)..." -ForegroundColor Yellow
Start-Process -FilePath "powershell.exe" -ArgumentList "-Command & 'C:\Users\ASUS\REAL TIME LOGISTICS\.venv\Scripts\python.exe' -m uvicorn orchestrator:app --app-dir 'C:\Users\ASUS\REAL TIME LOGISTICS\orchestration' --port 8002" -WindowStyle Hidden

# 5. Start GNN Sidecar (Port 3000) - The Neural Network
Write-Host "[+] Booting GNN Routing Sidecar (GNN Engine on :3000)..." -ForegroundColor Yellow
Start-Process -FilePath "powershell.exe" -ArgumentList "-Command & 'C:\Users\ASUS\REAL TIME LOGISTICS\.venv\Scripts\python.exe' -m uvicorn gnn_service:app --app-dir 'C:\Users\ASUS\REAL TIME LOGISTICS\routing-engine' --port 3000" -WindowStyle Hidden

# 6. Start Unified Master Portal (Port 8084) - The Interface
Write-Host "[+] Rendering Global Command Centre Portal (Master UI on :8084)..." -ForegroundColor Green
Start-Process -FilePath "powershell.exe" -ArgumentList "-Command & 'C:\Users\ASUS\REAL TIME LOGISTICS\.venv\Scripts\python.exe' -m http.server 8084 --directory 'C:\Users\ASUS\REAL TIME LOGISTICS'" -WindowStyle Hidden

# 7. Start Sub-Workspaces (Back-compat pings)
Start-Process -FilePath "powershell.exe" -ArgumentList "-Command & 'C:\Users\ASUS\REAL TIME LOGISTICS\.venv\Scripts\python.exe' -m http.server 8085 --directory 'C:\Users\ASUS\REAL TIME LOGISTICS\core-digital-twin'" -WindowStyle Hidden
Start-Process -FilePath "powershell.exe" -ArgumentList "-Command & 'C:\Users\ASUS\REAL TIME LOGISTICS\.venv\Scripts\python.exe' -m http.server 8086 --directory 'C:\Users\ASUS\REAL TIME LOGISTICS\dashboard'" -WindowStyle Hidden

# 8. Warm-up & Launch Browser
Write-Host "--- NEURAL SYNC COMPLETE ---" -ForegroundColor Cyan
Write-Host "[!] Launching Master Portal in 3 seconds..." -ForegroundColor Gray
Start-Sleep -Seconds 3

# Open the Master Portal
Start-Process "http://localhost:8084"

Write-Host "`nRLS LOGISTICS IS LIVE. COMMENCING COMMAND CENTRE OPS." -ForegroundColor Green
