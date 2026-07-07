"""Classifier tests. Full model tests are skipped unless transformers + a local
checkpoint/network are available — pure-shape logic is tested without them."""

import json

import pytest

from src.utils.config import taxonomy_labels

transformers = pytest.importorskip("transformers")
torch = pytest.importorskip("torch")


@pytest.fixture(scope="module")
def classifier():
    from src.models.distortion_classifier import DistortionClassifier

    try:
        return DistortionClassifier.load()
    except Exception as e:  # gated model without HF_TOKEN, no network, etc.
        pytest.skip(f"encoder unavailable in this environment: {e}")


def test_predict_output_shape(classifier):
    result = classifier.predict("I always ruin everything, nobody will ever love me.")
    assert set(result.keys()) == set(taxonomy_labels())
    for prob in result.values():
        assert 0.0 <= prob <= 1.0


def test_predict_handles_long_text(classifier):
    long_text = "I feel like a failure. " * 500  # force truncation path
    result = classifier.predict(long_text)
    assert len(result) == len(taxonomy_labels())


def test_jsonl_dataset_builder(tmp_path):
    from src.models.distortion_classifier import _jsonl_to_dataset

    labels = taxonomy_labels()
    row = {"text": "sample", "distortions": {labels[0]: 0.9, labels[1]: 0.2}}
    path = tmp_path / "mini.jsonl"
    path.write_text(json.dumps(row) + "\n")

    ds = _jsonl_to_dataset(path, labels)
    assert ds[0]["text"] == "sample"
    vec = ds[0]["label_vector"]
    assert vec[0] == 1.0 and vec[1] == 0.0 and len(vec) == len(labels)
