"""Embedding matcher using cosine similarity."""
import numpy as np
from app.config import CONFIG
from app.utils.logger import get_logger

logger = get_logger(__name__)


class EmbeddingMatcher:
    """In-memory cosine similarity matcher."""
    
    def __init__(self):
        self._cache: dict[str, tuple[str, np.ndarray]] = {}
    
    def load_cache(self, identities: list[dict]) -> None:
        """
        Load embedding cache from identities.
        
        Args:
            identities: List of dicts with person_id, name, embedding
        """
        self._cache = {
            item["person_id"]: (item["name"], item["embedding"])
            for item in identities
        }
        logger.info(f"Embedding cache loaded: {len(self._cache)} identities")
    
    def invalidate(self) -> None:
        """Clear the embedding cache."""
        self._cache.clear()
        logger.debug("Embedding cache invalidated")
    
    def find_best(self, query: np.ndarray) -> dict:
        """
        Find best matching identity for query embedding.
        
        Returns:
            Dict with person_id, name, score
        """
        if not self._cache:
            return {"name": "Unknown", "score": 0.0, "person_id": None}
        
        best_id, best_name, best_score = None, "Unknown", -1.0
        
        for pid, (name, stored) in self._cache.items():
            score = float(np.dot(query, stored))  # Both L2-normalized → cosine
            if score > best_score:
                best_score = score
                best_id = pid
                best_name = name
        
        if best_score < CONFIG.similarity_threshold:
            return {"name": "Unknown", "score": best_score, "person_id": None}
        
        return {"name": best_name, "score": best_score, "person_id": best_id}
