"""Dialogue module tests — backend interface + config wiring, no API calls."""

import pytest

from src.models.reframing_dialogue import LoRABackend, ReframingBackend
from src.utils.config import load_config


class FakeBackend(ReframingBackend):
    """Interface conformance check + reusable test double."""

    def generate(self, distortion_profile, user_text, history):
        strongest = max(distortion_profile, key=distortion_profile.get)
        return f"socratic-question-about-{strongest}"


def test_backend_interface():
    backend = FakeBackend()
    reply = backend.generate(
        {"all_or_nothing": 0.9, "mind_reading": 0.1},
        "I always ruin everything",
        [],
    )
    assert reply == "socratic-question-about-all_or_nothing"


def test_lora_backend_is_explicitly_unavailable():
    """LoRABackend must fail loudly, not silently degrade (no GPU confirmed)."""
    with pytest.raises(NotImplementedError):
        LoRABackend()


def test_dialogue_config_selects_valid_backend():
    cfg = load_config("dialogue")
    assert cfg["backend"] in ("prompt", "lora")
    assert cfg["prompt_backend"]["max_questions_per_turn"] >= 1
