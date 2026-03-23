"""
RLS Logistics — Memory Layer
Manages:
  - Pinecone: vector embeddings for hub/route spatial memory
  - TimescaleDB: time-series telemetry (GPS pings, load, traffic)
"""

PINECONE_API_KEY = "your-pinecone-api-key"
PINECONE_INDEX   = "rls-logistics-hubs"

TIMESCALE_DSN = "postgresql://rls_user:rls_pass@localhost:5432/rls_logistics"
