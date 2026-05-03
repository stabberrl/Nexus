"""AgenteWeb FastAPI main application.

Starts the autonomous scheduler and serves the dashboard API
with CORS enabled for localhost:8080.
"""

import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from scheduler import AutonomousScheduler
from routers import scan, analysis, generator, outreach, payments, dashboard

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[
        logging.FileHandler("C:/BusinessScanner/backend/agenteweb.log", encoding="utf-8"),
        logging.StreamHandler(),
    ],
)

logger = logging.getLogger(__name__)
scheduler = AutonomousScheduler()

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan — startup and shutdown events."""
    logger.info("AgenteWeb starting up...")
    scheduler.start()
    yield
    logger.info("AgenteWeb shutting down...")
    scheduler.stop()

app = FastAPI(
    title="AgenteWeb API",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:8080"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include all routers
app.include_router(scan.router)
app.include_router(analysis.router)
app.include_router(generator.router)
app.include_router(outreach.router)
app.include_router(payments.router)
app.include_router(dashboard.router)

@app.get("/api/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "ok",
        "ollama": scheduler.ollama.check_ollama_running(),
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)