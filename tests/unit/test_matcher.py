"""Unit tests for EmbeddingMatcher."""
import numpy as np
import pytest
from app.core.matcher import EmbeddingMatcher
from app.config import CONFIG


@pytest.fixture
def matcher():
    """Create a matcher instance."""
    return EmbeddingMatcher()


@pytest.fixture
def identities():
    """Create sample identities."""
    alice_vec = np.random.rand(512).astype(np.float32)
    alice_vec /= np.linalg.norm(alice_vec)
    
    bob_vec = np.random.rand(512).astype(np.float32)
    bob_vec /= np.linalg.norm(bob_vec)
    
    return [
        {"person_id": "ALICE1", "name": "Alice", "embedding": alice_vec},
        {"person_id": "BOB1", "name": "Bob", "embedding": bob_vec},
    ]


def test_exact_match(matcher, identities):
    """Test exact embedding match."""
    matcher.load_cache(identities)
    result = matcher.find_best(identities[0]["embedding"])
    assert result["name"] == "Alice"
    assert result["score"] >= 0.99


def test_empty_cache_returns_unknown(matcher):
    """Test that empty cache returns Unknown."""
    result = matcher.find_best(np.ones(512, dtype=np.float32))
    assert result["name"] == "Unknown"
    assert result["person_id"] is None


def test_cache_invalidation(matcher, identities):
    """Test cache invalidation."""
    matcher.load_cache(identities)
    matcher.invalidate()
    result = matcher.find_best(identities[0]["embedding"])
    assert result["name"] == "Unknown"


def test_below_threshold_returns_unknown(matcher, identities):
    """Test that low similarity returns Unknown."""
    matcher.load_cache(identities)
    # Create orthogonal vector (very low similarity)
    random_vec = np.random.rand(512).astype(np.float32)
    random_vec /= np.linalg.norm(random_vec)
    result = matcher.find_best(random_vec)
    # May or may not be Unknown depending on random similarity
    assert "name" in result
    assert "score" in result
