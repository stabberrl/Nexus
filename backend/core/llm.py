"""
Nexus AI - LLM Engine
Cliente para modelos locales via Ollama con soporte de tool calling y streaming.
"""

import json
import httpx
from typing import AsyncGenerator, Optional


OLLAMA_BASE_URL = "http://localhost:11434"
# Modelo ligero por defecto (3B). Cambiar a "llama3.1:8b" para más capacidad.
DEFAULT_MODEL = "llama3.2"
HEAVY_MODEL = "llama3.1:8b"


class ToolDefinition:
    """Define una herramienta que el LLM puede llamar."""

    def __init__(self, name: str, description: str, parameters: dict, handler: callable):
        self.name = name
        self.description = description
        self.parameters = parameters
        self.handler = handler

    def to_openai_tool(self) -> dict:
        """Convierte a formato tool compatible con Ollama."""
        return {
            "type": "function",
            "function": {
                "name": self.name,
                "description": self.description,
                "parameters": self.parameters,
            },
        }


class LLMEngine:
    """Motor de lenguaje que conecta con Ollama para inferencia local."""

    def __init__(self, model: str = DEFAULT_MODEL):
        self.model = model
        self.base_url = OLLAMA_BASE_URL
        self.tools: dict[str, ToolDefinition] = {}
        self.conversation_history: list[dict] = []

    def register_tool(self, tool: ToolDefinition):
        """Registra una herramienta que el LLM puede invocar."""
        self.tools[tool.name] = tool

    def _build_messages(self, user_message: str) -> list[dict]:
        """Construye el array de mensajes incluyendo historial."""
        messages = [{"role": "system", "content": self._system_prompt()}]
        messages.extend(self.conversation_history[-20:])  # Últimos 20 intercambios
        messages.append({"role": "user", "content": user_message})
        return messages

    def _system_prompt(self) -> str:
        return (
            "Te llamas Nexus. Eres un asistente de IA avanzado que controla el PC del usuario. "
            "Puedes ejecutar comandos, abrir aplicaciones, navegar por internet, "
            "crear documentos, y coordinar agentes especializados. "
            "Responde en español de forma natural y util. "
            "Cuando necesites realizar una accion, usa las herramientas disponibles. "
            "Se proactivo y sugiere cosas utiles que puedas hacer."
        )

    async def chat_stream(
        self, user_message: str, model: Optional[str] = None
    ) -> AsyncGenerator[str, None]:
        """
        Chat con streaming de tokens. Ejecuta tools automáticamente
        y devuelve la respuesta final.
        """
        use_model = model or self.model
        messages = self._build_messages(user_message)
        tool_defs = [t.to_openai_tool() for t in self.tools.values()]

        # Round 1: LLM genera respuesta o decide llamar a una tool
        payload = {
            "model": use_model,
            "messages": messages,
            "stream": True,
            "tools": tool_defs if tool_defs else None,
        }

        result_text = ""
        tool_calls = []
        client = httpx.AsyncClient(timeout=300.0)

        try:
            async with client.stream(
                "POST", f"{self.base_url}/api/chat", json=payload
            ) as response:
                async for line in response.aiter_lines():
                    if not line.strip():
                        continue
                    try:
                        chunk = json.loads(line)
                    except json.JSONDecodeError:
                        continue

                    if "message" in chunk:
                        msg = chunk["message"]
                        content = msg.get("content", "")

                        # Procesar tool calls
                        if "tool_calls" in msg:
                            for tc in msg["tool_calls"]:
                                tool_calls.append(tc)

                        if content:
                            result_text += content
                            yield content

                    if chunk.get("done"):
                        break

            # Si hay tool calls, ejecutarlas y hacer un segundo round
            if tool_calls:
                tool_results = await self._execute_tool_calls(tool_calls)
                yield f"\n\n**[Ejecutando {len(tool_calls)} accion(es)...]**\n\n"

                messages.append({"role": "assistant", "content": result_text, "tool_calls": tool_calls})
                for tr in tool_results:
                    messages.append({
                        "role": "tool",
                        "content": json.dumps(tr["result"], ensure_ascii=False),
                        "name": tr["name"],
                    })

                payload2 = {
                    "model": use_model,
                    "messages": messages,
                    "stream": True,
                }
                async with client.stream(
                    "POST", f"{self.base_url}/api/chat", json=payload2
                ) as response:
                    async for line in response.aiter_lines():
                        if not line.strip():
                            continue
                        try:
                            chunk = json.loads(line)
                        except json.JSONDecodeError:
                            continue
                        content = chunk.get("message", {}).get("content", "")
                        if content:
                            result_text += content
                            yield content
                        if chunk.get("done"):
                            break
        finally:
            await client.aclose()

        # Guardar en historial
        self.conversation_history.append({"role": "user", "content": user_message})
        self.conversation_history.append({"role": "assistant", "content": result_text})

    async def _execute_tool_calls(self, tool_calls: list) -> list[dict]:
        """Ejecuta las tools solicitadas por el LLM y devuelve resultados."""
        results = []
        for tc in tool_calls:
            func_name = tc.get("function", {}).get("name", "")
            func_args = tc.get("function", {}).get("arguments", {})

            if isinstance(func_args, str):
                try:
                    func_args = json.loads(func_args)
                except json.JSONDecodeError:
                    func_args = {}

            if func_name in self.tools:
                tool = self.tools[func_name]
                try:
                    result = await tool.handler(**func_args)
                    results.append({"name": func_name, "result": {"success": True, "data": result}})
                except Exception as e:
                    results.append({"name": func_name, "result": {"success": False, "error": str(e)}})
            else:
                results.append({"name": func_name, "result": {"success": False, "error": f"Tool '{func_name}' no encontrada"}})

        return results

    async def chat(self, user_message: str, model: Optional[str] = None) -> str:
        """Chat sin streaming, devuelve texto completo."""
        chunks = []
        async for chunk in self.chat_stream(user_message, model):
            chunks.append(chunk)
        return "".join(chunks)

    def clear_history(self):
        """Limpia el historial de conversación."""
        self.conversation_history.clear()

    async def list_models(self) -> list[dict]:
        """Lista los modelos disponibles en Ollama."""
        async with httpx.AsyncClient() as client:
            resp = await client.get(f"{self.base_url}/api/tags")
            if resp.status_code == 200:
                return resp.json().get("models", [])
            return []

    async def get_model_info(self, model: str) -> Optional[dict]:
        """Obtiene información de un modelo específico."""
        async with httpx.AsyncClient() as client:
            resp = await client.post(
                f"{self.base_url}/api/show",
                json={"name": model},
            )
            if resp.status_code == 200:
                return resp.json()
            return None
