"""Procedural location generation and expansion."""

from __future__ import annotations

import logging
from typing import Any

from game_engine.ollama_bridge import OllamaBridge

logger = logging.getLogger("tavern.locations")


class LocationGenerator:
    """Generates and expands locations in the game world."""

    def __init__(self, ollama: OllamaBridge) -> None:
        self.ollama = ollama

    async def generate_location(
        self,
        world_context: dict[str, Any],
        location_type: str = "",
        connected_to: str = "",
    ) -> dict[str, Any]:
        """Generate a new location connected to the world."""
        system_prompt = """Eres un generador de locaciones para RPG. Crea un 
        lugar único y coherente con el mundo.
        Responde ÚNICAMENTE con JSON:
        {
            "name": "Nombre de la locación",
            "description": "Descripción atmosférica y detalles clave",
            "type": "tipo (ciudad/mazmorra/bosque/etc)",
            "npcs": ["posibles NPCs aquí"],
            "secrets": ["secretos por descubrir"],
            "exits": ["hacia dónde se puede ir"],
            "mood": "ambientación emocional"
        }"""

        return await self.ollama.generate(
            system_prompt=system_prompt,
            user_prompt=f"Mundo: {json.dumps(world_context)}\n"
            f"Tipo sugerido: {location_type or 'cualquiera'}\n"
            f"Conectado a: {connected_to or 'nuevo destino'}",
            structured=True,
            temperature=0.8,
        )

    async def expand_location(
        self,
        location: dict[str, Any],
        world_context: dict[str, Any],
    ) -> dict[str, Any]:
        """Add more detail and sub-locations to an existing location."""
        system_prompt = """Expande esta locación con más detalles, lugares de 
        interés dentro de ella, y posibles interacciones.
        Responde ÚNICAMENTE con JSON:
        {
            "points_of_interest": ["lugares dentro"],
            "notable_npcs": ["NPCs adicionales"],
            "ambient_details": "detalles sensoriales adicionales",
            "hidden_areas": ["áreas secretas"],
            "rumors": ["rumores que se escuchan aquí"]
        }"""

        return await self.ollama.generate(
            system_prompt=system_prompt,
            user_prompt=f"Locación: {json.dumps(location)}\n"
            f"Mundo: {json.dumps(world_context)}",
            structured=True,
            temperature=0.8,
        )


import json
