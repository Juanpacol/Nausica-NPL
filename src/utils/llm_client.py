"""Single Anthropic API wrapper for the whole project.

Every module that talks to an LLM (weak labeling, dialogue expansion, PromptBackend,
LLM-judge) goes through here — one place for auth, retries, token accounting, and
JSON extraction. Do not instantiate SDK clients elsewhere.
"""

from __future__ import annotations

import json
import os
import re
import time

from dotenv import load_dotenv

from src.utils.logging_config import get_logger

logger = get_logger(__name__)

load_dotenv()


class LLMClient:
    def __init__(self, model: str, max_tokens: int = 1024):
        api_key = os.environ.get("ANTHROPIC_API_KEY")
        if not api_key:
            raise EnvironmentError(
                "ANTHROPIC_API_KEY is not set. Copy .env.example to .env and fill it in."
            )
        import anthropic

        self._client = anthropic.Anthropic(api_key=api_key)
        self.model = model
        self.max_tokens = max_tokens
        self.input_tokens = 0
        self.output_tokens = 0

    def complete(self, prompt: str, system: str | None = None, retries: int = 3) -> str:
        """One-shot completion with basic exponential-backoff retry."""
        kwargs: dict = {
            "model": self.model,
            "max_tokens": self.max_tokens,
            "messages": [{"role": "user", "content": prompt}],
        }
        if system:
            kwargs["system"] = system

        for attempt in range(retries):
            try:
                response = self._client.messages.create(**kwargs)
                self.input_tokens += response.usage.input_tokens
                self.output_tokens += response.usage.output_tokens
                return response.content[0].text
            except Exception as e:  # noqa: BLE001 — SDK raises many transient types
                if attempt == retries - 1:
                    raise
                wait = 2**attempt
                logger.warning("LLM call failed (%s), retrying in %ss", e, wait)
                time.sleep(wait)
        raise RuntimeError("unreachable")

    def complete_json(self, prompt: str, system: str | None = None) -> dict | list:
        """Completion that must return JSON; extracts the first JSON object/array."""
        text = self.complete(prompt, system=system)
        match = re.search(r"\{.*\}|\[.*\]", text, re.DOTALL)
        if not match:
            raise ValueError(f"No JSON found in LLM response: {text[:200]!r}")
        return json.loads(match.group(0))

    def usage_summary(self) -> str:
        return f"tokens in={self.input_tokens} out={self.output_tokens} model={self.model}"
