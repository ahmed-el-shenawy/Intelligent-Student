# src/models/vector_model.py
import logging
from typing import List
from uuid import UUID

from sqlalchemy import Float, insert, select, delete
from sqlalchemy.exc import IntegrityError

from .BaseModel import BaseModel
from models.postgres.tables_schema.tables import VectorEmbedding, Chunk
from models.postgres.operations_schema import VectorInsertItems,VectorOut

logger = logging.getLogger(__name__)


class VectorModel(BaseModel):
    def __init__(self):
        super().__init__()

    # -------------------------------------------------------------------------
    # ✅ Insert multiple vectors in batches
    # -------------------------------------------------------------------------
    async def insert_vectors(
        self,
        data: VectorInsertItems,
        batch_size: int = 100,
    ) -> list[dict]:
        """Insert vectors for a document (batched for performance)."""
        if not data.vectors:
            return []

        if len(data.chunk_id) != len(data.vectors):
            raise ValueError("chunk_id list length must match vectors length")

        inserted_rows = []

        async for session in self.get_session():
            for i in range(0, len(data.vectors), batch_size):
                batch_vectors = data.vectors[i:i + batch_size]
                batch_chunks = data.chunk_id[i:i + batch_size]

                rows_to_insert = [
                    {
                        "project_id": data.project_id,
                        "document_id": data.document_id,
                        "chunk_id": chunk_id,
                        "embedding": vector,
                    }
                    for chunk_id, vector in zip(batch_chunks, batch_vectors)
                ]

                stmt = insert(VectorEmbedding).values(rows_to_insert).returning(VectorEmbedding.id)

                try:
                    result = await session.execute(stmt)
                    await session.commit()
                    inserted_rows.extend([row.id for row in result.fetchall()])
                    print("2")
                except IntegrityError as e:
                    await session.rollback()
                    logger.error(f"Failed to insert vector batch: {e}")
                    raise ValueError("Failed to insert vectors batch") from e

        return True

    # -------------------------------------------------------------------------
    # ✅ Delete all vectors by document_id
    # -------------------------------------------------------------------------
    async def delete_vectors_by_document_id(self, document_id: UUID) -> bool:
        """Delete all vector embeddings related to a document."""
        async for session in self.get_session():
            stmt = delete(VectorEmbedding).where(VectorEmbedding.document_id == document_id)
            await session.execute(stmt)
            await session.commit()
            return True

    # -------------------------------------------------------------------------
    # ✅ Retrieve top-k similar chunks (with text + distance)
    # -------------------------------------------------------------------------
    async def top_k_similar_vector_text(
        self,
        query_vector: List[float],
        project_id: UUID,
        top_k: int,
    ) -> list[dict]:
        """
        Return the most similar chunks (with their text) and similarity distance.
        Uses cosine similarity via pgvector's '<=>' operator.
        """
        async for session in self.get_session():
            # Label distance as Float so SQLAlchemy does not try to parse it as Vector
            distance_expr = VectorEmbedding.embedding.op("<=>")(query_vector).cast(Float).label("distance")

            stmt = (
                select(Chunk.text, distance_expr)
                .join(Chunk, Chunk.id == VectorEmbedding.chunk_id)
                .where(VectorEmbedding.project_id == project_id)
                .order_by(distance_expr)
                .limit(top_k)
            )

            result = await session.execute(stmt)
            rows = result.fetchall()

            return [VectorOut(text=row.text, distance=row.distance) for row in rows]
