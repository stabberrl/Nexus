"""Bridge to Ollama local LLM for prompt execution and structured output parsing."""

from __future__ import annotations

import json
import logging
from typing import Any

import httpx

logger = logging.getLogger("tavern.ollama")

OLLAMA_BASE_URL = "http://localhost:11434"
DEFAULT_MODEL = "llama3.2"
MAX_RETRIES = 3


class OllamaBridge:
    """Handles communication with the local Ollama instance."""

    def __init__(self, model: str = DEFAULT_MODEL) -> None:
        self.model = model
        self.client = httpx.AsyncClient(
            base_url=OLLAMA_BASE_URL,
            timeout=httpx.Timeout(120.0),
        )

    async def generate(
        self,
        system_prompt: str,
        user_prompt: str,
        structured: bool = False,
        schema: dict | None = None,
        temperature: float = 0.7,
    ) -> str | dict[str, Any]:
        """Send a prompt to Ollama and return the response.

        Args:
            system_prompt: System-level instruction for the model.
            user_prompt: The user's input/message.
            structured: If True, attempt to parse response as JSON.
            schema: Optional JSON schema for structured output.
            temperature: Creativity level (0.0-1.0).

        Returns:
            Raw text string or parsed JSON dict.
        """
        payload: dict[str, Any] = {
            "model": self.model,
            "system": system_prompt,
            "prompt": user_prompt,
            "stream": False,
            "options": {
                "temperature": temperature,
            },
        }

        if structured:
            payload["format"] = "json"

        for attempt in range(MAX_RETRIES):
            try:
                response = await self.client.post("/api/generate", json=payload)
                response.raise_for_status()
                data = response.json()
                text = data.get("response", "")

                if structured:
                    return self._parse_json(text, schema)
                return text

            except httpx.TimeoutException:
                logger.warning(
                    "Ollama timeout (attempt %d/%d)", attempt + 1, MAX_RETRIES
                )
                if attempt == MAX_RETRIES - 1:
                    raise
            except httpx.HTTPStatusError as error:
                logger.error("Ollama error: %s", error)
                raise
            except json.JSONDecodeError as error:
                logger.error("Failed to parse JSON: %s", error)
                if not structured:
                    return text
                raise

        msg = "Max retries exceeded"
        raise RuntimeError(msg)

    def _parse_json(
        self, text: str, schema: dict | None = None
    ) -> dict[str, Any]:
        """Extract and validate JSON from model output."""
        # Try direct parse first
        try:
            data = json.loads(text)
            if schema and not self._validate_schema(data, schema):
                logger.warning("Response does not match expected schema")
            return data
        except json.JSONDecodeError:
            pass

        # Try to extract JSON from markdown code block
        import re

        match = re.search(r"```(?:json)?\s*([\s\S]*?)```", text)
        if match:
            try:
                return json.loads(match.group(1))
            except json.JSONDecodeError:
                pass

        msg = f"Could not parse JSON from response: {text[:200]}"
        raise ValueError(msg)

    def _validate_schema(self, data: dict, schema: dict) -> bool:
        """Basic schema validation for required top-level keys."""
        if "required" in schema:
            for key in schema["required"]:
                if key not in data:
                    return False
        return True

    async def check_health(self) -> bool:
        """Check if Ollama is running and has the model."""
        try:
            response = await self.client.get("/api/tags")
            response.raise_for_status()
            models = response.json().get("models", [])
            return any(m["name"].startswith(self.model) for m in models)
        except Exception:
            return False

    async def close(self) -> None:
        await self.aclose()

    async def aclose(self) -> None:
        await self.client.aclose()
