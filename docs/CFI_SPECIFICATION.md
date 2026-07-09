# Cognitive Flexibility Index (CFI) — Formal Specification

Formal definition of the project's core metric. Implementation:
`src/metrics/cognitive_flexibility_index.py` (pure logic, unit-tested in
`tests/test_cfi_metric.py`). Label definitions and weight rationale:
`docs/TAXONOMY.md`. This document consolidates the math, the design arguments,
and the upgrade path in one place for papers and reviewers.

## Definition

Given the 5-type distortion taxonomy L = {all_or_nothing, overgeneralization,
emotional_reasoning, catastrophizing, mind_reading}, per-label calibrated
probabilities p_i ∈ [0, 1] from the distortion classifier, and fixed severity
weights w_i > 0 (configs/data.yaml):

```
             Σ_{i ∈ L}  w_i · clamp(p_i, 0, 1)
CFI(text) = ─────────────────────────────────────        ∈ [0, 1]
                       Σ_{i ∈ L}  w_i
```

Higher = more cognitively rigid. Normalization by Σw_i keeps the range stable
even if config weights don't sum exactly to 1; unknown labels in the input are
ignored, missing labels count as 0 (see `compute_cfi`).

### Properties (each one is a unit test)

| Property | Statement | Test |
|---|---|---|
| Boundedness | CFI ∈ [0, 1] for any input | `test_cfi_bounds` |
| Zero point | No detected distortion ⇒ CFI = 0 | `test_neutral_text_scores_zero` |
| Monotonicity | Raising any p_i never lowers CFI | `test_monotonic_in_each_label` |
| Robustness | Out-of-range probabilities are clamped | `test_probabilities_clamped` |
| Closed vocabulary | Labels outside L are ignored | `test_unknown_labels_ignored` |

## Weights

| Label | Weight | Rationale (docs/TAXONOMY.md) |
|---|---|---|
| all_or_nothing | 0.25 | strongest rigidity/helplessness predictor in CBT literature |
| overgeneralization | 0.25 | idem |
| catastrophizing | 0.20 | high severity, more situational |
| emotional_reasoning | 0.15 | pervasive but lower specificity |
| mind_reading | 0.15 | idem |

These are **fixed severity priors, not fitted parameters** — a defensible
starting point, disclosed as such. Upgrade path: learn the weights by
regression against real clinical outcomes (normalized PHQ-9/GAD-7) once
longitudinal data exists — the same pattern already implemented for the
composite score in `src/metrics/composite_rigidity.py:calibrate_weights`.

## Why a continuous index instead of binary classification

The system's headline evaluation is whether CFI **decreases across the turns of
a reframing dialogue** (`ReframingTrajectory.delta < 0`). That question is
unanswerable with a binary label:

| Capability | Binary label | Multi-label categorical | **CFI** |
|---|---|---|---|
| Detects distortion presence | ✓ | ✓ | ✓ |
| Grades severity | ✗ | ✗ | ✓ |
| Sensitive to within-session change | ✗ | coarse | ✓ |
| Per-distortion interpretability | ✗ | ✓ | ✓ (weighted decomposition) |
| Correlatable with continuous clinical scales | rank-only | rank-only | ✓ (Pearson/Spearman) |

A binary "distorted / not distorted" flag cannot distinguish a client moving
from catastrophizing at p=0.9 to p=0.5 — clinically meaningful loosening that
CFI captures as a score drop while a threshold classifier reports "still
distorted" twice.

## Trajectory semantics

`ReframingTrajectory` records CFI per **client** turn (counselor turns carry no
client cognition). `delta` = last − first; negative = rigidity decreased (the
goal). `is_improving` is the sign of delta. Session-level aggregation and trend
detection over a user's history live in `src/models/archetypes.py`.

## Known limitations (disclose in every paper)

1. p_i come from a classifier fine-tuned on **LLM weak labels** — no clinician
   ground truth at scale (docs/DATA_QUALITY.md holds the spot-check evidence).
2. Weights are literature-informed priors, not fitted (see upgrade path above).
3. CFI treats distortions as independent; interaction structure (co-occurring
   distortions amplifying each other) is future work (docs/ARCHITECTURE.md).
4. CFI measures *linguistic expression* of rigidity, not rigidity itself — a
   guarded client can score low while thinking rigidly.

## Worked example

> _pending — fill with a real trajectory after the Phase 1 classifier
> fine-tune lands (docs/VALIDATION.md tracks the training status)._
