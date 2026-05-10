"""NPC conversation manager with context-aware dialogue."""

from __future__ import annotations

import logging
from typing import Any

from game_engine.ollama_bridge import OllamaBridge

logger = logging.getLogger("tavern.conversation")


class ConversationManager:
    """Manages NPC dialogue with context, memory, and personality."""

    def __init__(self, ollama: OllamaBridge) -> None:
        self.ollama = ollama

    async def generate_response(
        self,
        npc_name: str,
        npc_personality: str,
        npc_role: str,
        player_message: str,
        conversation_history: list[dict],
        npc_memory: list[dict],
        world_context: dict[str, Any],
    ) -> str:
        """Generate a contextual NPC response."""
        memory_summary = self._summarize_memory(npc_memory)
        recent_history = conversation_history[-6:] if conversation_history else []

        system_prompt = f"""Eres {npc_name}, {npc_role} en este mundo.
        
        Personalidad: {npc_personality}
        
        Reglas:
        - Responde EN PERSONAJE, siempre.
        - Usa el contexto de la conversación para respuestas coherentes.
        - Reacciona a las acciones y decisiones del jugador.
        - Puedes revelar información, hacer peticiones, o guardar secretos.
        - No rompas la cuarta pared.
        - Mantén respuestas con una extensión natural (2-4 párrafos)."""

        user_prompt = f"""
        Contexto mundial: {json.dumps(world_context)}
        Tu memoria relevante: {memory_summary}
        Historial reciente: {json.dumps(recent_history)}
        
        Mensaje del jugador: {player_message}
        """

        return await self.ollama.generate(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            temperature=0.8,
        )

    async def generate_conversation_options(
        self,
        npc_name: str,
        npc_role: str,
        context: dict[str, Any],
    ) -> list[str]:
        """Generate suggested conversation topics/options."""
        system_prompt = f"""Genera 3-4 opciones de diálogo realistas que el 
        jugador podría decirle a {npc_name} ({npc_role}). 
        Responde ÚNICAMENTE con un array JSON de strings."""

        result = await self.ollama.generate(
            system_prompt=system_prompt,
            user_prompt=f"Contexto: {json.dumps(context)}",
            structured=True,
            temperature=0.7,
        )

        if isinstance(result, list):
            return result
        return []

    def _summarize_memory(self, memory: list[dict]) -> str:
        """Summarize NPC memory for context window efficiency."""
        if not memory:
            return "No has interactuado antes con este viajero."
        recent = memory[-5:]
        return " | ".join(
            f"{m.get('event', '')}: {m.get('detail', '')}" for m in recent
        )


import json
