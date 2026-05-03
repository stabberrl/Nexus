"""Configuration module for AgenteWeb.

Loads all environment variables from .env file with type conversion
and provides defaults for the autonomous system.
"""

import os
from pathlib import Path
from typing import Optional, List, Dict

class Config:
    """Application configuration loaded from environment variables."""

    def __init__(self) -> None:
        env_path = Path(__file__).parent.parent / ".env"
        if env_path.exists():
            with open(env_path, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith("#") and "=" in line:
                        key, value = line.split("=", 1)
                        os.environ.setdefault(key.strip(), value.strip())

        self.GMAIL_USER: str = os.getenv("GMAIL_USER", "")
        self.GMAIL_APP_PASSWORD: str = os.getenv("GMAIL_APP_PASSWORD", "")
        self.GITHUB_TOKEN: Optional[str] = os.getenv("GITHUB_TOKEN") or None
        self.MP_ACCESS_TOKEN: Optional[str] = os.getenv("MP_ACCESS_TOKEN") or None
        self.SECRET_KEY: str = os.getenv("SECRET_KEY", "businessscanner2026")
        self.OLLAMA_URL: str = os.getenv("OLLAMA_URL", "http://localhost:11434")
        self.OLLAMA_MODEL: str = os.getenv("OLLAMA_MODEL", "llama3.2")
        self.SCAN_INTERVAL_HOURS: int = int(os.getenv("SCAN_INTERVAL_HOURS", "24"))
        self.MIN_SCORE_TO_CONTACT: int = int(os.getenv("MIN_SCORE_TO_CONTACT", "70"))
        self.MAX_EMAILS_PER_DAY: int = int(os.getenv("MAX_EMAILS_PER_DAY", "50"))

        self.ZONAS_LATAM: List[Dict[str, object]] = [
            {"nombre": "Santiago Centro, Santiago", "lat": -33.4489, "lng": -70.6693},
            {"nombre": "Providencia, Santiago", "lat": -33.4314, "lng": -70.6095},
            {"nombre": "Medellin, Colombia", "lat": 6.2476, "lng": -75.5658},
            {"nombre": "Bogota, Colombia", "lat": 4.7110, "lng": -74.0721},
            {"nombre": "Buenos Aires, Argentina", "lat": -34.6037, "lng": -58.3816},
            {"nombre": "Lima, Peru", "lat": -12.0464, "lng": -77.0428},
            {"nombre": "Ciudad de Mexico, Mexico", "lat": 19.4326, "lng": -99.1332},
            {"nombre": "Monterrey, Mexico", "lat": 25.6866, "lng": -100.3161},
            {"nombre": "Montevideo, Uruguay", "lat": -34.9011, "lng": -56.1645},
            {"nombre": "Quito, Ecuador", "lat": -0.1807, "lng": -78.4678},
        ]

    def get_ollama_url(self) -> str:
        """Get full Ollama API URL for generate endpoint."""
        return f"{self.OLLAMA_URL}/api/generate"

    def get_ollama_model(self) -> str:
        """Get configured Ollama model name."""
        return self.OLLAMA_MODEL


def get_config() -> Config:
    """Factory function to get config instance."""
    return Config()