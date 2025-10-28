from typing import Dict, Optional, List, Any
from uuid import UUID
import logging

from sqlalchemy import select, delete, func, and_, update
from sqlalchemy.exc import IntegrityError

from sqlalchemy.sql.elements import ClauseElement

from models.postgres.operations_schema.documents import DocumentUpdate
from .BaseModel import BaseModel
from models.postgres.operations_schema import (
    DocumentInsert,
    DocumentOut,
    DocumentDelete,
    DocumentSearch,
    DocumentInsertBulk,
)
from models.postgres.tables_schema .tables import Document

logger = logging.getLogger(__name__)


class DocumentsModel(BaseModel):
    def __init__(self):
        super().__init__()

    async def insert_document(self, doc_data: DocumentInsert) -> DocumentOut:
        async for session in self.get_session():
            new_doc = Document(
                project_id=doc_data.project_id,
                filename=doc_data.filename,
                doc_metadata=doc_data.metadata,
            )
            session.add(new_doc)
            try:
                await session.commit()
                await session.refresh(new_doc)
                return DocumentOut.model_validate(new_doc)
            except IntegrityError as e:
                await session.rollback()
                logger.error(f"Failed to insert document '{doc_data.filename}': {e}")
                raise ValueError(f"Failed to insert document '{doc_data.filename}' for project '{doc_data.project_id}'.")

    async def insert_documents_bulk(
        self,
        bulk_data: DocumentInsertBulk,
        batch_size: int = 100
    ) -> List[DocumentOut]:
        inserted_docs = []

        async for session in self.get_session():
            for i in range(0, len(bulk_data.documents), batch_size):
                batch = bulk_data.documents[i:i + batch_size]

            db_objects = []
            for doc in batch:
                d = Document(
                    project_id=bulk_data.project_id,
                    filename=doc.filename
                )
                d.metadata_json = doc.metadata  # assign separately
                db_objects.append(d)

                session.add_all(db_objects)
                try:
                    await session.commit()
                    for doc in db_objects:
                        await session.refresh(doc)
                    inserted_docs.extend(db_objects)
                except IntegrityError as e:
                    await session.rollback()
                    logger.error(f"Bulk insert batch failed due to duplicates: {e}")
                    raise ValueError("Some documents already exist for this project.")

        return [DocumentOut.model_validate(doc) for doc in inserted_docs]

    async def del_document(self, doc_data: DocumentDelete) -> Optional[DocumentOut]:
        async for session in self.get_session():
            stmt = (
                delete(Document)
                .where(
                    and_(
                        Document.filename == doc_data.filename,
                        Document.project_id == doc_data.project_id,
                    )
                )
                .returning(Document)
            )
            result = await session.execute(stmt)
            await session.commit()
            deleted_doc = result.scalar_one_or_none()
            return DocumentOut.model_validate(deleted_doc) if deleted_doc else None

    async def _list_documents(
        self,
        filters: Optional[List[ClauseElement]] = None,
        offset: int = 0,
        limit: int = 10,
    ) -> Dict[str, Any]:
        filters = filters or []

        async for session in self.get_session():
            stmt = (
                select(Document, func.count().over().label("total_count"))
                .where(*filters)
                .offset(offset)
                .limit(limit)
            )
            result = await session.execute(stmt)
            rows = result.all()

            total_count = rows[0].total_count if rows else 0
            items = [DocumentOut.model_validate(doc) for doc, _ in rows]

            return {
                "total": total_count,
                "offset": offset,
                "limit": limit,
                "items": items,
            }

    async def list_documents(self, project_id: UUID, offset: int = 0, limit: int = 10) -> Dict:
        return await self._list_documents(
            filters=[Document.project_id == project_id],
            offset=offset,
            limit=limit
        )
    async def list_flushed_documents(self, project_id: UUID, offset: int = 0, limit: int = 10) -> Dict:
        return await self._list_documents(
            filters=[Document.project_id == project_id, Document.is_flushed == True],
            offset=offset,
            limit=limit
        )

    async def list_unflushed_documents(self, project_id: UUID, offset: int = 0, limit: int = 10) -> Dict:
        return await self._list_documents(
            filters=[Document.project_id == project_id, Document.is_flushed == False],
            offset=offset,
            limit=limit
        )
    
    async def list_processed_documents(self, project_id: UUID, offset: int = 0, limit: int = 10) -> Dict:
        return await self._list_documents(
            filters=[Document.project_id == project_id, Document.is_processed == True],
            offset=offset,
            limit=limit
        )    
    
    async def list_unprocessed_documents(self, project_id: UUID, offset: int = 0, limit: int = 10) -> Dict:
        return await self._list_documents(
            filters=[Document.project_id == project_id, Document.is_processed == False],
            offset=offset,
            limit=limit
        )

    async def search_document(self, doc_data: DocumentSearch) -> DocumentOut:
        async for session in self.get_session():
            stmt = select(Document).where(
                and_(
                    Document.project_id == doc_data.project_id,
                    Document.filename == doc_data.filename
                )
            )
            result = await session.execute(stmt)
            document = result.scalar_one_or_none() 
            return DocumentOut.model_validate(document) if document else None

    async def update_document(self, document_id: int) -> Optional[DocumentOut]:
        async for session in self.get_session():
            stmt = (
                update(Document)
                .where(Document.id == document_id)
                .values(is_processed=True)
                .returning(Document)
            )

            result = await session.execute(stmt)
            await session.commit()

            document = result.scalar_one_or_none()
            return DocumentOut.model_validate(document) if document else None

    async def flush_document(self, document_id: int) -> Optional[DocumentOut]:
        async for session in self.get_session():
            stmt = (
                update(Document)
                .where(Document.id == document_id)
                .values(is_flushed=True)
                .returning(Document)
            )

            result = await session.execute(stmt)
            await session.commit()

            document = result.scalar_one_or_none()
            return DocumentOut.model_validate(document) if document else None