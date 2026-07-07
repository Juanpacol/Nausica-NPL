"""Single LLM client for the whole project — provider-agnostic.

Every module that talks to an LLM (weak labeling, dialogue expansion, PromptBackend,
LLM-judge) goes through here — one place for auth, retries, token accounting, and
JSON extraction. Do not instantiate SDK/HTTP clients elsewhere.

Providers (configs/data.yaml -> llm.provider, overridable via NAUSICA_LLM_PROVIDER):
- "ollama"    — local server at http://127.0.0.1:11434, free, no API key, no data
                leaves the machine (default; fits the project's local-first story).
- "anthropic" — Claude API; requires ANTHROPIC_API_KEY in .env. Higher quality for
                dialogue generation; costs tokens.
"""

from __future__ import annotations

import json
import os
import re
import time
import urllib.error
import urllib.request

from dotenv import load_dotenv

from src.utils.logging_config import get_logger

logger = get_logger(__name__)

load_dotenv()

OLLAMA_URL = os.environ.get("OLLAMA_URL", "http://127.0.0.1:11434")

# qwen3-style thinking blocks must never leak into outputs we parse or store
_THINK_RE = re.compile(r"<think>.*?</think>", re.DOTALL)


class LLMClient:
    def __init__(self, model: str, max_tokens: int = 1024, provider: str | None = None):
        if provider is None:
            provider = os.environ.get("NAUSICA_LLM_PROVIDER")
        if provider is None:
            from src.utils.config import load_config

            provider = load_config("data").get("llm", {}).get("provider", "ollama")
        self.provider = provider
        self.max_tokens = max_tokens
        self.input_tokens = 0
        self.output_tokens = 0

        if self.provider == "anthropic":
            api_key = os.environ.get("ANTHROPIC_API_KEY")
            if not api_key:
                raise EnvironmentError(
                    "provider=anthropic but ANTHROPIC_API_KEY is not set. "
                    "Fill .env or switch to the free local provider (ollama)."
                )
            import anthropic

            self._client = anthropic.Anthropic(api_key=api_key)
            self.model = model
        elif self.provider == "ollama":
            self.model = model
            self._assert_ollama_up()
        else:
            raise ValueError(f"Unknown LLM provider: {self.provider!r} (ollama|anthropic)")

        logger.info("LLM client: provider=%s model=%s", self.provider, self.model)

    # ------------------------------------------------------------- public API

    def complete(
        self,
        prompt: str,
        system: str | None = None,
        retries: int = 3,
        json_mode: bool = False,
    ) -> str:
        """One-shot completion with basic exponential-backoff retry."""
        for attempt in range(retries):
            try:
                if self.provider == "anthropic":
                    return self._complete_anthropic(prompt, system)
                return self._complete_ollama(prompt, system, json_mode=json_mode)
            except Exception as e:  # noqa: BLE001 — transient network/server errors
                if attempt == retries - 1:
                    raise
                wait = 2**attempt
                logger.warning("LLM call failed (%s), retrying in %ss", e, wait)
                time.sleep(wait)
        raise RuntimeError("unreachable")

    def complete_json(self, prompt: str, system: str | None = None) -> dict | list:
        """Completion that must return JSON; extracts the first JSON object/array.

        On Ollama this uses the server's constrained JSON decoding (format=json),
        which guarantees syntactically valid output from local models.
        """
        text = self.complete(prompt, system=system, json_mode=True)
        match = re.search(r"\{.*\}|\[.*\]", text, re.DOTALL)
        if not match:
            raise ValueError(f"No JSON found in LLM response: {text[:200]!r}")
        return json.loads(match.group(0))

    def usage_summary(self) -> str:
        return (
            f"provider={self.provider} tokens in={self.input_tokens} "
            f"out={self.output_tokens} model={self.model}"
        )

    # ---------------------------------------------------------------- backends

    def _complete_anthropic(self, prompt: str, system: str | None) -> str:
        kwargs: dict = {
            "model": self.model,
            "max_tokens": self.max_tokens,
            "messages": [{"role": "user", "content": prompt}],
        }
        if system:
            kwargs["system"] = system
        response = self._client.messages.create(**kwargs)
        self.input_tokens += response.usage.input_tokens
        self.output_tokens += response.usage.output_tokens
        return response.content[0].text

    def _complete_ollama(self, prompt: str, system: str | None, json_mode: bool = False) -> str:
        messages = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": prompt})
        payload = {
            "model": self.model,
            "messages": messages,
            "stream": False,
            "think": False,  # disable qwen3 thinking mode; ignored by other models
            "options": {"num_predict": self.max_tokens, "temperature": 0.7},
        }
        if json_mode:
            payload["format"] = "json"  # server-side constrained decoding
        body = self._post_json(f"{OLLAMA_URL}/api/chat", payload, timeout=600)
        self.input_tokens += body.get("prompt_eval_count", 0)
        self.output_tokens += body.get("eval_count", 0)
        text = body["message"]["content"]
        return _THINK_RE.sub("", text).strip()

    # ------------------------------------------------------------------ helpers

    @staticmethod
    def _post_json(url: str, payload: dict, timeout: int) -> dict:
        req = urllib.request.Request(
            url,
            data=json.dumps(payload).encode(),
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return json.loads(resp.read())

    @staticmethod
    def _assert_ollama_up() -> None:
        try:
            with urllib.request.urlopen(f"{OLLAMA_URL}/api/tags", timeout=5):
                pass
        except (urllib.error.URLError, OSError) as e:
            raise EnvironmentError(
                f"Ollama server not reachable at {OLLAMA_URL}. Start it with: ollama serve"
            ) from e
