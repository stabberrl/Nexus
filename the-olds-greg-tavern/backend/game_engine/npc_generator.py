"""NPC generator for procedural character creation."""

from __future__ import annotations

import logging
from typing import Any

from game_engine.ollama_bridge import OllamaBridge

logger = logging.getLogger("tavern.npcs")


class NpcGenerator:
    """Generates NPCs with personalities, backstories, and secrets."""

    def __init__(self, ollama: OllamaBridge) -> None:
        self.ollama = ollama

    async def generate_npc(
        self,
        world_context: dict[str, Any],
        location_context: dict[str, Any],
        role_hint: str = "",
    ) -> dict[str, Any]:
        """Generate a contextual NPC."""
        system_prompt = """Eres un creador de NPCs para RPG. Genera un personaje 
        único con profundidad y potencial narrativo.
        Responde ÚNICAMENTE con JSON:
        {
            "name": "Nombre completo",
            "description": "Apariencia física y presencia",
            "personality": "Rasgos de personalidad detallados",
            "role": "Su función/ocupación",
            "backstory": "Historia breve (2-3 líneas)",
            "secret": "Un secreto que oculta",
            "goals": ["qué quiere lograr"],
            "attitude": "amigable/neutral/hostil",
            "voice": "Cómo habla (formal, rudo, misterioso, etc)"
        }"""

        return await self.ollama.generate(
            system_prompt=system_prompt,
            user_prompt=f"Mundo: {json.dumps(world_context)}\n"
            f"Locación: {json.dumps(location_context)}\n"
            f"Sugerencia de rol: {role_hint or 'cualquiera'}",
            structured=True,
            temperature=0.85,
        )


import json
