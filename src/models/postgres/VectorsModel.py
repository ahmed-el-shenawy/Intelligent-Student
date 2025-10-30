# src/models/vector_model.py
import logging
from typing import List
from uuid import UUID

from sqlalchemy import Float, insert, select, delete
from sqlalchemy.exc import IntegrityError

from .BaseModel import BaseModel
from models.postgres.tables_schema.tables import VectorEmbedding, Chunk
from models.postgres.operations_schema import VectorInsertItems, VectorOut

logger = logging.getLogger("VectorModel")


class VectorModel(BaseModel):
    def __init__(self):
        super().__init__()

    # -------------------------------------------------------------------------
    # ✅ Insert multiple vectors in batches
    # -------------------------------------------------------------------------
    async def insert_vectors(
        self,
        db,
        data: VectorInsertItems,
        batch_size: int = 100,
    ) -> list[int]:
        """Insert vectors for a document (batched for performance)."""
        if not data.vectors:
            logger.info(f"No vectors to insert for document {data.document_id}")
            return []

        if len(data.chunk_id) != len(data.vectors):
            raise ValueError("chunk_id list length must match vectors length")

        inserted_rows = []

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
                logger.info(f"Attempting to insert vector batch for document {data.document_id} [{i}-{i + len(batch_vectors)}]")
                result = await db.execute(stmt)
                await db.commit()
                batch_ids = [row.id for row in result.fetchall()]
                inserted_rows.extend(batch_ids)
                logger.info(f"Successfully inserted {len(batch_ids)} vectors for document {data.document_id}")
            except IntegrityError as e:
                await db.rollback()
                logger.error(f"Failed to insert vector batch for document {data.document_id}: {e}")
                raise ValueError("Failed to insert vectors batch") from e

        return inserted_rows

    # -------------------------------------------------------------------------
    # ✅ Delete all vectors by document_id
    # -------------------------------------------------------------------------
    async def delete_vectors_by_document_id(self, db, document_id: UUID) -> bool:
        """Delete all vector embeddings related to a document."""
        try:
            logger.info(f"Attempting to delete vectors for document {document_id}")
            stmt = delete(VectorEmbedding).where(VectorEmbedding.document_id == document_id)
            result = await db.execute(stmt)
            await db.commit()
            deleted_count = result.rowcount or 0
            logger.info(f"Deleted {deleted_count} vectors for document {document_id}")
            return True
        except Exception as e:
            await db.rollback()
            logger.error(f"Failed to delete vectors for document {document_id}: {e}")
            return False

    # -------------------------------------------------------------------------
    # ✅ Retrieve top-k similar chunks (with text + distance)
    # -------------------------------------------------------------------------
    async def top_k_similar_vector_text(
        self,
        db,
        query_vector: List[float],
        project_id: UUID,
        top_k: int,
    ) -> list[VectorOut]:
        """
        Return the most similar chunks (with their text) and similarity distance.
        Uses cosine similarity via pgvector's '<=>' operator.
        """
        try:
            logger.info(f"Querying top {top_k} similar vectors for project {project_id}")
            distance_expr = VectorEmbedding.embedding.op("<=>")(query_vector).cast(Float).label("distance")

            stmt = (
                select(Chunk.text, distance_expr)
                .join(Chunk, Chunk.id == VectorEmbedding.chunk_id)
                .where(VectorEmbedding.project_id == project_id)
                .order_by(distance_expr)
                .limit(top_k)
            )

            result = await db.execute(stmt)
            rows = result.fetchall()
            logger.info(f"Retrieved {len(rows)} similar vectors for project {project_id}")
            return [VectorOut(text=row.text, distance=row.distance) for row in rows]
        except Exception as e:
            logger.error(f"Failed to retrieve top-k vectors for project {project_id}: {e}")
            return []
