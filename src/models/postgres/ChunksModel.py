from typing import List
from uuid import UUID

from sqlalchemy import delete, select
from sqlalchemy.exc import IntegrityError

from .BaseModel import BaseModel
from models.postgres.tables_schema.tables import Chunk
from models.postgres.operations_schema import ChunkInsert, ChunkOut


class ChunksModel(BaseModel):
    def __init__(self):
        super().__init__()

    async def insert_chunks(self, chunks_list: List[ChunkInsert], batch_size: int = 100):
        async for session in self.get_session():
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

                session.add_all(db_objects)
                try:
                    await session.commit()
                    # Optional: refresh each object if needed
                    for obj in db_objects:
                        await session.refresh(obj)
                    return db_objects
                except IntegrityError as e:
                    await session.rollback()
                    raise ValueError(f"Failed to insert chunk batch: {e}")

    async def is_document_id_exist(self, document_id: UUID):
        async for session in self.get_session():
            stmt = select(Chunk).where(Chunk.document_id == document_id)
            result = await session.execute(stmt)
            await session.commit()
            chunk = result.scalar_one_or_none()
            return ChunkOut.model_validate(chunk) if chunk else None

    async def delete_chunks_by_document_id(self, document_id: UUID):
        async for session in self.get_session():
            stmt = delete(Chunk).where(Chunk.document_id == document_id)
            result = await session.execute(stmt)
            await session.commit()
            deleted_count = result.rowcount or 0
            return deleted_count > 0