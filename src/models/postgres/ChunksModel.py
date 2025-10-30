from typing import List
from uuid import UUID

from sqlalchemy import delete, select
from sqlalchemy.exc import IntegrityError

from .BaseModel import BaseModel
from models.postgres.tables_schema.tables import Chunk
from models.postgres.operations_schema import ChunkInsert, ChunkOut
from helpers.logger import get_logger

logger = get_logger("ChunksModel")


class ChunksModel(BaseModel):
    def __init__(self):
        super().__init__()

    async def insert_chunks(self, db, chunks_list: List[ChunkInsert], batch_size: int = 100) -> List[Chunk]:
        """
        Insert chunks in batches using the provided db session.
        Logs each attempt, success, and failure.
        """
        inserted_chunks = []

        for i in range(0, len(chunks_list), batch_size):
            batch = chunks_list[i:i + batch_size]
            db_objects = [
                Chunk(
                    document_id=chunk.document_id,
                    text=chunk.text,
                    metadata_json=chunk.metadata_json,
                )
                for chunk in batch
            ]

            logger.info(f"Attempting to insert batch {i // batch_size + 1} with {len(batch)} chunks...")
            db.add_all(db_objects)
            try:
                await db.commit()
                for obj in db_objects:
                    await db.refresh(obj)
                inserted_chunks.extend(db_objects)
                logger.info(f"Successfully inserted batch {i // batch_size + 1}")
            except IntegrityError as e:
                await db.rollback()
                logger.error(f"Failed to insert batch {i // batch_size + 1}: {e}")
                raise ValueError(f"Failed to insert chunk batch: {e}")

        logger.info(f"Inserted total of {len(inserted_chunks)} chunks successfully.")
        return inserted_chunks

    async def is_document_id_exist(self, db, document_id: UUID) -> ChunkOut | None:
        """
        Check if any chunk exists for a given document_id using the provided db session.
        """
        logger.info(f"Checking if chunks exist for document_id={document_id}...")
        stmt = select(Chunk).where(Chunk.document_id == document_id)
        result = await db.execute(stmt)
        chunk = result.scalar_one_or_none()
        if chunk:
            logger.info(f"Found chunks for document_id={document_id}")
            return ChunkOut.model_validate(chunk)
        logger.info(f"No chunks found for document_id={document_id}")
        return None

    async def delete_chunks_by_document_id(self, db, document_id: UUID) -> bool:
        """
        Delete all chunks for a given document_id using the provided db session.
        Logs attempt and result.
        """
        logger.info(f"Attempting to delete chunks for document_id={document_id}...")
        stmt = delete(Chunk).where(Chunk.document_id == document_id)
        result = await db.execute(stmt)
        await db.commit()
        deleted = (result.rowcount or 0) > 0
        if deleted:
            logger.info(f"Deleted {result.rowcount} chunk(s) for document_id={document_id}")
        else:
            logger.info(f"No chunks to delete for document_id={document_id}")
        return deleted
