from fastapi import APIRouter, HTTPException, UploadFile, File, Request
from typing import List

from fastapi.encoders import jsonable_encoder
from fastapi.responses import JSONResponse
from controllers import DocumentsController
from .schemes.documents import DocumentFlushRequest, DocumentProcessRequest, DocumentGetRequest, DocumentDelRequest, DocumentSearch

doc_controller = DocumentsController()

documents_router = APIRouter(prefix="/documents")

@documents_router.post("/upload/{project_name}")
async def upload_documents(project_name: str, files: List[UploadFile] = File(...)):
    try:
        result = await doc_controller.upload_docs(project_name, files)
        return JSONResponse(
            content={"status": "success", "data": jsonable_encoder(result)},
            status_code=200
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@documents_router.post("/process")
async def process_documents(request: Request, data: DocumentProcessRequest):
    try:
        client = request.app.state.embedding_client
        result = await doc_controller.process_docs(client = client,
                                                    project_name = data.project_name,
                                                    file_names= data.file_names,
                                                    chunk_size=data.chunk_size,
                                                    chunk_overlap=data.chunk_overlap)
        return JSONResponse(
            content={"status": "success","processed_doc": jsonable_encoder(result) },
            status_code=200
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    
@documents_router.post("/flush")
async def process_documents( data: DocumentFlushRequest):
    try:
        result = await doc_controller.flush_documents( project_name = data.project_name,
                                                    filenames= data.file_names,)
        return JSONResponse(
            content={"status": "success","Flushed documents": jsonable_encoder(result) },
            status_code=200
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    
@documents_router.post("/search")
async def delete_documents(search_data:DocumentSearch ):
    try:
        del_item = await doc_controller.del_by_project_id_and_filename(search_data)
        if not del_item:
                return JSONResponse(
                content={"status": "not found"},
                status_code=404
                )
        return JSONResponse(
                content={"status": "successfully deleted", "data": jsonable_encoder(del_item)},
                status_code=200
            )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@documents_router.get("")
async def list_documents(get_data: DocumentGetRequest):
    try:
        result = await doc_controller.get_docs(get_data.project_name, offset=get_data.offset, limit=get_data.limit, filter=get_data.filter)
        if not result:
            return JSONResponse(
            content={"status": "not found"},
            status_code=404
            )
        return JSONResponse(
            content={"status": "success", "data": jsonable_encoder(result)},
            status_code=200
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@documents_router.delete("")
async def delete_documents(del_data:DocumentDelRequest ):
    try:
        del_item = await doc_controller.del_by_project_id_and_filename(del_data)
        if not del_item:
                return JSONResponse(
                content={"status": "not found"},
                status_code=404
                )
        return JSONResponse(
                content={"status": "successfully deleted", "data": jsonable_encoder(del_item)},
                status_code=200
            )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    
