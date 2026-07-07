"""Composite rigidity score (Phase 4) — weighted blend of the three signals.

    composite = w1 * classifier_cfi            (compute_cfi over distortion probs)
              + w2 * temporal_predicted_cfi    (CFI of the predicted next turn)
              + w3 * embedding_rigidity        (rigid-flexible axis projection)

Weights live in configs/model.yaml (`composite_rigidity.weights`) and are
HEURISTIC — not calibrated against real outcomes (disclosed in docs/VALIDATION.md).
The ensemble story: three independent operationalizations of the same construct
converging on one number is stronger evidence than any single one; when they
disagree strongly, `signal_spread` flags it rather than hiding it in the mean.

Signals can be missing (temporal model needs ≥1 history turn; embedding needs its
trained artifacts) — the blend renormalizes over the signals actually present.
"""

from __future__ import annotations

from src.utils.config import load_config


def compute_composite_rigidity(
    classifier_cfi: float,
    temporal_predicted_cfi: float | None = None,
    embedding_rigidity: float | None = None,
) -> dict:
    """Blend available signals; renormalize weights over the non-None ones.

    Returns {composite, components, weights_used, signal_spread}.
    signal_spread = max - min of the present signals (disagreement flag).
    """
    weights = load_config("model")["composite_rigidity"]["weights"]
    signals = {
        "classifier_cfi": classifier_cfi,
        "temporal_predicted_cfi": temporal_predicted_cfi,
        "embedding_rigidity": embedding_rigidity,
    }
    present = {k: v for k, v in signals.items() if v is not None}
    if not present:
        raise ValueError("At least classifier_cfi must be provided")
    for name, value in present.items():
        if not 0.0 <= value <= 1.0:
            raise ValueError(f"{name}={value} outside [0, 1]")

    total_w = sum(weights[k] for k in present)
    weights_used = {k: weights[k] / total_w for k in present}
    composite = sum(present[k] * weights_used[k] for k in present)

    return {
        "composite": round(composite, 4),
        "components": present,
        "weights_used": {k: round(w, 4) for k, w in weights_used.items()},
        "signal_spread": round(max(present.values()) - min(present.values()), 4),
    }
