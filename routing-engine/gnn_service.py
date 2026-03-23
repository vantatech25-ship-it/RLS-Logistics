from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import torch
from gnn_model import LogisticsGNN, hubs_to_pyg_graph, predict_congestion, load_model
import os

app = FastAPI(title="RTL Logistics GNN Sidecar")

# Model configuration
MODEL_PATH = "gnn_weights.pt"
IN_CHANNELS = 4
HIDDEN_CHANNELS = 32

# Global model instance
model = None

@app.on_event("startup")
async def startup_event():
    global model
    if os.path.exists(MODEL_PATH):
        print(f"[GNN] Loading model from {MODEL_PATH}")
        model = load_model(MODEL_PATH, in_channels=IN_CHANNELS, hidden=HIDDEN_CHANNELS)
    else:
        print(f"[GNN] No model found at {MODEL_PATH}. Prediction will return fallback scores.")
        model = LogisticsGNN(in_channels=IN_CHANNELS, hidden=HIDDEN_CHANNELS)

class PredictionRequest(BaseModel):
    hub_features: list[dict]
    edges: list[list[int]]

@app.post("/predict")
async def predict(req: PredictionRequest):
    if not model:
        raise HTTPException(status_code=503, detail="Model not initialized")
    
    try:
        # Convert Rust-style data to PyG graph
        graph = hubs_to_pyg_graph(req.hub_features, [tuple(e) for e in req.edges])
        
        # Run inference
        scores = predict_congestion(model, graph)
        
        return {"scores": scores}
    except Exception as e:
        print(f"[GNN] Prediction error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/health")
async def health():
    return {"status": "ok", "model_loaded": model is not None}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
