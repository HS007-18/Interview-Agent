"""LLM abstraction layer — provider-agnostic interface.

This is the ONLY module that knows about OpenRouter, API keys, or model names.
All other modules call this service and are completely provider-agnostic.
"""

import json
import logging
import re

from openai import AsyncOpenAI

from app import config

logger = logging.getLogger(__name__)


def _parse_json_from_response(raw: str) -> dict:
    """Extract and parse JSON from an LLM response.

    Handles responses wrapped in markdown code fences (```json ... ```).
    """
    # Try direct parse first
    text = raw.strip()
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass

    # Strip markdown code fences
    pattern = r"```(?:json)?\s*\n?(.*?)\n?\s*```"
    match = re.search(pattern, text, re.DOTALL)
    if match:
        try:
            return json.loads(match.group(1).strip())
        except json.JSONDecodeError:
            pass

    # Last resort: find the first { ... } block
    brace_start = text.find("{")
    brace_end = text.rfind("}")
    if brace_start != -1 and brace_end != -1 and brace_end > brace_start:
        try:
            return json.loads(text[brace_start : brace_end + 1])
        except json.JSONDecodeError:
            pass

    logger.error("Failed to parse JSON from LLM response: %s", text[:200])
    raise ValueError(f"Could not parse JSON from LLM response: {text[:200]}")


class LLMService:
    """Provider-agnostic LLM interface.

    Currently backed by OpenRouter (OpenAI-compatible API).
    To swap providers, change the implementation — the interface stays the same.
    """

    def __init__(self) -> None:
        if not config.OPENROUTER_API_KEY:
            raise ValueError(
                "OPENROUTER_API_KEY not set. "
                "Copy .env.example to .env and add your key."
            )
        self.client = AsyncOpenAI(
            base_url=config.OPENROUTER_BASE_URL,
            api_key=config.OPENROUTER_API_KEY,
        )
        self.model = config.LLM_MODEL
        logger.info("LLM Service initialized: model=%s", self.model)

    async def chat(
        self,
        system_prompt: str,
        messages: list[dict[str, str]],
        temperature: float = 0.7,
    ) -> str:
        """Send a conversation to the LLM, return the raw text response.

        Args:
            system_prompt: The system message setting the LLM's behavior.
            messages: Conversation history as [{"role": "user"/"assistant", "content": "..."}].
            temperature: Sampling temperature (0.0 = deterministic, 1.0 = creative).

        Returns:
            The LLM's text response.
        """
        full_messages = [{"role": "system", "content": system_prompt}] + messages

        logger.debug(
            "LLM call: model=%s, messages=%d, temp=%.1f",
            self.model, len(full_messages), temperature,
        )

        response = await self.client.chat.completions.create(
            model=self.model,
            messages=full_messages,
            temperature=temperature,
            max_tokens=1000,
        )

        content = response.choices[0].message.content or ""
        logger.debug("LLM response length: %d chars", len(content))
        return content

    async def chat_json(
        self,
        system_prompt: str,
        messages: list[dict[str, str]],
        temperature: float = 0.7,
    ) -> dict:
        """Send a conversation to the LLM, parse and return JSON response.

        The LLM is expected to respond with valid JSON (possibly wrapped in
        markdown code fences). This method handles extraction and parsing.

        Args:
            system_prompt: The system message setting the LLM's behavior.
            messages: Conversation history.
            temperature: Sampling temperature.

        Returns:
            Parsed JSON as a Python dict.

        Raises:
            ValueError: If the response cannot be parsed as JSON.
        """
        raw = await self.chat(system_prompt, messages, temperature)
        return _parse_json_from_response(raw)


# Module-level singleton — initialized on first import
_instance: LLMService | None = None


def get_llm_service() -> LLMService:
    """Get or create the singleton LLMService instance."""
    global _instance
    if _instance is None:
        _instance = LLMService()
    return _instance
