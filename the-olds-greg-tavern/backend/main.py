from __future__ import annotations

import logging
import os
from pathlib import Path

import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from routers import game, ollama

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("tavern-backend")

app = FastAPI(title="The Old's Greg Tavern - Backend")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

DATA_DIR = Path(os.getenv("TAVERN_DATA_DIR", str(Path.home() / ".oldstavern")))


@app.on_event("startup")
async def startup() -> None:
    """Ensure data directory exists on startup."""
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    logger.info("Backend started. Data dir: %s", DATA_DIR)


app.include_router(game.router)
app.include_router(ollama.router)


@app.get("/health")
async def health() -> dict:
    """Health check endpoint."""
    return {"status": "ok", "version": "0.1.0"}


if __name__ == "__main__":
    port = int(os.getenv("TAVERN_PORT", "8765"))
    uvicorn.run(app, host="127.0.0.1", port=port, log_level="info")
