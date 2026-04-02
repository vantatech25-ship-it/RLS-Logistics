#!/bin/bash
# tablet_setup.sh (v2.0)
# RLS Logistics — Unified Mobile Command Centre Launcher
# --------------------------------------------------------------------------

echo "----------------------------------------------------"
echo "◈ RLS LOGISTICS: MOBILE COMMAND CENTRE ◈"
echo "----------------------------------------------------"

# 1. Verification of System Assets
if [ ! -f "gnn_sidecar.zip" ]; then
    echo "[!] Error: gnn_sidecar.zip not found."
    exit 1
fi

# 2. Extract Sidecar & Backend Components
echo "[+] Preparing Neural Engine assets..."
unzip -o gnn_sidecar.zip -d ./gnn-engine > /dev/null

# 3. Environment Preparation
if [ ! -d ".venv_tablet" ]; then
    echo "[+] Initializing Python virtual environment..."
    python3 -m venv .venv_tablet
fi
source .venv_tablet/bin/activate

echo "[+] Syncing service dependencies..."
# Use consolidated requirements
pip install -q fastapi uvicorn httpx pinecone-client asyncpg pytorch-geometric > /dev/null

# 4. Starting Unified Backend (GNN + Orchestrator)
echo "[+] Starting Autonomous Orchestration Pool..."
# We run the orchestrator and sidecar in the background
nohup python3 orchestrator.py > orchestrator.log 2>&1 &
ORCH_PID=$!

echo "[+] Initializing GNN Hub Sidecar..."
cd gnn-engine
nohup python3 gnn_service.py > gnn_sidecar.log 2>&1 &
GNN_PID=$!
cd ..

# 5. UI Auto-Launch (Kiosk Mode)
echo "----------------------------------------------------"
echo "[✔] BACKEND SERVICES INITIALIZED"
echo "[i] Orchestrator PID: $ORCH_PID"
echo "[i] GNN Hub PID: $GNN_PID"
echo "----------------------------------------------------"

# Detect browser and launch dashboard
echo "[+] Launching RLS Command Centre Dashboard..."
if command -v google-chrome > /dev/null; then
    google-chrome --kiosk --new-window "http://localhost:8000/dashboard.html" &
elif command -v firefox > /dev/null; then
    firefox --kiosk "http://localhost:8000/dashboard.html" &
else
    echo "[!] No kiosk browser found. Please open: http://localhost:8000/dashboard.html"
fi

echo "◈ SYSTEM READY ◈"
echo "Handover to client now. Close terminal to terminate."
