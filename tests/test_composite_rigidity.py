"""Composite rigidity blend tests — pure math over config weights."""

import pytest

from src.metrics.composite_rigidity import compute_composite_rigidity


def test_all_signals_weighted_blend():
    result = compute_composite_rigidity(0.8, 0.6, 0.4)
    # weights 0.5/0.25/0.25 -> 0.4 + 0.15 + 0.1 = 0.65
    assert result["composite"] == pytest.approx(0.65, abs=1e-4)
    assert result["signal_spread"] == pytest.approx(0.4, abs=1e-4)


def test_missing_signals_renormalize():
    result = compute_composite_rigidity(0.8, None, None)
    assert result["composite"] == pytest.approx(0.8, abs=1e-4)
    assert result["weights_used"] == {"classifier_cfi": 1.0}


def test_two_signals_renormalize():
    result = compute_composite_rigidity(0.6, None, 0.6)
    # 0.5 and 0.25 renormalize to 2/3 and 1/3; both signals 0.6 -> 0.6
    assert result["composite"] == pytest.approx(0.6, abs=1e-4)
    assert result["weights_used"]["classifier_cfi"] == pytest.approx(2 / 3, abs=1e-3)


def test_out_of_range_rejected():
    with pytest.raises(ValueError):
        compute_composite_rigidity(1.2)
    with pytest.raises(ValueError):
        compute_composite_rigidity(0.5, -0.1, None)


def test_agreement_has_zero_spread():
    assert compute_composite_rigidity(0.5, 0.5, 0.5)["signal_spread"] == 0.0
