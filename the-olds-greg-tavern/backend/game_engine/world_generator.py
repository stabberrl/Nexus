"""Procedural world generation through LLM conversation and structured prompts."""

from __future__ import annotations

from game_engine.models import World
from game_engine.ollama_bridge import OllamaBridge


class WorldGenerator:
    """Generates and evolves game worlds using LLM."""

    def __init__(self, ollama: OllamaBridge) -> None:
        self.ollama = ollama

    async def create_world_from_conversation(
        self, player_idea: str
    ) -> World:
        """Generate a full world from the player's initial description."""
        system_prompt = """Eres un creador de mundos para un RPG narrativo. 
        A partir de la idea del jugador, genera un mundo coherente con:
        - Nombre del mundo
        - Descripción general
        - Ambientación (fantasía, cyberpunk, etc.)
        - Tono (épico, oscuro, humorístico, etc.)
        - 4-6 locaciones iniciales con nombre, descripción y tipo
        - 3-5 NPCs clave con nombre, rol y personalidad
        - 2-3 facciones o grupos importantes
        - Una situación inicial que enganche al jugador
        
        Responde ÚNICAMENTE con JSON válido, sin texto adicional."""

        schema = {
            "world_name": "string",
            "description": "string",
            "setting": "string",
            "tone": "string",
            "locations": "array",
            "npcs": "array",
            "factions": "array",
            "initial_situation": "string",
        }

        data = await self.ollama.generate(
            system_prompt=system_prompt,
            user_prompt=f"Idea del jugador: {player_idea}",
            structured=True,
            schema=schema,
            temperature=0.8,
        )

        return self._parse_world(data)

    def _parse_world(self, data: dict) -> World:
        """Convert LLM response into World model."""
        return World(
            name=data.get("world_name", "Mundo Sin Nombre"),
            description=data.get("description", ""),
            setting=data.get("setting", "fantasía"),
            tone=data.get("tone", "épico"),
        )
