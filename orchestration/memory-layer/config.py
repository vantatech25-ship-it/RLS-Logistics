"""
RLS Logistics — Memory Layer
Manages:
  - Pinecone: vector embeddings for hub/route spatial memory
  - TimescaleDB: time-series telemetry (GPS pings, load, traffic)
"""

import os
from dotenv import load_dotenv
from pathlib import Path

# Load environment variables from the root .env file
env_path = Path(__file__).parent.parent.parent / ".env"
load_dotenv(dotenv_path=env_path)

PINECONE_API_KEY = os.getenv("PINECONE_API_KEY", "your-pinecone-api-key")
PINECONE_INDEX   = os.getenv("PINECONE_INDEX", "rls-logistics-hubs")

TIMESCALE_DSN = os.getenv("TIMESCALE_DSN", "postgresql://rls_user:rls_pass@localhost:5432/rls_logistics")

