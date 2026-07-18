"""Registration service for adding new identities."""
import numpy as np
import uuid
from app.core.detector import FaceDetector
from app.core.model_manager import ModelManager
from app.db.identity_repo import IdentityRepository
from app.utils.logger import get_logger

logger = get_logger(__name__)


class RegistrationService:
    """Handles registration of new identities."""
    
    CAPTURE_FRAMES = 5
    
    def __init__(
        self,
        detector: FaceDetector,
        model_manager: ModelManager,
        repo: IdentityRepository,
    ):
        self._detector = detector
        self._mm = model_manager
        self._repo = repo
    
    def register(
        self, name: str, frames: list, person_id: str | None = None
    ) -> str:
        """
        Register a new identity from captured frames.
        
        Args:
            name: Identity name
            frames: List of BGR frames
            person_id: Optional person ID (auto-generated if None)
        
        Returns:
            Assigned person_id
        """
        embeddings = []
        
        for frame in frames:
            faces = self._detector.detect(frame)
            if not faces:
                continue
            
            crop = self._detector.crop_face(frame, faces[0]["bbox"])
            emb = self._mm.active_model.get_embedding(crop)
            embeddings.append(emb)
        
        if not embeddings:
            raise ValueError("No faces detected in capture frames")
        
        # Average embeddings for robustness
        avg_embedding = np.mean(embeddings, axis=0)
        avg_embedding = avg_embedding / np.linalg.norm(avg_embedding)
        
        pid = person_id or str(uuid.uuid4())[:8].upper()
        self._repo.upsert_identity(
            name=name,
            person_id=pid,
            model_name=self._mm.active_name,
            embedding=avg_embedding,
        )
        
        logger.info(f"Registered: {name} ({pid}) via {self._mm.active_name}")
        return pid
