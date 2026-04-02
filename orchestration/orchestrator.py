"""
orchestrator.py
LangGraph agent orchestrating the Living Neural Network logistics pipeline.
Now exposed as a FastAPI service for real-time UI dispatching.

Graph flow:
  fetch_hubs → store_memory → request_route → log_route → END
"""

import asyncio
import uuid
import httpx
from typing import TypedDict, List, Dict, Any, Optional
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from langgraph.graph import StateGraph, END

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), "memory-layer"))

from pinecone_client import upsert_hub_embedding, find_similar_hubs
from timescale_client import record_hub_telemetry, log_route_execution

from config import ROUTING_ENGINE_URL


# ---------------------------------------------------------------------------
# App Setup
# ---------------------------------------------------------------------------

app = FastAPI(title="RLS Logistics Orchestrator", version="1.1.0")

class DispatchRequest(BaseModel):
    from_hub_id: str
    to_hub_id: str

# ---------------------------------------------------------------------------
# Agent State — shared across all graph nodes
# ---------------------------------------------------------------------------

class AgentState(TypedDict):
    """
    The single mutable state object that flows through the LangGraph pipeline.
    """
    from_hub_id: str
    to_hub_id: str
    hub_features: List[Dict[str, Any]]
    route_recommendation: Optional[Dict[str, Any]]
    route_id: str
    errors: List[str]


# ---------------------------------------------------------------------------
# Nodes (Refactored for cleaner async execution)
# ---------------------------------------------------------------------------

async def fetch_hubs(state: AgentState) -> AgentState:
    print(f"[Orchestrator] Fetching live hubs from {ROUTING_ENGINE_URL}")
    async with httpx.AsyncClient() as client:
        try:
            resp = await client.get(f"{ROUTING_ENGINE_URL}/hubs", timeout=5.0)
            resp.raise_for_status()
            data = resp.json()
            if data.get("success"):
                state["hub_features"] = data["data"]
            else:
                state["errors"].append("Routing engine returned success=false")
        except Exception as e:
            state["errors"].append(f"HTTP Error: {str(e)}")
    return state


async def store_memory(state: AgentState) -> AgentState:
    hub_features = state.get("hub_features", [])
    if not hub_features:
        return state

    print(f"[Orchestrator] Storing memory for {len(hub_features)} hubs")
    
    # Store telemetry and embeddings in parallel
    async def _process_hub(h):
        try:
            upsert_hub_embedding(h)
            await record_hub_telemetry(h)
        except Exception as e:
            print(f"Error storing hub {h.get('hub_id')}: {e}")

    await asyncio.gather(*[_process_hub(h) for h in hub_features])
    return state


async def request_route(state: AgentState) -> AgentState:
    print(f"[Orchestrator] Requesting GNN route: {state['from_hub_id']} → {state['to_hub_id']}")
    async with httpx.AsyncClient() as client:
        try:
            resp = await client.post(
                f"{ROUTING_ENGINE_URL}/route",
                json={"from_hub_id": state["from_hub_id"], "to_hub_id": state["to_hub_id"]},
                timeout=10.0,
            )
            recommendation = resp.json().get("data")
            if resp.status_code == 200 and recommendation:
                state["route_recommendation"] = recommendation
            else:
                # Fallback: Query Pinecone for similar hub logic
                print("[Orchestrator] Route failed — leveraging Pinecone memory layer...")
                ref_hub = state["hub_features"][0] if state["hub_features"] else {"hub_id": state["from_hub_id"]}
                alternatives = find_similar_hubs(ref_hub, top_k=2)
                state["errors"].append(f"Route fail. Alt suggestions: {[a.get('id') for a in alternatives]}")
        except Exception as e:
            state["errors"].append(f"Route API error: {str(e)}")
    return state


async def log_route(state: AgentState) -> AgentState:
    rec = state.get("route_recommendation")
    if rec:
        print("[Orchestrator] Logging dispatched route to persistence layer")
        await log_route_execution({
            "route_id": state["route_id"],
            "from_hub_id": state["from_hub_id"],
            "to_hub_id": state["to_hub_id"],
            "predicted_cost": rec.get("adjusted_cost", 0.0),
            "gnn_confidence": rec.get("confidence", 0),
        })
    return state


def check_route(state: AgentState) -> str:
    return "log_route" if state.get("route_recommendation") else END


# ---------------------------------------------------------------------------
# Graph Construction
# ---------------------------------------------------------------------------

def build_graph() -> StateGraph:
    workflow = StateGraph(AgentState)
    workflow.add_node("fetch_hubs",   fetch_hubs)
    workflow.add_node("store_memory", store_memory)
    workflow.add_node("request_route", request_route)
    workflow.add_node("log_route",    log_route)

    workflow.set_entry_point("fetch_hubs")
    workflow.add_edge("fetch_hubs",    "store_memory")
    workflow.add_edge("store_memory",  "request_route")
    workflow.add_conditional_edges("request_route", check_route, {
        "log_route": "log_route",
        END: END
    })
    workflow.add_edge("log_route", END)
    return workflow.compile()


# ---------------------------------------------------------------------------
# API Endpoints
# ---------------------------------------------------------------------------

@app.get("/health")
async def health():
    return {"status": "online", "service": "rls-orchestrator"}

@app.post("/dispatch")
async def dispatch_route(req: DispatchRequest):
    """Entry point for the dashboard UI."""
    orchestrator = build_graph()
    initial_state: AgentState = {
        "from_hub_id": req.from_hub_id,
        "to_hub_id": req.to_hub_id,
        "hub_features": [],
        "route_recommendation": None,
        "route_id": str(uuid.uuid4()),
        "errors": [],
    }
    
    try:
        result = await orchestrator.ainvoke(initial_state)
        return {
            "success": len(result["errors"]) == 0 or result.get("route_recommendation") is not None,
            "data": result.get("route_recommendation"),
            "route_id": result["route_id"],
            "errors": result["errors"]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8002)
