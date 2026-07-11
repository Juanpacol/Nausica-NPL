"""Verification (Phase 8/9) — Layer 3's entry point into the reasoning pipeline.

`verify_recommendation` is where Layer 1.5's confidence signal gates Layer
3's scrutiny (docs/IMPLEMENTATION_PLAN.md §3, Layer 1.5 ensemble
correction): low LLM/temporal confidence should tighten rule thresholds and
set `clinician_review_required = True`, never silently pass a shaky
recommendation through. Rigidity is a modulator of the recommendation
content (e.g. gentler first exposure step), never a confidence input —
that split is enforced by callers passing it separately from `confidence`
in `candidate_recommendation`.

Consumed by `src/models/reasoning_pipeline.py` (Phase 9 orchestration,
Layer 1 -> 1.5 -> 2 -> 3) and, transitively, the `POST /recommend` endpoint
(`src/api/main.py`).
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

from .engine import RuleSet

if TYPE_CHECKING:
    from src.knowledge_graph.ocd_graph import OCDGraph


@dataclass(frozen=True)
class VerifiedRecommendation:
    """Layer 3's output: a recommendation plus its full, auditable reasoning chain.

    This is the JSON contract described in the CLAUDE.md architecture
    overview and `docs/IMPLEMENTATION_PLAN.md` §3 (Layer 3) — every field
    here is what makes the recommendation "clinically defensible" rather
    than an opaque LLM output.
    """

    recommendation: str  # e.g. "Start graduated exposure with contamination items"
    reasoning_chain: list[str]  # one entry per layer/signal, e.g.
    # ["LLM detected: contamination_fear (0.78)", "NN predicted: escalation risk",
    #  "KG queried: contamination -> graduated_exposure_contamination",
    #  "Rules verified: safety ✓, guidelines ✓"]
    safety_flags: list[str]  # e.g. ["contraindication_suicidality"]
    confidence: float  # overall confidence in [0, 1] (epistemic only — see module docstring)
    clinician_review_required: bool  # True forces the Layer 4 approval gate to block auto-display


def verify_recommendation(
    candidate_recommendation: dict[str, Any],
    patient_context: dict[str, Any],
    kg: "OCDGraph",
    rules: RuleSet,
) -> VerifiedRecommendation:
    """Verify a candidate recommendation against KG facts, rules, and patient state.

    Orchestration (docs/IMPLEMENTATION_PLAN.md §4, Phase 9):
        1. Query `kg` for the protocol implied by
           `candidate_recommendation["distortion"]` (+ obsession, rigidity).
        2. Build the rule-evaluation context: candidate fields + KG result +
           `patient_context`.
        3. Run `rules.apply(candidate_recommendation, context)`.
        4. Fold the per-rule verdicts into a single `VerifiedRecommendation`:
           any failed safety-priority rule sets `safety_flags` and forces
           `clinician_review_required = True`; guideline-rule failures
           demote the recommendation to `clinician_review_required = True`
           without necessarily flagging; low
           `candidate_recommendation["confidence"]` (Layer 1.5) independently
           forces review regardless of rule outcomes.
        5. Assemble `reasoning_chain` as one human-readable line per
           layer/signal consulted, in order (LLM -> NN -> KG -> Rules),
           using `kg.explain_path` for the KG line.

    Args:
        candidate_recommendation: output of Layers 1-2, e.g.
            {"distortion": str, "obsession": str, "technique": str,
             "confidence": float, "rigidity": float}.
        patient_context: {"session_history": ..., "current_state": ...,
            "past_outcomes": ...} — whatever `SESSION_CONSISTENCY` and
            `PATIENT_STATE` conditions in `configs/rules.yaml` need.
        kg: a built `OCDGraph` (Layer 2) — queried for contraindications and
            precedent, never mutated.
        rules: a loaded `RuleSet` (Layer 3) — verifies safety, consistency,
            and guideline compliance.

    Returns:
        A `VerifiedRecommendation` with a complete reasoning chain. Never
        returns a bare LLM/KG recommendation unverified — if verification
        cannot complete (e.g. KG has no path for the candidate), the
        returned recommendation must fall back to generic psychoeducation
        with `clinician_review_required = True`, per the Layer 4 safety
        gate (docs/IMPLEMENTATION_PLAN.md §3, Layer 4).

    Raises:
        ValueError: if `candidate_recommendation` is missing required keys.
    """
    raise NotImplementedError
