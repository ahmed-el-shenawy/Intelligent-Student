from typing import Dict, Optional, List, Any
from uuid import UUID
import logging

from sqlalchemy import select, delete, func, and_, update
from sqlalchemy.exc import IntegrityError
from sqlalchemy.sql.elements import ClauseElement
from sqlalchemy.ext.asyncio import AsyncSession

from models.postgres.operations_schema import (
    DocumentInsert,
    DocumentOut,
    DocumentDelete,
    DocumentSearch,
    DocumentInsertBulk,
)
from models.postgres.tables_schema.tables import Document

logger = logging.getLogger("DocumentsModel")

class DocumentsModel:
    def __init__(self):
        pass

    # ------------------------- Insert Single Document -------------------------
    async def insert_document(self, db: AsyncSession, doc_data: DocumentInsert) -> DocumentOut:
        logger.info(f"[INSERT] Inserting document '{doc_data.filename}' for project '{doc_data.project_id}'")
        new_doc = Document(
            project_id=doc_data.project_id,
            filename=doc_data.filename,
            doc_metadata=doc_data.metadata,
        )
        db.add(new_doc)
        try:
            await db.commit()
            await db.refresh(new_doc)
            logger.info(f"[INSERT] Success: Document '{doc_data.filename}' inserted")
            return DocumentOut.model_validate(new_doc)
        except IntegrityError as e:
            await db.rollback()
            logger.error(f"[INSERT] Failed: {e}")
            raise ValueError(f"Document '{doc_data.filename}' already exists for project '{doc_data.project_id}'.")

    # ------------------------- Bulk Insert -------------------------
    async def insert_documents_bulk(self, db: AsyncSession, bulk_data: DocumentInsertBulk, batch_size: int = 100) -> List[DocumentOut]:
        logger.info(f"[BULK INSERT] Bulk insert for project '{bulk_data.project_id}', total: {len(bulk_data.documents)}")
        inserted_docs = []

        for i in range(0, len(bulk_data.documents), batch_size):
            batch = bulk_data.documents[i:i + batch_size]
            db_objects = []
            for doc in batch:
                d = Document(project_id=bulk_data.project_id, filename=doc.filename)
                d.metadata_json = doc.metadata
                db_objects.append(d)

            db.add_all(db_objects)
            try:
                await db.commit()
                for doc in db_objects:
                    await db.refresh(doc)
                inserted_docs.extend(db_objects)
                logger.info(f"[BULK INSERT] Inserted batch of {len(db_objects)} documents")
            except IntegrityError as e:
                await db.rollback()
                logger.error(f"[BULK INSERT] Failed batch: {e}")
                raise ValueError("Some documents already exist for this project.")

        return [DocumentOut.model_validate(doc) for doc in inserted_docs]

    # ------------------------- Delete Document -------------------------
    async def del_document(self, db: AsyncSession, doc_data: DocumentDelete) -> Optional[DocumentOut]:
        logger.info(f"[DELETE] Deleting document '{doc_data.filename}' for project '{doc_data.project_id}'")
        stmt = (
            delete(Document)
            .where(and_(Document.filename == doc_data.filename, Document.project_id == doc_data.project_id))
            .returning(Document)
        )
        result = await db.execute(stmt)
        await db.commit()
        deleted_doc = result.scalar_one_or_none()
        if deleted_doc:
            logger.info(f"[DELETE] Success: '{doc_data.filename}' deleted")
            return DocumentOut.model_validate(deleted_doc)
        else:
            logger.warning(f"[DELETE] Document '{doc_data.filename}' not found")
            return None

    # ------------------------- List Documents -------------------------
    async def list_documents(self, db: AsyncSession, project_id: UUID, offset: int = 0, limit: int = 10) -> Dict[str, Any]:
        return await self._list_documents(db, [Document.project_id == project_id], offset, limit)

    async def list_processed_documents(self, db: AsyncSession, project_id: UUID, offset: int = 0, limit: int = 10) -> Dict[str, Any]:
        return await self._list_documents(db, [Document.project_id == project_id, Document.is_processed == True], offset, limit)

    async def list_unprocessed_documents(self, db: AsyncSession, project_id: UUID, offset: int = 0, limit: int = 10) -> Dict[str, Any]:
        return await self._list_documents(db, [Document.project_id == project_id, Document.is_processed == False], offset, limit)

    async def list_flushed_documents(self, db: AsyncSession, project_id: UUID, offset: int = 0, limit: int = 10) -> Dict[str, Any]:
        return await self._list_documents(db, [Document.project_id == project_id, Document.is_flushed == True], offset, limit)

    async def list_unflushed_documents(self, db: AsyncSession, project_id: UUID, offset: int = 0, limit: int = 10) -> Dict[str, Any]:
        return await self._list_documents(db, [Document.project_id == project_id, Document.is_flushed == False], offset, limit)

    async def _list_documents(self, db: AsyncSession, filters: Optional[List[ClauseElement]] = None, offset: int = 0, limit: int = 10) -> Dict[str, Any]:
        stmt = select(Document, func.count().over().label("total_count")).where(*filters).offset(offset).limit(limit)
        result = await db.execute(stmt)
        rows = result.all()
        total_count = rows[0].total_count if rows else 0
        items = [DocumentOut.model_validate(doc) for doc, _ in rows]
        logger.info(f"[LIST] Retrieved {len(items)} documents (offset={offset}, limit={limit})")
        return {"total": total_count, "offset": offset, "limit": limit, "items": items}

    # ------------------------- Search Document -------------------------
    async def search_document(self, db: AsyncSession, doc_data: DocumentSearch) -> Optional[DocumentOut]:
        stmt = select(Document).where(and_(Document.project_id == doc_data.project_id, Document.filename == doc_data.filename))
        result = await db.execute(stmt)
        document = result.scalar_one_or_none()
        return DocumentOut.model_validate(document) if document else None

    # ------------------------- Update Document (processed) -------------------------
    async def update_document(self, db: AsyncSession, document_id: int) -> Optional[DocumentOut]:
        stmt = update(Document).where(Document.id == document_id).values(is_processed=True).returning(Document)
        result = await db.execute(stmt)
        await db.commit()
        document = result.scalar_one_or_none()
        return DocumentOut.model_validate(document) if document else None

    # ------------------------- Flush Document -------------------------
    async def flush_document(self, db: AsyncSession, document_id: int) -> Optional[DocumentOut]:
        stmt = update(Document).where(Document.id == document_id).values(is_flushed=True).returning(Document)
        result = await db.execute(stmt)
        await db.commit()
        document = result.scalar_one_or_none()
        return DocumentOut.model_validate(document) if document else None
