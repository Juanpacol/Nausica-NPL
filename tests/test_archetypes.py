"""Archetype mapping tests — pure config-driven logic, no models needed."""

from src.models.archetypes import classify_archetype, dominant_archetype


def _profile(**overrides):
    base = {
        "all_or_nothing": 0.1,
        "overgeneralization": 0.1,
        "emotional_reasoning": 0.1,
        "catastrophizing": 0.1,
        "mind_reading": 0.1,
    }
    base.update(overrides)
    return base


def test_worst_case_thinking_needs_both_labels():
    assert classify_archetype(
        _profile(catastrophizing=0.8, mind_reading=0.7)
    ) == "worst_case_thinking"
    # only one of the pair active -> falls through to the single-label rule
    assert classify_archetype(_profile(catastrophizing=0.8)) == "catastrophic_focus"


def test_black_white_thinking():
    assert classify_archetype(
        _profile(all_or_nothing=0.6, overgeneralization=0.6)
    ) == "black_white_thinking"


def test_fallback_when_nothing_active():
    assert classify_archetype(_profile()) == "balanced_thinking"


def test_rule_order_specific_first():
    # all four active: the first (most specific) matching rule wins
    assert classify_archetype(
        _profile(catastrophizing=0.9, mind_reading=0.9,
                 all_or_nothing=0.9, overgeneralization=0.9)
    ) == "worst_case_thinking"


def test_dominant_archetype_counts_and_trend():
    rigid = _profile(catastrophizing=0.9, mind_reading=0.9)
    flexible = _profile()
    result = dominant_archetype([rigid, rigid, rigid, flexible, flexible, flexible])
    assert result["archetype"] == "worst_case_thinking"  # tie broken by count order
    assert result["counts"]["worst_case_thinking"] == 3
    assert result["trend"] == "improving"  # newest third much less distortion mass


def test_dominant_archetype_empty_history():
    result = dominant_archetype([])
    assert result["archetype"] == "balanced_thinking"
    assert result["trend"] is None
