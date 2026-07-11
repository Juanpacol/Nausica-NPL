# Symbolic Rules Engine — Specification (Skeleton)

> **Status:** outline only — Phase 8 (`RuleSet`/`apply_rules`/`~50 rules`)
> is not started. This document is the placeholder structure to fill in as
> that phase lands; see `docs/IMPLEMENTATION_PLAN.md` §3 (Layer 3) and §4
> (Phase 8) for the authoritative scope and timeline.

Implementation: `src/rules_engine/` (`engine.py`, `verification.py`).
Content: `configs/rules.yaml`. Tests: deferred to Phase 8 (target: 20+
unit tests, rules exercised without a live knowledge graph via mocked KG
queries).

## 1. Purpose: safety + guideline compliance

- *(fill in Phase 8)* Restate the Layer 3 invariant from
  `docs/IMPLEMENTATION_PLAN.md` §3: all conditional/procedural logic lives
  here, never in `src/knowledge_graph/` (Layer 2 = facts, Layer 3 =
  inference over facts + patient state).
- *(fill in Phase 8)* Why a custom YAML engine over Rete/experta — see
  "Stack decisions" table in `docs/IMPLEMENTATION_PLAN.md` §3; consistency
  with `src/models/archetypes.py` / `cognitive_fable.py`'s config-driven
  policy pattern.

## 2. Rule anatomy: conditions, actions, priority

- *(fill in Phase 8)* `Condition` / `ConditionType` reference
  (`src/rules_engine/engine.py`) — one entry per type
  (CONFIDENCE_ABOVE, DISTORTION_EQUALS, RIGIDITY_ABOVE, PATIENT_STATE,
  SESSION_CONSISTENCY), what context field each reads, and supported
  operators.
- *(fill in Phase 8)* `Action` / action types (approve, flag,
  suggest_alternative, escalate) and what each does downstream in
  `verify_recommendation`.
- *(fill in Phase 8)* `priority` ordering convention: safety (90-100) >
  clinical guideline (50-89) > consistency (0-49) — see
  `configs/rules.yaml` for the current placeholder bands.

## 3. Execution semantics

- *(fill in Phase 8)* `RuleSet.apply` evaluates **every** rule (not
  first-match-wins) and returns all (rule, passed, explanation) tuples —
  document why: Layer 3's auditability guarantee requires every verdict to
  be inspectable, not just the one that changed the final decision.
- *(fill in Phase 8)* How `verify_recommendation`
  (`src/rules_engine/verification.py`) folds that list into a single
  `VerifiedRecommendation` (safety failures -> `safety_flags` +
  mandatory review; guideline failures -> review without a flag;
  consistency failures -> `suggest_alternative`).

## 4. Integration with Layer 2 (KG queries in conditions)

- *(fill in Phase 9)* How `verify_recommendation` merges an `OCDGraph`
  query result (`kg.query_treatment`, `kg.explain_path`) into the
  evaluation context before calling `RuleSet.apply` — contraindications
  discovered in the graph become `PATIENT_STATE`/safety conditions, not
  hardcoded rule logic.

## 5. Integration with Layer 1.5 (confidence gating)

- *(fill in Phase 9)* The F2-corrected ensemble split
  (`docs/IMPLEMENTATION_PLAN.md` §3, Layer 1.5): `confidence` (LLM +
  temporal, epistemic) gates rule strictness and
  `clinician_review_required`; `rigidity` modulates the recommendation
  content only and must never be read by a `CONFIDENCE_ABOVE` condition.

## 6. Known limitations (disclose always)

- *(fill in Phase 8)* Rules are hand-authored, not learned or verified
  against a formal clinical ontology — compliance is checked against the
  Phase 6 expert checklist (Q2 in `docs/IMPLEMENTATION_PLAN.md` §5), not
  an independent regulatory standard.
