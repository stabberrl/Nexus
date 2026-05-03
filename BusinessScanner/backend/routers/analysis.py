"""Analysis router — Ollama business analysis."""
from fastapi import APIRouter
from services.ollama_ai import OllamaService
from models.schemas import OllamaAnalysisRequest

router = APIRouter(prefix="/api/analysis", tags=["analysis"])

@router.post("/analyze")
async def analyze(request: OllamaAnalysisRequest):
    svc = OllamaService()
    result = svc.analyze_business(request.nombre, request.categoria, request.ciudad, request.telefono)
    if not result:
        return {"error": "Analysis failed"}
    return result.__dict__