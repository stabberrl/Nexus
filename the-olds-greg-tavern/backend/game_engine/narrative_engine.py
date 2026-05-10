from __future__ import annotations

import logging
from typing import Any

from game_engine.ollama_bridge import OllamaBridge

logger = logging.getLogger("tavern.narrative")


class NarrativeEngine:
    """Manages narrative state, scene descriptions, and story progression."""

    def __init__(self, ollama: OllamaBridge) -> None:
        self.ollama = ollama

    async def describe_scene(
        self,
        location_name: str,
        location_desc: str,
        npcs_present: list[str],
        recent_history: list[str],
        player_action: str | None = None,
    ) -> str:
        """Generate a rich narrative description of the current scene."""
        context = f"""
        Location: {location_name}
        Description: {location_desc}
        NPCs present: {', '.join(npcs_present) if npcs_present else 'None'}
        Recent events: {' | '.join(recent_history[-3:]) if recent_history else 'New arrival'}
        Player action: {player_action or 'Looking around'}
        """

        system_prompt = """Eres el narrador de un RPG. Describe escenas de forma 
        vívida e inmersiva usando texto enriquecido. Usa lenguaje evocador pero 
        conciso. Termina con una pregunta o gancho que invite al jugador a actuar."""

        return await self.ollama.generate(
            system_prompt=system_prompt,
            user_prompt=f"Describe esta escena: {context}",
            temperature=0.8,
        )

    async def resolve_action(
        self,
        action: str,
        context: dict[str, Any],
    ) -> dict[str, Any]:
        """Determine the outcome of a player action."""
        system_prompt = """Eres un motor de física narrativa para un RPG. 
        Determina el resultado de las acciones del jugador de forma coherente 
        con el mundo. Responde ÚNICAMENTE con JSON:
        {
            "success": true/false,
            "narrative": "descripción del resultado",
            "consequences": ["lista de cambios en el mundo"],
            "suggested_actions": ["posibles siguientes pasos"]
        }"""

        return await self.ollama.generate(
            system_prompt=system_prompt,
            user_prompt=f"Contexto: {json.dumps(context)}\nAcción: {action}",
            structured=True,
            temperature=0.7,
        )

    async def progress_time(
        self,
        turns: int,
        world_state: dict[str, Any],
    ) -> str:
        """Generate time progression narrative."""
        system_prompt = """Eres un narrador RPG. Describe el paso del tiempo 
        en el mundo, eventos que ocurren entre bastidores y cambios en el 
        ambiente. Mantén la coherencia con el estado actual del mundo."""

        return await self.ollama.generate(
            system_prompt=system_prompt,
            user_prompt=f"Han pasado {turns} turnos. Estado del mundo: {json.dumps(world_state)}",
            temperature=0.7,
        )


import json
