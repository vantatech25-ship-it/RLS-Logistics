# Routing Engine

**RTL Logistics — Living Neural Network | Rust GNN Routing Service**

A high-performance, async routing micro-service that combines **Dijkstra graph pathfinding** with **Graph Neural Network (GNN) congestion scoring** to produce optimal logistics routes in real-time.

---

## Architecture

```
src/
├── main.rs          # Tokio entry point, seeds the network, starts Axum server
├── graph/mod.rs     # Hub & RouteEdge models, live network graph (petgraph)
├── gnn/mod.rs       # Async client for GNN sidecar + heuristic fallback
├── api/mod.rs       # REST API handlers (Axum + Tower)
└── ...

gnn_service.py       # FastAPI sidecar serving the PyTorch GNN model
gnn_model.py         # PyTorch Geometric model definition and training
```

## API Endpoints

| Method | Path      | Description                                      |
|--------|-----------|--------------------------------------------------|
| GET    | `/health` | Liveness probe                                   |
| GET    | `/hubs`   | List all hubs with GNN congestion scores         |
| POST   | `/route`  | Get GNN-optimised route between two hubs         |
| POST   | `/hubs`   | Add a new hub to the live network                |
| POST   | `/routes` | Connect two hubs with a weighted route edge      |

## Route Request Example (for LangGraph)

```json
POST /route
{
  "from_hub_id": "JHB",
  "to_hub_id": "CPT"
}
```

### Response

```json
{
  "success": true,
  "data": {
    "path": {
      "from": "Johannesburg Hub",
      "to": "Cape Town Hub",
      "total_cost": 1680.0,
      "hubs_traversed": ["Johannesburg Hub", "Cape Town Hub"]
    },
    "gnn_adjustment": 0.365,
    "adjusted_cost": 2293.2,
    "confidence": 64,
    "hub_features": [ ... ]
  }
}
```

## Running Locally

> **Prerequisite**: Install Rust via [rustup.rs](https://rustup.rs)

```powershell
cd "routing-engine"
cargo run
# API available at http://localhost:3000
```

## Running Tests

```powershell
cargo test
```

## GNN Roadmap

- [x] **Phase 1**: Heuristic congestion scoring using hub load and connectivity features.
- [x] **Phase 2**: Replace heuristic with dedicated **GNN Sidecar** (FastAPI + PyTorch).
- [ ] **Phase 3**: Feed live telemetry from TimescaleDB into the GNN for real-time embeddings.

## Integration Points

| System          | How it connects                                      |
|-----------------|------------------------------------------------------|
| **LangGraph**   | Calls `POST /route` and `GET /hubs` via HTTP         |
| **TimescaleDB** | Feeds live traffic/load data into `RouteEdge` weights|
| **Pinecone**    | Stores `hub_features` embeddings for spatial search  |
| **Digital Twin**| Reads hub congestion scores for 3D visualization     |
