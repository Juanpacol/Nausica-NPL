"""Cognitive Fable tests — heuristic policy is pure logic (no LLM, no checkpoint);
FablePolicyNet round-trips through a tiny checkpoint trained in the test itself."""

import pytest

from src.models.cognitive_fable import (
    CognitiveFable,
    FableAction,
    FableState,
    default_policy,
)
from src.utils.config import load_config, taxonomy_labels

CFG = load_config("model")["cognitive_fable"]


def test_config_covers_taxonomy():
    """Every taxonomy label must map to a technique from the declared vocab."""
    assert set(CFG["technique_map"].keys()) == set(taxonomy_labels())
    assert set(CFG["technique_map"].values()) <= set(CFG["techniques"])
    assert CFG["fallback_technique"] in CFG["techniques"]
    assert {band["tone"] for band in CFG["severity_bands"]} <= set(CFG["tones"])


def test_strongest_distortion_picks_technique():
    state = FableState(distortions={"catastrophizing": 0.9, "mind_reading": 0.2})
    action = default_policy(state)
    assert action.target_distortion == "catastrophizing"
    assert action.technique == CFG["technique_map"]["catastrophizing"]
    assert action.tone == "validating"  # 0.9 >= 0.8 band


def test_severity_bands_pick_tone():
    mild = default_policy(FableState(distortions={"mind_reading": 0.3}))
    moderate = default_policy(FableState(distortions={"mind_reading": 0.6}))
    severe = default_policy(FableState(distortions={"mind_reading": 0.95}))
    assert mild.tone == "exploratory"
    assert moderate.tone == "gently_challenging"
    assert severe.tone == "validating"


def test_empty_profile_gets_fallback():
    for distortions in ({}, {label: 0.0 for label in taxonomy_labels()}):
        action = default_policy(FableState(distortions=distortions))
        assert action.technique == CFG["fallback_technique"]
        assert action.target_distortion == "none"


def test_unknown_labels_ignored():
    action = default_policy(FableState(distortions={"not_a_label": 0.99}))
    assert action.target_distortion == "none"


def test_tie_breaks_deterministically():
    labels = taxonomy_labels()
    tied = {labels[0]: 0.7, labels[1]: 0.7}
    assert default_policy(FableState(distortions=tied)) == default_policy(
        FableState(distortions=dict(reversed(list(tied.items()))))
    )


def test_fable_heuristic_dispatch():
    fable = CognitiveFable(policy="heuristic")
    action = fable.select_action(FableState(distortions={"all_or_nothing": 0.8}))
    assert isinstance(action, FableAction)
    assert action.technique == CFG["technique_map"]["all_or_nothing"]


def test_fable_rejects_unknown_policy():
    with pytest.raises(ValueError):
        CognitiveFable(policy="quantum")


def test_policy_net_roundtrip(tmp_path):
    """Train a tiny net in-test, save, load, and predict — no real data needed."""
    torch = pytest.importorskip("torch")
    from src.models.cognitive_fable import FablePolicyNet

    labels = taxonomy_labels()
    arch = {"n_in": len(labels) + 1, "hidden": 8,
            "n_tech": len(CFG["techniques"]), "n_tone": len(CFG["tones"])}
    torch.manual_seed(0)
    net = FablePolicyNet(FablePolicyNet._build(**arch),
                         techniques=CFG["techniques"], tones=CFG["tones"])

    ckpt = tmp_path / "model.pt"
    net.save(ckpt, arch)
    loaded = FablePolicyNet.load(ckpt)

    state = FableState(distortions={labels[0]: 0.9}, session_turn=2)
    action = loaded.predict(state)
    assert action.technique in CFG["techniques"]
    assert action.tone in CFG["tones"]
    assert action.target_distortion == labels[0]
    # Same weights -> same prediction as the pre-save net
    assert loaded.predict(state) == net.predict(state)
