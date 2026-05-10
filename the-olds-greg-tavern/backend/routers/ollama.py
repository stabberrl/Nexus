"""Ollama management and proxy routes."""

from __future__ import annotations

import logging

from fastapi import APIRouter, HTTPException

from game_engine.ollama_bridge import OllamaBridge, OLLAMA_BASE_URL

logger = logging.getLogger("tavern.ollama")

ollama = OllamaBridge()
router = APIRouter(prefix="/api/ollama", tags=["ollama"])


@router.get("/health")
async def check_ollama() -> dict:
    """Check if Ollama is running and has the model."""
    try:
        healthy = await ollama.check_health()
        return {"healthy": healthy, "model": ollama.model, "url": OLLAMA_BASE_URL}
    except Exception as error:
        return {"healthy": False, "error": str(error), "model": ollama.model}


@router.get("/models")
async def list_models() -> dict:
    """List available models in Ollama."""
    try:
        import httpx

        async with httpx.AsyncClient(base_url=OLLAMA_BASE_URL) as client:
            response = await client.get("/api/tags")
            response.raise_for_status()
            return response.json()
    except Exception as error:
        logger.error("Failed to list models: %s", error)
        raise HTTPException(status_code=503, detail=str(error)) from error
