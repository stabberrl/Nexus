"""
Nexus AI - Task Planner
Descompone tareas complejas en sub-tareas y las asigna a agentes especializados.
"""

import json
import httpx
from typing import Optional


OLLAMA_URL = "http://localhost:11434/api/chat"
PLANNER_MODEL = "llama3.2"


class TaskPlanner:
    """
    Planificador que descompone comandos complejos en tareas atómicas
    y las asigna al agente especializado correcto.
    """

    AGENT_TYPES = {
        "system": "Control del PC: abrir apps, ejecutar comandos, gestionar archivos",
        "web": "Navegación web: búsquedas, extraer contenido de páginas",
        "code": "Ejecución de código: scripts Python, análisis de datos",
        "documents": "Creación de documentos: Word, Excel, presentaciones",
        "assistant": "Asistencia general: responder preguntas, conversación",
    }

    async def plan(self, user_request: str) -> list[dict]:
        """
        Analiza el request del usuario y devuelve un plan con tareas.
        """
        agent_descriptions = "\n".join(f"- {k}: {v}" for k, v in self.AGENT_TYPES.items())
        prompt = f"""
Asigna el request del usuario al agente correcto. Tipos de agente:
{agent_descriptions}

Responde SOLO con JSON exactamente en este formato, nada mas:
[{{"description": "descripcion corta", "agent": "tipo"}}]

Reglas:
- Si pregunta por sistema/PC/archivos/procesos -> agent: system
- Si pide buscar en internet/pagina web -> agent: web
- Si pide ejecutar codigo/analisis de datos -> agent: code
- Si pide crear documentos Word/Excel -> agent: documents
- Si es saludo/pregunta general -> agent: assistant

Request: {user_request}
JSON:"""

        async with httpx.AsyncClient(timeout=180.0) as client:
            try:
                response = await client.post(OLLAMA_URL, json={
                    "model": PLANNER_MODEL,
                    "messages": [{"role": "user", "content": prompt}],
                    "stream": False,
                    "options": {"temperature": 0.1},
                })
            except httpx.TimeoutException:
                return [{"description": user_request, "agent": "assistant"}]

            if response.status_code != 200:
                return [{"description": user_request, "agent": "assistant"}]

            try:
                content = response.json()["message"]["content"]
                # Extraer JSON
                json_start = content.find("[")
                json_end = content.rfind("]") + 1
                if json_start >= 0 and json_end > json_start:
                    tasks = json.loads(content[json_start:json_end])
                    # Validar
                    for t in tasks:
                        if "description" not in t:
                            t["description"] = user_request
                        if "agent" not in t or t["agent"] not in self.AGENT_TYPES:
                            t["agent"] = "assistant"
                    return tasks
            except (json.JSONDecodeError, KeyError, IndexError):
                pass

            return [{"description": user_request, "agent": "assistant"}]

    async def plan_with_context(self, user_request: str, context: str = "") -> list[dict]:
        """
        Planifica incluyendo contexto adicional (memoria, historial).
        """
        prompt_with_context = f"{context}\n\nRequest: {user_request}" if context else user_request
        return await self.plan(prompt_with_context)
