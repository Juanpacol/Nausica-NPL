"""Rigidity embedding tests. Projection math is pure and tested without any model;
model-dependent paths are skipped when artifacts/library are unavailable."""

import numpy as np
import pytest

from src.models.rigidity_embedding import _project
from src.utils.config import PROJECT_ROOT, load_config


@pytest.fixture
def geometry():
    flexible = np.array([0.0, 0.0])
    rigid = np.array([1.0, 0.0])
    axis = rigid - flexible
    # raw projections: flexible -> 0, rigid -> 1 (dot products along the axis)
    return {"flexible": flexible, "rigid": rigid, "axis": axis, "lo": 0.0, "hi": 1.0}


def test_projection_endpoints(geometry):
    g = geometry
    at_rigid = _project(g["rigid"], g["flexible"], g["axis"], g["lo"], g["hi"])
    at_flexible = _project(g["flexible"], g["flexible"], g["axis"], g["lo"], g["hi"])
    assert at_rigid == pytest.approx(1.0)
    assert at_flexible == pytest.approx(0.0)


def test_projection_midpoint(geometry):
    g = geometry
    mid = (g["rigid"] + g["flexible"]) / 2
    assert _project(mid, g["flexible"], g["axis"], g["lo"], g["hi"]) == pytest.approx(0.5)


def test_projection_clamps_out_of_range(geometry):
    g = geometry
    beyond_rigid = g["rigid"] * 3
    behind_flexible = -g["rigid"]
    assert _project(beyond_rigid, g["flexible"], g["axis"], g["lo"], g["hi"]) == 1.0
    assert _project(behind_flexible, g["flexible"], g["axis"], g["lo"], g["hi"]) == 0.0


def test_projection_rejects_degenerate_range(geometry):
    g = geometry
    with pytest.raises(ValueError):
        _project(g["rigid"], g["flexible"], g["axis"], 1.0, 1.0)


def test_trained_embedder_scores_in_range():
    pytest.importorskip("sentence_transformers")
    cfg = load_config("model")["contrastive_embedding"]
    if not (PROJECT_ROOT / cfg["output_dir"] / "projection.json").exists():
        pytest.skip("rigidity embedding not trained yet")
    from src.models.rigidity_embedding import RigidityEmbedder

    embedder = RigidityEmbedder.load()
    score = embedder.rigidity_score("I always fail at everything")
    assert isinstance(score, float) and 0.0 <= score <= 1.0
