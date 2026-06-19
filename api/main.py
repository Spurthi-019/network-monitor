# api/main.py
# FastAPI application entry point.
# Run this file to start the web server.

import sys
from pathlib import Path

# Add parent directory to path so imports work when run directly
sys.path.insert(0, str(Path(__file__).parent.parent))

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from logger_setup import setup_logging, get_logger
from api.routes import devices, metrics, alerts
from database.db import create_tables

# ── Initialise logging FIRST ──────────────────────────────────
setup_logging()
logger = get_logger(__name__)

# ── Create FastAPI app ────────────────────────────────────────
app = FastAPI(
    title       = "Network Performance Monitor API",
    description = (
        "REST API for monitoring network latency, "
        "packet loss, and device connectivity. "
        "Built with FastAPI + Python sockets + threading."
    ),
    version     = "1.0.0",
    docs_url    = "/docs",      # Swagger UI at /docs
    redoc_url   = "/redoc",     # ReDoc UI at /redoc
)

# ── CORS middleware ───────────────────────────────────────────
# Allows browsers and frontends to call your API.
# In production, replace "*" with your actual frontend URL.
app.add_middleware(
    CORSMiddleware,
    allow_origins     = ["*"],
    allow_credentials = True,
    allow_methods     = ["*"],
    allow_headers     = ["*"],
)

# ── Register route files ──────────────────────────────────────
# Each router handles a group of endpoints
app.include_router(devices.router)
app.include_router(metrics.router)
app.include_router(alerts.router)


# ── Root endpoint ─────────────────────────────────────────────
@app.get("/", tags=["Root"])
def root():
    """
    GET /

    Health check for the API itself.
    Always returns OK if the server is running.
    """
    logger.info("GET / — API health check")
    return {
        "status":  "online",
        "message": "Network Monitor API is running",
        "docs":    "Visit /docs to explore all endpoints",
        "version": "1.0.0",
    }


# ── Startup event ─────────────────────────────────────────────
@app.on_event("startup")
async def on_startup():
    create_tables()
    logger.info("=" * 50)
    logger.info("Network Monitor API started")
    logger.info("Docs available at: http://localhost:8000/docs")
    logger.info("=" * 50)


# ── Shutdown event ────────────────────────────────────────────
@app.on_event("shutdown")
async def on_shutdown():
    logger.info("Network Monitor API shutting down")


# ── Run the server ────────────────────────────────────────────
# Only executed if you run this file directly (not imported)
if __name__ == "__main__":
    import uvicorn

    logger.info("Starting Network Monitor API server...")
    logger.info("Access the API at: http://localhost:8000")
    logger.info("Interactive docs at: http://localhost:8000/docs")
    logger.info("Press Ctrl+C to stop")

    uvicorn.run(
        app,
        host       = "0.0.0.0",
        port       = 8000,
        log_level  = "info",
    )
