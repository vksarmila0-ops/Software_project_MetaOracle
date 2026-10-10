"""
FastAPI application entry point for MetaOracle.
Initializes database, CORS, REST routers, and mounts the modern web frontend.
"""

from contextlib import asynccontextmanager
import os
from pathlib import Path
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from .config import BASE_DIR, APP_NAME, CORS_ORIGINS
from .database.session import init_db
from .api import (
    tests_router,
    relations_router,
    mutation_router,
    benchmark_router,
    snippets_router,
    stats_router,
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Initialize SQLite database and create tables
    init_db()
    yield


app = FastAPI(
    title=APP_NAME,
    description="Full-stack Metamorphic Testing Studio & Automation Framework REST API",
    version="2.0.0",
    lifespan=lifespan,
)

# Enable CORS for frontend flexibility
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register API Routers
app.include_router(tests_router)
app.include_router(relations_router)
app.include_router(mutation_router)
app.include_router(benchmark_router)
app.include_router(snippets_router)
app.include_router(stats_router)


@app.get("/api/health", tags=["System"])
def health_check():
    """Health status endpoint."""
    return {
        "status": "healthy",
        "service": APP_NAME,
        "database": "SQLite (Connected)",
        "version": "2.0.0",
    }


# Static Frontend Mounting
FRONTEND_DIR = BASE_DIR / "frontend"
if FRONTEND_DIR.exists():
    # Mount subdirectories (css, js, assets)
    if (FRONTEND_DIR / "css").exists():
        app.mount("/css", StaticFiles(directory=str(FRONTEND_DIR / "css")), name="css")
    if (FRONTEND_DIR / "js").exists():
        app.mount("/js", StaticFiles(directory=str(FRONTEND_DIR / "js")), name="js")
    if (FRONTEND_DIR / "assets").exists():
        app.mount("/assets", StaticFiles(directory=str(FRONTEND_DIR / "assets")), name="assets")

    @app.get("/", tags=["Frontend"])
    async def serve_index():
        index_file = FRONTEND_DIR / "index.html"
        if index_file.exists():
            return FileResponse(str(index_file))
        return {"message": "MetaOracle API is running. Access API documentation at /docs."}
