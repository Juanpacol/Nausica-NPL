"""Mindset archetypes (Phase 4) — human-readable thinking-pattern labels.

Maps a 5-dim distortion probability profile to a named archetype via the
config-driven rules in configs/model.yaml (`archetypes`). A rule matches when ALL
its labels exceed the activation threshold; the first matching rule wins (rules
are ordered most-specific first), with a fallback when none match.

This is deliberately rule-based, not learned: the mapping must be inspectable and
tunable by clinicians without retraining anything. BERTopic topic assignments
(src/models/mindset_profiler.py) can enrich this later once a topic model is
trained on the full weak-labeled corpus — the two are complementary, not coupled.

Aggregation over a user's history (`dominant_archetype`) powers the
GET /profile/archetype endpoint: dominant pattern + whether recent texts lean
less rigid than older ones (trend).
"""

from __future__ import annotations

from src.utils.config import load_config


def classify_archetype(distortions: dict[str, float]) -> str:
    """Distortion profile -> archetype name (first matching config rule)."""
    cfg = load_config("model")["archetypes"]
    threshold = cfg["activation_threshold"]
    for rule in cfg["rules"]:
        if all(distortions.get(label, 0.0) >= threshold for label in rule["labels"]):
            return rule["name"]
    return cfg["fallback"]


def dominant_archetype(profiles: list[dict[str, float]]) -> dict:
    """Aggregate a chronological list of distortion profiles.

    Returns {archetype, counts, trend} where trend compares the mean CFI-weighted
    distortion mass of the newest third vs the oldest third of the history:
    'improving' (recent < older), 'worsening', or 'stable' (within ±0.02).
    Empty history -> fallback archetype with empty counts.
    """
    cfg = load_config("model")["archetypes"]
    if not profiles:
        return {"archetype": cfg["fallback"], "counts": {}, "trend": None}

    counts: dict[str, int] = {}
    for p in profiles:
        name = classify_archetype(p)
        counts[name] = counts.get(name, 0) + 1
    dominant = max(counts, key=lambda k: counts[k])

    trend = None
    if len(profiles) >= 3:
        third = max(1, len(profiles) // 3)
        mean_mass = lambda chunk: sum(  # noqa: E731
            sum(p.values()) / max(len(p), 1) for p in chunk
        ) / len(chunk)
        older, newer = mean_mass(profiles[:third]), mean_mass(profiles[-third:])
        if newer < older - 0.02:
            trend = "improving"
        elif newer > older + 0.02:
            trend = "worsening"
        else:
            trend = "stable"

    return {"archetype": dominant, "counts": counts, "trend": trend}
