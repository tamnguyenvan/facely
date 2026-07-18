"""Identity repository for database operations."""
import numpy as np
from app.db.database import Database
from app.utils.logger import get_logger

logger = get_logger(__name__)


class IdentityRepository:
    """Repository for identity and embedding CRUD operations."""
    
    def __init__(self, db: Database):
        self._db = db
    
    def upsert_identity(
        self, name: str, person_id: str, model_name: str, embedding: np.ndarray
    ) -> None:
        """Insert or update an identity with its embedding."""
        conn = self._db.get_connection()
        try:
            with conn:
                # Upsert identity
                conn.execute(
                    """
                    INSERT INTO identities (name, person_id)
                    VALUES (?, ?)
                    ON CONFLICT(person_id) DO UPDATE SET
                        name = excluded.name,
                        updated_at = datetime('now')
                    """,
                    (name, person_id),
                )
                
                # Get identity ID
                row = conn.execute(
                    "SELECT id FROM identities WHERE person_id = ?", (person_id,)
                ).fetchone()
                
                # Insert embedding
                conn.execute(
                    """
                    INSERT INTO embeddings (identity_id, model_name, vector)
                    VALUES (?, ?, ?)
                    ON CONFLICT(identity_id, model_name) DO UPDATE SET
                        vector = excluded.vector,
                        created_at = datetime('now')
                    """,
                    (row["id"], model_name, embedding.tobytes()),
                )
            logger.info(f"Upserted identity: {name} ({person_id})")
        finally:
            conn.close()
    
    def get_all_embeddings(self, model_name: str) -> list[dict]:
        """Get all embeddings for a specific model."""
        conn = self._db.get_connection()
        try:
            rows = conn.execute(
                """
                SELECT i.person_id, i.name, e.vector
                FROM embeddings e
                JOIN identities i ON i.id = e.identity_id
                WHERE e.model_name = ?
                """,
                (model_name,),
            ).fetchall()
            
            result = []
            for row in rows:
                vec = np.frombuffer(row["vector"], dtype=np.float32).copy()
                result.append({
                    "person_id": row["person_id"],
                    "name": row["name"],
                    "embedding": vec,
                })
            return result
        finally:
            conn.close()
    
    def delete_identity(self, person_id: str) -> None:
        """Delete an identity and all its embeddings."""
        conn = self._db.get_connection()
        try:
            with conn:
                conn.execute(
                    "DELETE FROM identities WHERE person_id = ?", (person_id,)
                )
            logger.info(f"Deleted identity: {person_id}")
        finally:
            conn.close()
    
    def list_identities(self) -> list[dict]:
        """List all identities."""
        conn = self._db.get_connection()
        try:
            rows = conn.execute(
                "SELECT person_id, name, created_at FROM identities ORDER BY name"
            ).fetchall()
            return [dict(r) for r in rows]
        finally:
            conn.close()
