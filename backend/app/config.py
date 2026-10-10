"""
Configuration settings for MetaOracle backend.
"""

import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent.parent
APP_NAME = "MetaOracle Metamorphic Testing Studio"
DB_PATH = BASE_DIR / "metaoracle.db"

DATABASE_URL = os.getenv("DATABASE_URL", f"sqlite:///{DB_PATH}")
HOST = os.getenv("HOST", "127.0.0.1")
PORT = int(os.getenv("PORT", "8000"))
DEBUG = os.getenv("DEBUG", "True").lower() in ("true", "1", "t")
CORS_ORIGINS = ["*"]
TEST_TIMEOUT_SECONDS = float(os.getenv("TEST_TIMEOUT_SECONDS", "3.0"))
DEFAULT_SEED = int(os.getenv("RANDOM_SEED", "42"))
