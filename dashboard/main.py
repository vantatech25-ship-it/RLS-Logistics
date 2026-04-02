"""
main.py — RLS Logistics KPI Dashboard
FastAPI backend serving real-time metrics from TimescaleDB + Routing Engine.
Pairs with the frontend dashboard.html for a full KPI view.
"""

import asyncio
import httpx
import asyncpg
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from contextlib import asynccontextmanager
import os

TIMESCALE_DSN      = os.getenv("TIMESCALE_DSN", "postgresql://rls_user:rls_pass@localhost:5432/rls_logistics")
ROUTING_ENGINE_URL = os.getenv("ROUTING_ENGINE_URL", "http://localhost:3000")
ORCHESTRATOR_URL   = os.getenv("ORCHESTRATOR_URL", "http://localhost:8002")


# ─── App lifecycle ────────────────────────────────────────────────────────────
@asynccontextmanager
async def lifespan(app: FastAPI):
    try:
        app.state.db = await asyncpg.create_pool(TIMESCALE_DSN, min_size=2, max_size=10)
        print(f"Connected to TimescaleDB at {TIMESCALE_DSN}")
    except Exception as e:
        print(f"Warning: Could not connect to TimescaleDB: {e}. Using mockup mode.")
        app.state.db = None
    yield
    if app.state.db:
        await app.state.db.close()


app = FastAPI(title="RLS Logistics KPI Dashboard", version="1.0.0", lifespan=lifespan)
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])


# ─── Serve frontend ───────────────────────────────────────────────────────────
@app.get("/")
async def serve_dashboard():
    # Use absolute path to ensure dashboard.html is found regardless of CWD
    static_path = os.path.join(os.path.dirname(__file__), "dashboard.html")
    return FileResponse(static_path)


# ─── /api/kpis — top-level summary metrics ───────────────────────────────────
@app.get("/api/kpis")
async def get_kpis():
    """One-stop endpoint: hub count, avg congestion, route stats."""
    pool = app.state.db
    if not pool:
        # Mockup data for demo when DB is down
        return {
            "hub_count":       4,
            "avg_congestion":  0.42,
            "avg_load":        0.65,
            "recent_readings": 24,
            "routes_24h":      152,
            "routes_completed":148,
            "avg_cost_delta":  -12.5,
            "avg_confidence":  94.2,
            "live_vehicles":   12,
        }

    # Hub stats
    hub_stats = await pool.fetchrow("""
        SELECT
            COUNT(DISTINCT hub_id)                        AS total_hubs,
            AVG(congestion_score)                         AS avg_congestion,
            AVG(load_factor)                              AS avg_load,
            COUNT(*) FILTER (WHERE time > NOW() - INTERVAL '5 min') AS recent_readings
        FROM hub_telemetry
    """)

    # Route stats
    route_stats = await pool.fetchrow("""
        SELECT
            COUNT(*)                            AS total_routes,
            COUNT(*) FILTER (WHERE completed)   AS completed_routes,
            AVG(actual_cost - predicted_cost)
              FILTER (WHERE completed)          AS avg_cost_delta,
            AVG(gnn_confidence)                 AS avg_confidence
        FROM route_executions
        WHERE time > NOW() - INTERVAL '24 hours'
    """)

    # Live fleet size
    fleet = await pool.fetchval("""
        SELECT COUNT(DISTINCT vehicle_id) FROM vehicle_pings
        WHERE time > NOW() - INTERVAL '10 min'
    """)

    return {
        "hub_count":       hub_stats["total_hubs"] or 0,
        "avg_congestion":  round(float(hub_stats["avg_congestion"] or 0.0), 3),
        "avg_load":        round(float(hub_stats["avg_load"] or 0.0), 3),
        "recent_readings": hub_stats["recent_readings"] or 0,
        "routes_24h":      route_stats["total_routes"] or 0,
        "routes_completed":route_stats["completed_routes"] or 0,
        "avg_cost_delta":  round(float(route_stats["avg_cost_delta"] or 0.0), 2),
        "avg_confidence":  round(float(route_stats["avg_confidence"] or 0.0), 1),
        "live_vehicles":   fleet or 0,
    }


# ─── /api/hubs — per-hub congestion trend ────────────────────────────────────
@app.get("/api/hubs")
async def get_hub_scores():
    """Latest GNN scores per hub, proxied from the Rust engine."""
    async with httpx.AsyncClient() as client:
        try:
            r = await client.get(f"{ROUTING_ENGINE_URL}/hubs", timeout=2.0)
            return r.json()
        except Exception:
            # Mockup hub scores for demo
            return {
                "success": True,
                "data": [
                    {"hub_id":"JHB", "load_factor":0.75, "congestion_score":0.52, "connectivity":3},
                    {"hub_id":"CPT", "load_factor":0.45, "congestion_score":0.28, "connectivity":2},
                    {"hub_id":"DBN", "load_factor":0.82, "congestion_score":0.61, "connectivity":2},
                    {"hub_id":"PE",  "load_factor":0.35, "congestion_score":0.15, "connectivity":3},
                ]
            }


# ─── /api/congestion-trend — last 12h time-series ────────────────────────────
@app.get("/api/congestion-trend")
async def congestion_trend(hub_id: str = "JHB"):
    pool = app.state.db
    if not pool:
        # Mockup trend data
        import datetime
        now = datetime.datetime.now()
        return [
            {"time": str(now - datetime.timedelta(hours=i)), "congestion": 0.3 + (i % 5)*0.1, "load": 0.5 + (i % 3)*0.1}
            for i in range(24, 0, -1)
        ]

    rows = await pool.fetch("""
        SELECT
            time_bucket('30 minutes', time) AS bucket,
            AVG(congestion_score)           AS avg_cong,
            AVG(load_factor)                AS avg_load
        FROM hub_telemetry
        WHERE hub_id = $1
          AND time > NOW() - INTERVAL '12 hours'
        GROUP BY bucket
        ORDER BY bucket ASC
    """, hub_id)
    return [{"time": str(r["bucket"]), "congestion": round(float(r["avg_cong"] or 0.0), 3), "load": round(float(r["avg_load"] or 0.0), 3)} for r in rows]


# ─── /api/routes/recent — last 20 dispatched routes ─────────────────────────
@app.get("/api/routes/recent")
async def recent_routes():
    pool = app.state.db
    if not pool:
        # Mockup recent routes
        return [
            {"route_id": "R-9982", "from_hub_id": "JHB", "to_hub_id": "CPT", "predicted_cost": 2240, "actual_cost": 2180, "gnn_confidence": 94, "completed": True, "time": "2026-03-30T08:30:00Z"},
            {"route_id": "R-9983", "from_hub_id": "JHB", "to_hub_id": "DBN", "predicted_cost": 650, "actual_cost": 0, "gnn_confidence": 98, "completed": False, "time": "2026-03-30T09:15:00Z"},
        ]

    rows = await pool.fetch("""
        SELECT route_id, from_hub_id, to_hub_id, predicted_cost,
               actual_cost, gnn_confidence, completed, time
        FROM route_executions
        ORDER BY time DESC LIMIT 20
    """)
    return [dict(r) for r in rows]


# ─── /api/fleet — live vehicle positions ─────────────────────────────────────
@app.get("/api/fleet")
async def fleet_positions():
    pool = app.state.db
    if not pool:
        # Mock fleet data for demo
        return [{"vehicle_id": f"V-{100 + i}", "hub_id": "JHB", "latitude": -26.1, "longitude": 28.1, "speed_kmh": 85, "heading_deg": 120, "time": "2026-03-30T09:00:00Z"} for i in range(5)]
    
    rows = await pool.fetch("""
        SELECT DISTINCT ON (vehicle_id)
            vehicle_id, hub_id, latitude, longitude, speed_kmh, heading_deg, time
        FROM vehicle_pings
        ORDER BY vehicle_id, time DESC
    """)
    return [dict(r) for r in rows]


# ─── /api/dispatch — triggers the LangGraph orchestrator ─────────────────────
@app.post("/api/dispatch")
async def dispatch_route(from_hub_id: str, to_hub_id: str):
    """Proxies a dispatch request to the LangGraph autonomous orchestrator."""
    async with httpx.AsyncClient() as client:
        try:
            resp = await client.post(
                f"{ORCHESTRATOR_URL}/dispatch",
                json={"from_hub_id": from_hub_id, "to_hub_id": to_hub_id},
                timeout=2.0
            )
            return resp.json()
        except Exception as e:
            return {
                "success": True, 
                "data": {"confidence": 95}, 
                "route_id": "MOCK-9999", 
                "errors": [f"MOCK API"]
            }
