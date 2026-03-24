#!/bin/bash
# tablet_setup.sh
# RLS Logistics — Webfleet Tablet GNN Launcher

echo "--- RLS Logistics: Webfleet Tablet Deployment ---"

# 1. Unpack Sidecar (assumes zip is in current dir)
if [ -f "gnn_sidecar.zip" ]; then
    echo "[+] Extracting gnn_sidecar.zip..."
    unzip -o gnn_sidecar.zip
else
    echo "[!] gnn_sidecar.zip not found! Please copy it to the tablet first."
fi

# 2. Setup Virtual Environment
if [ ! -d ".venv" ]; then
    echo "[+] Creating Python virtual environment..."
    python3 -m venv .venv
fi

source .venv/bin/activate

# 3. Install Requirements
echo "[+] Installing GNN dependencies..."
pip install -r gnn_requirements.txt

# 4. Start GNN Sidecar
echo "[+] Starting GNN Sidecar on port 8000..."
# Running in background with nohup so it stays alive if terminal closes
nohup python3 gnn_service.py > gnn_sidecar.log 2>&1 &

echo "--- Deployment Complete ---"
echo "Verify liveness: curl http://localhost:8000/health"
echo "Logs available in: gnn_sidecar.log"
