"""Dynamic quest and event generation system."""

from __future__ import annotations

import logging
from typing import Any

from game_engine.ollama_bridge import OllamaBridge

logger = logging.getLogger("tavern.quests")


class QuestSystem:
    """Generates and manages quests, events, and random encounters."""

    def __init__(self, ollama: OllamaBridge) -> None:
        self.ollama = ollama

    async def generate_quest(
        self,
        world_context: dict[str, Any],
        location_context: dict[str, Any],
        npcs_available: list[dict],
    ) -> dict[str, Any]:
        """Generate a contextual quest for the player."""
        system_prompt = """Eres un generador de misiones para RPG. Crea una 
        misión coherente con el mundo actual del jugador.
        Responde ÚNICAMENTE con JSON:
        {
            "title": "Nombre de la misión",
            "description": "Descripción y motivación",
            "giver": "NPC que la ofrece",
            "objectives": ["objetivo 1", "objetivo 2"],
            "rewards": ["recompensa 1"],
            "difficulty": "facil/media/dificil",
            "location_hint": "pista de ubicación"
        }"""

        return await self.ollama.generate(
            system_prompt=system_prompt,
            user_prompt=f"Mundo: {json.dumps(world_context)}\n"
            f"Locación: {json.dumps(location_context)}\n"
            f"NPCs disponibles: {json.dumps(npcs_available)}",
            structured=True,
            temperature=0.8,
        )

    async def generate_random_event(
        self,
        world_context: dict[str, Any],
        location_context: dict[str, Any],
    ) -> dict[str, Any]:
        """Generate a random event or encounter."""
        system_prompt = """Eres un generador de eventos aleatorios para RPG. 
        Crea encuentros, descubrimientos o sucesos coherentes con el mundo.
        Responde ÚNICAMENTE con JSON:
        {
            "type": "encuentro/descubrimiento/peligro/comercio",
            "title": "Nombre del evento",
            "description": "Descripción vívida",
            "choices": [
                {"text": "opción A", "difficulty": "facil"},
                {"text": "opción B", "difficulty": "media"}
            ],
            "consequences_hint": "pista de lo que podría pasar"
        }"""

        return await self.ollama.generate(
            system_prompt=system_prompt,
            user_prompt=f"Mundo: {json.dumps(world_context)}\n"
            f"Locación actual: {json.dumps(location_context)}",
            structured=True,
            temperature=0.9,
        )


import json
