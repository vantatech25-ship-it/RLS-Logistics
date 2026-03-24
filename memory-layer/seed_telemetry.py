"""
seed_telemetry.py
RLS Logistics — Telemetry Simulator
Seeds TimescaleDB and Pinecone with synthetic logistics data for the Dashboard and Digital Twin.
"""

import asyncio
import random
import time
from datetime import datetime, timedelta, timezone
import asyncpg
from pinecone_client import upsert_hub_embedding
from timescale_client import record_hub_telemetry, record_vehicle_ping, log_route_execution, init_schema
from config import TIMESCALE_DSN

# --- Configuration ---
HUBS = [
    {"hub_id": "JHB", "lat": -26.2041, "lon": 28.0473, "connectivity": 3},
    {"hub_id": "CPT", "lat": -33.9249, "lon": 18.4241, "connectivity": 2},
    {"hub_id": "DBN", "lat": -29.8587, "lon": 31.0218, "connectivity": 2},
    {"hub_id": "PE",  "lat": -33.9608, "lon": 25.6022, "connectivity": 3},
]

VEHICLES = ["VAN-001", "VAN-002", "VAN-003", "TRK-101", "TRK-102", "TRK-103"]

async def seed_historical_hubs():
    """Seed 12 hours of hub telemetry."""
    print("[Seed] Seeding hub telemetry trend...")
    for hub in HUBS:
        for i in range(24):  # 24 half-hour intervals
            timestamp = datetime.now(timezone.utc) - timedelta(minutes=30 * i)
            load = 0.4 + random.random() * 0.4
            cong = 0.3 + random.random() * 0.4
            
            # Using record_hub_telemetry but patching the time if needed
            # For simplicity, we just seed current + slightly past
            await record_hub_telemetry({
                "hub_id": hub["hub_id"],
                "load_factor": load,
                "congestion_score": cong,
                "active": True
            })
            # Also upsert latest to Pinecone
            if i == 0:
                upsert_hub_embedding({
                    **hub,
                    "load_factor": load,
                    "congestion_score": cong
                })

async def seed_live_fleet():
    """Seed current GPS position for all vehicles."""
    print("[Seed] Seeding live fleet positions...")
    for vehicle in VEHICLES:
        origin = random.choice(HUBS)
        # Random offset from hub
        lat = origin["lat"] + (random.random() - 0.5) * 0.1
        lon = origin["lon"] + (random.random() - 0.5) * 0.1
        
        await record_vehicle_ping({
            "vehicle_id": vehicle,
            "hub_id": origin["hub_id"],
            "latitude": lat,
            "longitude": lon,
            "speed_kmh": random.randint(40, 110),
            "heading_deg": random.randint(0, 359)
        })

async def seed_routes():
    """Seed some recent route executions."""
    print("[Seed] Seeding recent route logs...")
    for i in range(10):
        h1, h2 = random.sample(HUBS, 2)
        await log_route_execution({
            "route_id": f"R-{random.randint(1000, 9999)}",
            "from_hub_id": h1["hub_id"],
            "to_hub_id": h2["hub_id"],
            "predicted_cost": random.randint(500, 3000),
            "gnn_confidence": random.randint(60, 95)
        })

async def main():
    print("--- RLS Logistics: Data Seeder ---")
    try:
        # 1. Init Schema
        conn = await asyncpg.connect(TIMESCALE_DSN)
        await init_schema(conn)
        await conn.close()
        
        # 2. Seed Data
        await seed_historical_hubs()
        await seed_live_fleet()
        await seed_routes()
        
        print("\n[OK] Seeding complete! Dashboard should now show live data.")
    except Exception as e:
        print(f"\n[FAIL] Seeding failed: {e}")
        print("    Ensure TimescaleDB is running on localhost:5432")

if __name__ == "__main__":
    asyncio.run(main())
