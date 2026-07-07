"""Socratic reframing dialogue module (Phase 4) — pluggable backend.

`ReframingBackend` is the single interface the rest of the system depends on.
- PromptBackend: Anthropic API with a structured CBT/Socratic system prompt. Default,
  zero GPU. Conditioned on the distortion profile detected by the classifier.
- LoRABackend: placeholder for a QLoRA fine-tuned open model — intentionally
  unimplemented until GPU access is confirmed (see CLAUDE.md).

Backend selection lives in configs/dialogue.yaml, not in code.
"""

from __future__ import annotations

from abc import ABC, abstractmethod

from src.utils.config import load_config
from src.utils.logging_config import get_logger

logger = get_logger(__name__)

SOCRATIC_SYSTEM_PROMPT = """You are a counselor practicing Cognitive Behavioral Therapy, \
specialized in Socratic questioning and the downward-arrow technique. You are part of a \
research prototype — you never diagnose, never mention disorders, never give medical advice.

The client's latest message shows these detected cognitive distortion signals (0-1):
{distortion_profile}

Your task for this single turn:
- Address the STRONGEST detected distortion, implicitly (never name the distortion or \
use clinical jargon with the client).
- Ask at most {max_questions} open Socratic question(s) that invite the client to examine \
evidence, exceptions, or alternative framings of their belief.
- Warm, natural, brief (2-4 sentences). Never lecture, never give direct advice, never \
dismiss the feeling.
- If the client expresses intent of self-harm or harm to others, drop the technique and \
respond only with empathic acknowledgement plus a recommendation to seek immediate \
professional help or a local crisis line.

Respond with the counselor's next message only — no meta-commentary."""


class ReframingBackend(ABC):
    @abstractmethod
    def generate(
        self,
        distortion_profile: dict[str, float],
        user_text: str,
        history: list[dict[str, str]],
        exemplars: list[dict] | None = None,
    ) -> str:
        """Produce the counselor's next turn.

        history: [{"role": "client"|"counselor", "text": ...}, ...] (oldest first)
        exemplars: optional RAG few-shots — past exchanges of THIS client where a
        reply measurably lowered CFI (src/models/rag_retrieval.py). May be ignored
        by backends that don't support them.
        """


class PromptBackend(ReframingBackend):
    def __init__(self):
        from src.utils.llm_client import LLMClient

        cfg = load_config("dialogue")["prompt_backend"]
        self._client = LLMClient(model=cfg["model"], max_tokens=cfg["max_tokens"])
        self._max_questions = cfg["max_questions_per_turn"]

    def generate(self, distortion_profile, user_text, history, exemplars=None) -> str:
        profile_str = ", ".join(f"{k}={v:.2f}" for k, v in sorted(
            distortion_profile.items(), key=lambda kv: -kv[1]))
        system = SOCRATIC_SYSTEM_PROMPT.format(
            distortion_profile=profile_str, max_questions=self._max_questions
        )
        if exemplars:
            shots = "\n\n".join(
                f"[client]: {e['client_text']}\n[counselor]: {e['counselor_text']}"
                for e in exemplars
            )
            system += (
                "\n\nApproaches that previously helped THIS client examine similar "
                "beliefs (match their spirit, never copy them verbatim):\n" + shots
            )
        transcript = "\n".join(f"[{t['role']}]: {t['text']}" for t in history)
        prompt = (
            (f"Conversation so far:\n{transcript}\n\n" if transcript else "")
            + f"[client]: {user_text}"
        )
        return self._client.complete(prompt, system=system).strip()


class LoRABackend(ReframingBackend):
    """QLoRA fine-tuned open model. Deliberately unimplemented — do not build this
    until GPU access is confirmed; PromptBackend is the supported path."""

    def __init__(self):
        raise NotImplementedError(
            "LoRABackend requires confirmed GPU access and a trained adapter at "
            "configs/dialogue.yaml:lora_backend.adapter_path. Use backend: prompt."
        )

    def generate(self, distortion_profile, user_text, history, exemplars=None) -> str:  # pragma: no cover
        raise NotImplementedError


def get_backend() -> ReframingBackend:
    """Instantiate the backend selected in configs/dialogue.yaml."""
    choice = load_config("dialogue")["backend"]
    backends = {"prompt": PromptBackend, "lora": LoRABackend}
    if choice not in backends:
        raise ValueError(f"Unknown dialogue backend {choice!r}; expected one of {list(backends)}")
    logger.info("Reframing backend: %s", choice)
    return backends[choice]()
