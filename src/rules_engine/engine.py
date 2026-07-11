"""Rules engine core (Phase 8) — Layer 3's procedural inference over Layer 2
facts + Layer 1.5 confidence + patient state.

Layer 3's invariant (docs/IMPLEMENTATION_PLAN.md §3): **all conditional
logic lives here**, never in the knowledge graph (`src/knowledge_graph/`,
which holds only declarative facts). `RuleSet` loads `configs/rules.yaml`
(~50 rules: safety, clinical-guideline, consistency) and evaluates them,
in priority order, against a candidate recommendation + context dict built
from Layers 1, 1.5, and 2's outputs.

Custom YAML-driven engine over Rete/experta is a deliberate stack decision
(docs/IMPLEMENTATION_PLAN.md §3, "Stack decisions"): simple, debuggable,
and consistent with this project's existing config-driven-policy pattern
(`src/models/archetypes.py`, `src/models/cognitive_fable.py`) — clinicians
edit YAML, not code.

`apply_rules()` is the low-level primitive; `src/rules_engine/verification.py`
wraps it into `verify_recommendation()`, the actual Layer 3 entry point used
by the reasoning pipeline (Phase 9) and the `/recommend` endpoint.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class ConditionType(Enum):
    """Kinds of conditions a rule's `conditions` list can contain.

    Each maps to a lookup strategy in `Condition.evaluate`'s context dict —
    see `src/rules_engine/verification.py::verify_recommendation` for how
    that context is assembled from Layers 1/1.5/2 outputs and patient state.
    """

    CONFIDENCE_ABOVE = "confidence_above"  # Layer 1.5 ensemble confidence
    DISTORTION_EQUALS = "distortion_equals"  # Layer 1 candidate distortion
    RIGIDITY_ABOVE = "rigidity_above"  # Layer 1.5 rigidity (modulates, not gates confidence)
    PATIENT_STATE = "patient_state"  # dotted path into patient_context, e.g. "suicidal_risk"
    SESSION_CONSISTENCY = "session_consistency"  # contradiction-with-history check


@dataclass(frozen=True)
class Condition:
    """A single condition within a rule. All conditions in a `Rule` are ANDed."""

    type: ConditionType
    field: str  # dotted path into the evaluation context, e.g. "patient_state.suicidal_risk"
    operator: str  # one of ">", ">=", "<", "<=", "==", "!=", "in"
    value: Any

    def evaluate(self, context: dict[str, Any]) -> bool:
        """Resolve `field` in `context` and compare against `value` via `operator`.

        Args:
            context: the flat/nested evaluation context assembled by
                `verify_recommendation` — candidate recommendation fields,
                patient_context, and any KG query results merged in.

        Returns:
            True if the condition holds; False if it doesn't, INCLUDING when
            `field` is missing from `context` (missing data never silently
            passes a safety condition).

        Raises:
            ValueError: on an unsupported `operator`.
        """
        raise NotImplementedError


@dataclass(frozen=True)
class Action:
    """The effect a rule has when all of its conditions pass."""

    type: str  # "approve" | "flag" | "suggest_alternative" | "escalate"
    params: dict[str, Any] = field(default_factory=dict)  # e.g. {"level": ..., "message": ...}


@dataclass(frozen=True)
class Rule:
    """One rule: identity + ordering + conditions (AND) + the action they trigger."""

    id: str
    name: str
    priority: int  # higher runs first; safety rules should outrank guideline rules
    conditions: list[Condition]
    action: Action
    description: str = ""


class RuleSet:
    """An ordered collection of `Rule`s loaded from `configs/rules.yaml`."""

    def __init__(self) -> None:
        self.rules: list[Rule] = []

    @classmethod
    def from_yaml(cls, rules_yaml: str) -> "RuleSet":
        """Parse `configs/rules.yaml` (or an equivalently shaped file) into a `RuleSet`.

        Args:
            rules_yaml: path to a YAML file shaped like `configs/rules.yaml`
                (top-level `rules:` list; see that file's comments for the
                per-rule shape).

        Returns:
            A `RuleSet` with `rules` sorted by `priority`, descending.

        Raises:
            FileNotFoundError: if `rules_yaml` does not exist.
            ValueError: on a malformed rule (unknown `ConditionType`,
                missing required fields, duplicate `id`).
        """
        raise NotImplementedError

    def apply(
        self,
        recommendation: dict[str, Any],
        context: dict[str, Any],
    ) -> list[tuple[Rule, bool, str]]:
        """Evaluate every rule against `recommendation` + `context`, in priority order.

        Args:
            recommendation: the candidate recommendation under verification
                (distortion, technique, confidence, rigidity — see
                `src/rules_engine/verification.py::verify_recommendation`).
            context: patient_context plus any KG query results merged in by
                the caller.

        Returns:
            One (rule, passed, explanation) tuple per rule in `self.rules`,
            in priority order. `explanation` is a short human-readable
            string suitable for `VerifiedRecommendation.reasoning_chain`
            (e.g. "safety_suicidality_contraindication: PASSED — no
            suicidal_risk signal above 0.7").

        Note:
            This returns ALL rules' outcomes (not first-match-wins) — Layer
            3's auditability guarantee (docs/IMPLEMENTATION_PLAN.md §3)
            requires every rule's verdict to be inspectable, not just the
            one that changed the final decision. `verify_recommendation`
            decides how to fold this list into approve/flag/escalate.
        """
        raise NotImplementedError


def apply_rules(
    text: str,
    state: dict[str, Any],
    rules: RuleSet,
) -> list[tuple[str, bool, str]]:
    """Module-level convenience wrapper matching the
    `apply_rules(text, state, rules)` signature referenced in
    docs/IMPLEMENTATION_PLAN.md §4 (Phase 8): builds a minimal
    recommendation/context pair from raw `text` + `state` (no Layer 2 query)
    and delegates to `RuleSet.apply`. Intended for the Phase 8 unit tests
    that exercise rules without a live knowledge graph (mocked KG queries).

    Returns:
        (rule_id, passed, explanation) tuples — the `Rule` objects
        themselves are not needed by callers using this entry point.
    """
    raise NotImplementedError
