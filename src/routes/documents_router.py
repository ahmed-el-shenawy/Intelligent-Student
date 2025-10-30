from fastapi import APIRouter, Request, UploadFile, File, Depends
from typing import List
from sqlalchemy.ext.asyncio import AsyncSession

from controllers.DocumentsController import DocumentsController
from helpers.deps import get_current_user
from helpers.handle_exceptions import handle_exceptions
from helpers.db_connection import get_db
from routes.schemes.documents import DocumentFlushRequest, DocumentProcessRequest, DocumentGetRequest, DocumentDelRequest, DocumentSearch

documents_router = APIRouter(prefix="/documents", tags=["Documents"])
doc_controller = DocumentsController()

@documents_router.post("/upload/{project_name}")
@handle_exceptions
async def upload_documents(project_name: str, files: List[UploadFile] = File(...), db: AsyncSession = Depends(get_db), current_user=Depends(get_current_user)):
    return await doc_controller.upload_docs(db, project_name, files)

@documents_router.post("/process")
@handle_exceptions
async def process_documents(request:Request, data: DocumentProcessRequest, db: AsyncSession = Depends(get_db), current_user=Depends(get_current_user)):
    client = request.app.state.embedding_client
    if not client:
        raise ValueError("Embedding client not initialized")
    return await doc_controller.process_docs(db, client=client, project_name=data.project_name, file_names=data.file_names, chunk_size=data.chunk_size, chunk_overlap=data.chunk_overlap)

@documents_router.post("/flush")
@handle_exceptions
async def flush_documents(data: DocumentFlushRequest, db: AsyncSession = Depends(get_db), current_user=Depends(get_current_user)):
    return await doc_controller.flush_documents(db, data.project_name, data.file_names)

@documents_router.post("/delete")
@handle_exceptions
async def delete_documents(data: DocumentDelRequest, db: AsyncSession = Depends(get_db), current_user=Depends(get_current_user)):
    return await doc_controller.del_by_project_id_and_filename(db, data)

@documents_router.get("")
@handle_exceptions
async def list_documents(data: DocumentGetRequest, db: AsyncSession = Depends(get_db), current_user=Depends(get_current_user)):
    return await doc_controller.get_docs(db, data.project_name, data.filter, data.offset, data.limit)

@documents_router.post("/search")
@handle_exceptions
async def search_documents(data: DocumentSearch, db: AsyncSession = Depends(get_db), current_user=Depends(get_current_user)):
    doc = await doc_controller.get_by_project_id_and_filename(db, data.project_id, data.filename)
    if not doc:
        raise FileNotFoundError(f"Document '{data.filename}' not found")
    return doc

@documents_router.delete("")
@handle_exceptions
async def delete_document(data: DocumentDelRequest, db: AsyncSession = Depends(get_db), current_user=Depends(get_current_user)):
    return await doc_controller.del_by_project_id_and_filename(db, data)