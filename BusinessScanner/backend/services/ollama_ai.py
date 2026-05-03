"""Ollama local LLM service for business opportunity analysis.

Uses llama3.2 via Ollama API to analyze businesses and suggest
pricing, priorities, and email pitches.
"""

import json
import requests
from typing import Optional, List, Dict, Any
from dataclasses import dataclass


@dataclass
class AnalysisResult:
    """Result from Ollama AI analysis."""
    score: int
    categoria_prioridad: str
    razones: List[str]
    pitch_email: str
    nombre_negocio_limpio: str
    secciones_web: List[str]
    precio_sugerido_clp: int
    precio_sugerido_usd: int


class OllamaService:
    """Service for local LLM analysis via Ollama."""

    def __init__(self, base_url: str = "http://localhost:11434", model: str = "llama3.2") -> None:
        self.base_url = base_url.rstrip("/")
        self.model = model
        self.session = requests.Session()

    def check_ollama_running(self) -> bool:
        """Verify Ollama service is running."""
        try:
            resp = self.session.get(f"{self.base_url}/api/tags", timeout=5)
            return resp.status_code == 200
        except Exception:
            return False

    def analyze_business(
        self, nombre: str, categoria: Optional[str], ciudad: str, telefono: Optional[str]
    ) -> Optional[AnalysisResult]:
        """Analyze a business using Ollama LLM.

        Args:
            nombre: Business name
            categoria: Business category
            ciudad: City name
            telefono: Phone number

        Returns:
            AnalysisResult or None on failure
        """
        if not self.check_ollama_running():
            print("Ollama is not running. Please start: ollama serve")
            return None

        prompt = f"""Eres experto en marketing digital para negocios locales
en Latinoamérica. Analiza y responde ÚNICAMENTE con JSON:
{{
  "score": <0-100>,
  "categoria_prioridad": "",
  "razones": ["", "", ""],
  "pitch_email": "",
  "nombre_negocio_limpio": "",
  "secciones_web": ["inicio","servicios","contacto"],
  "precio_sugerido_clp": ,
  "precio_sugerido_usd": 
}}
Negocio: {nombre} | {categoria or "general"} | {ciudad} | Tel: {telefono or "N/A"}"""

        try:
            resp = self.session.post(
                f"{self.base_url}/api/generate",
                json={"model": self.model, "prompt": prompt, "stream": False},
                timeout=60,
            )
            resp.raise_for_status()
            data = resp.json()
            response_text = data.get("response", "").strip()

            # Extract JSON from response
            json_start = response_text.find("{")
            json_end = response_text.rfind("}") + 1
            if json_start >= 0 and json_end > json_start:
                result = json.loads(response_text[json_start:json_end])
                return AnalysisResult(
                    score=int(result.get("score", 0)),
                    categoria_prioridad=result.get("categoria_prioridad", ""),
                    razones=result.get("razones", []),
                    pitch_email=result.get("pitch_email", ""),
                    nombre_negocio_limpio=result.get("nombre_negocio_limpio", nombre),
                    secciones_web=result.get("secciones_web", ["inicio", "servicios", "contacto"]),
                    precio_sugerido_clp=int(result.get("precio_sugerido_clp", 50000)),
                    precio_sugerido_usd=int(result.get("precio_sugerido_usd", 50)),
                )
            return None
        except Exception as e:
            print(f"Ollama analysis error for {nombre}: {e}")
            return None
