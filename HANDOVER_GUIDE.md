# ◈ RLS LOGISTICS: CLIENT OPERATIONAL GUIDE ◈

Welcome to your **Living Neural Network Command Centre**. This tablet is your primary interface for autonomous fleet orchestration and real-time GNN-optimized routing.

## 1. Quick Start

- **Power On**: Ensure the tablet is connected to the internet.
- **Launch Command Centre**: Open the terminal and run `./tablet_setup.sh`.
- **System Ready**: The RLS Dashboard will automatically open in fullscreen (Kiosk mode).

## 2. Key Dashboard Metrics

### **Avg Congestion**
A GNN-derived score (0-100%).
- **< 35%**: Green (Optimal)
- **35% - 55%**: Orange (Slight Delay Potential)
- **> 55%**: Red (High-Congestion Detected)

### **GNN Confidence**
The neural network's self-assessment of its route prediction.
- **Goal**: > 90%
- **Action**: If < 80%, consider manual intervention.

## 3. Autonomous Orchestration

The system runs on an **Autonomous LangGraph Pipeline**.
- **Neural Sync**: Watch for the "Neural Sync" overlay; this indicates the AI is querying spatial memory for the best possible route.
- **Manual Dispatch**: Use the **Manual Dispatch** button to override AI suggestions or provide specific routing requests for your fleet.

## 4. Digital Twin Navigation

- **Rotate/Zoom**: Standard touch gestures to interact with the 3D Globe.
- **Fleet Pings**: Red/Green dots on the globe represent live vehicle telemetry.

## 5. Support & Neural Maintenance

- **Log Check**: All dispatch logs are securely stored in the TimescaleDB persistence layer.
- **Contact**: For infrastructure recalibration, contact your lead platform engineer.

---
*Powered by RLS Intelligent Logistics — v1.1.0*
