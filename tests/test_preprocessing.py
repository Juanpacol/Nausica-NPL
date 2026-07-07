"""Preprocessing tests — pure logic, no datasets required."""

from src.data_pipeline.preprocessing import clean_text, linguistic_features


def test_clean_removes_urls_and_mentions():
    text = "check this https://example.com/x @someone and tell me"
    cleaned = clean_text(text)
    assert "https://" not in cleaned
    assert "@someone" not in cleaned


def test_clean_preserves_emphasis():
    """Casing and punctuation are signal for distortion detection."""
    text = "I will NEVER be good enough!!!"
    assert "NEVER" in clean_text(text)
    assert "!!!" in clean_text(text)


def test_clean_normalizes_whitespace():
    assert clean_text("too   many\n\nspaces") == "too many spaces"


def test_absolutism_rate_detects_markers():
    rigid = linguistic_features("I always fail and nothing ever works, everyone hates me")
    neutral = linguistic_features("Today I went to the store and bought some bread")
    assert rigid["absolutism_rate"] > neutral["absolutism_rate"] == 0.0


def test_first_person_rate():
    feats = linguistic_features("I think I hurt myself and my dog")
    assert feats["first_person_rate"] > 0
    assert feats["word_count"] == 8
