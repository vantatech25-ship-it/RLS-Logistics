# launch.ps1
# RLS Logistics — Local Stack Launcher

Write-Host "--- RLS Logistics Launcher ---" -ForegroundColor Cyan

# 1. Check for .env
if (-not (Test-Path ".env")) {
    Write-Host "[!] .env file not found. Copying from .env.example..." -ForegroundColor Yellow
    Copy-Item ".env.example" ".env"
}

# 2. Check for Docker
if (-not (Get-Command "docker" -ErrorAction SilentlyContinue)) {
    Write-Host "[!] Docker not found in PATH. Please install Docker Desktop." -ForegroundColor Red
    exit
}

# 3. Launch Docker Compose
Write-Host "[+] Launching full-stack orchestration..." -ForegroundColor Green
docker compose up --build -d

# 4. Wait for healthy endpoints
Write-Host "[...] Waiting for services to warm up..." -ForegroundColor Gray
Start-Sleep -Seconds 10

Write-Host "`nSystem Ready!" -ForegroundColor Green
Write-Host "  Digital Twin:  http://localhost:8080"
Write-Host "  KPI Dashboard: http://localhost:8000"
Write-Host "  Routing API:   http://localhost:3000/health"
