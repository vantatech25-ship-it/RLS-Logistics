"""
RLS Logistics — LangGraph Orchestrator
Coordinates: Rust Routing Engine → Pinecone Memory → TimescaleDB → Digital Twin
"""

import os
from dotenv import load_dotenv
from pathlib import Path

# Load environment variables from the root .env file
env_path = Path(__file__).parent.parent / ".env"
load_dotenv(dotenv_path=env_path)

ROUTING_ENGINE_URL = os.getenv("ROUTING_ENGINE_URL", "http://localhost:3000")

