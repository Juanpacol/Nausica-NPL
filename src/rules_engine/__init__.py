"""Layer 3 — Symbolic Rules Engine (Phase 8). See docs/RULES_ENGINE_SPECIFICATION.md.

Public surface: build a `RuleSet` from `configs/rules.yaml`, evaluate it
against a candidate recommendation (`apply_rules`), or go straight to the
Layer 3 entry point that also folds in Layer 2 facts
(`verify_recommendation`). `Condition`/`Action`/`Rule` internals live in
`engine.py` for callers that need finer-grained control (Phase 8 unit
tests, mocked KG).
"""

from __future__ import annotations

from .engine import Action, Condition, RuleSet, apply_rules
from .verification import VerifiedRecommendation, verify_recommendation

__all__ = [
    "RuleSet",
    "Condition",
    "Action",
    "VerifiedRecommendation",
    "apply_rules",
    "verify_recommendation",
]
