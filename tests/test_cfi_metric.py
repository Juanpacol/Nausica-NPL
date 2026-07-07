"""CFI metric tests — pure logic, no network/GPU/API keys required."""

import pytest

from src.metrics.cognitive_flexibility_index import (
    ReframingTrajectory,
    compute_cfi,
)
from src.utils.config import cfi_weights, taxonomy_labels

ALL_HIGH = {label: 0.95 for label in taxonomy_labels()}
ALL_ZERO = {label: 0.0 for label in taxonomy_labels()}


def test_cfi_bounds():
    assert 0.0 <= compute_cfi(ALL_ZERO) <= compute_cfi(ALL_HIGH) <= 1.0


def test_neutral_text_scores_zero():
    assert compute_cfi(ALL_ZERO) == 0.0


def test_all_distortions_score_higher_than_neutral():
    assert compute_cfi(ALL_HIGH) > compute_cfi(ALL_ZERO)


def test_monotonic_in_each_label():
    """Raising any single distortion's probability must never lower CFI."""
    for label in taxonomy_labels():
        low = dict(ALL_ZERO)
        high = dict(ALL_ZERO)
        high[label] = 0.9
        assert compute_cfi(high) > compute_cfi(low)


def test_probabilities_clamped():
    wild = {label: 5.0 for label in taxonomy_labels()}
    assert compute_cfi(wild) <= 1.0
    negative = {label: -1.0 for label in taxonomy_labels()}
    assert compute_cfi(negative) == 0.0


def test_unknown_labels_ignored():
    probs = dict(ALL_ZERO)
    probs["not_a_real_label"] = 1.0
    assert compute_cfi(probs) == 0.0


def test_weights_config_covers_taxonomy():
    assert set(cfi_weights().keys()) == set(taxonomy_labels())
    assert sum(cfi_weights().values()) == pytest.approx(1.0)


def test_trajectory_tracks_improvement():
    traj = ReframingTrajectory("s1")
    assert traj.delta is None and traj.is_improving is None

    traj.add_turn({label: 0.8 for label in taxonomy_labels()})
    traj.add_turn({label: 0.5 for label in taxonomy_labels()})
    traj.add_turn({label: 0.3 for label in taxonomy_labels()})

    assert traj.delta is not None and traj.delta < 0
    assert traj.is_improving is True
    d = traj.to_dict()
    assert [p["turn"] for p in d["points"]] == [1, 2, 3]


def test_trajectory_detects_worsening():
    traj = ReframingTrajectory("s2")
    traj.add_turn({label: 0.2 for label in taxonomy_labels()})
    traj.add_turn({label: 0.7 for label in taxonomy_labels()})
    assert traj.is_improving is False
