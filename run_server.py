"""
MetaOracle Server Launcher.
Starts the FastAPI backend server with Uvicorn, initializes SQLite database,
and serves the Single Page Application frontend at http://127.0.0.1:8000.
"""

import sys
import os
from pathlib import Path

# Fix Windows console encoding for UTF-8 characters if needed
if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

import uvicorn

# Ensure project root is in sys.path
BASE_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(BASE_DIR))

from backend.app.config import HOST, PORT, DEBUG, APP_NAME
from backend.app.database.session import init_db


def main():
    print("=" * 70)
    print(f"  [METAORACLE] {APP_NAME.upper()}")
    print("=" * 70)
    print("  Initializing SQLite database & schema...")
    init_db()
    print("  Database ready: metaoracle.db")
    print(f"  Starting server at:   http://{HOST}:{PORT}")
    print(f"  Interactive API Docs: http://{HOST}:{PORT}/docs")
    print(f"  Web Dashboard UI:     http://{HOST}:{PORT}/")
    print("=" * 70)
    print("  Press Ctrl+C to stop the server.\n")

    uvicorn.run(
        "backend.app.main:app",
        host=HOST,
        port=PORT,
        reload=DEBUG,
        log_level="info",
    )


if __name__ == "__main__":
    main()
