import hashlib
import magic
import re
from pathlib import Path
from typing import List
from uuid import UUID

from fastapi import UploadFile
from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from sqlalchemy.ext.asyncio import AsyncSession

from .BaseController import BaseController
from models.postgres.operations_schema.projects import ProjectSearch
from models.postgres.DocumentsModel import DocumentsModel
from models.postgres.VectorsModel import VectorModel
from models.postgres.ProjectsModel import ProjectModel
from models.postgres.ChunksModel import ChunksModel
from models.postgres.operations_schema import VectorInsertItems
from models.postgres.operations_schema.documents import DocumentInsert, DocumentInsertBulk, DocumentSearch, DocumentDelete
from models.postgres.operations_schema.chunks import ChunkInsert
from routes.schemes.documents import DocumentDelRequest
from helpers import settings
from helpers.logger import get_logger

logger = get_logger("DocumentsController")


class DocumentsController(BaseController):
    def __init__(self):
        super().__init__()
        self.max_file_size_bytes = settings.MAX_FILE_SIZE_MB * 1024 * 1024
        self.allowed_mime_types = settings.ALLOWED_MIME_TYPES
        self.ASSETS_DIR = Path("assets")

    # ------------------------- Helpers -------------------------
    def validate_content_type(self, file: UploadFile) -> str:
        mime = magic.Magic(mime=True)
        content_type = mime.from_buffer(file.file.read(1024))
        file.file.seek(0)

        if content_type not in self.allowed_mime_types:
            raise ValueError(f"[FAIL] File '{file.filename}' type '{content_type}' not allowed.")
        return content_type

    def validate_file_size(self, file: UploadFile) -> int:
        file_size = 0
        while chunk := file.file.read(1024):
            file_size += len(chunk)
            if file_size > self.max_file_size_bytes:
                raise ValueError(f"[FAIL] '{file.filename}' exceeds {settings.MAX_FILE_SIZE_MB} MB limit.")
        file.file.seek(0)
        return file_size

    def validate_filename(self, filename: str) -> str:
        name = Path(filename).name
        if not re.match(r"^[A-Za-z0-9_]+(\.[A-Za-z0-9_]+)?$", name):
            raise ValueError(f"[FAIL] Invalid filename '{filename}'. Only letters, digits, underscores allowed.")
        return name
    
    def load_and_chunk_pdf(self, project_name: str, file_name: str, chunk_size: int = 1000, chunk_overlap: int = 150):
        pdf_path =  self.ASSETS_DIR/project_name/file_name
        if not pdf_path.exists():
            raise FileNotFoundError(f"File not found: {file_name} in project {project_name}")

        loader = PyPDFLoader(str(pdf_path))
        docs = loader.load()

        splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap)
        chunks = splitter.split_documents(docs)

        chunked_data = []
        for idx, chunk in enumerate(chunks):
            page_number = chunk.metadata.get("page", 0) + 1 

            chunked_data.append({
                "chunk_order": idx,
                "page_number": page_number,
                "text": chunk.page_content.strip()
            })

        return chunked_data

    # ------------------------- Upload Documents -------------------------
    async def upload_docs(self, db: AsyncSession, project_name: str, files: List[UploadFile]):
        project_search = ProjectSearch(name=project_name)
        project = await ProjectModel().search_by_name(db, project_search)
        if not project:
            raise ValueError(f"Project '{project_name}' does not exist")

        names, sizes, types = [], [], []
        duplicates = []

        for f in files:
            sizes.append(self.validate_file_size(f))
            types.append(self.validate_content_type(f))
            name = self.validate_filename(f.filename)

            # check duplicate
            exists = await DocumentsModel().search_document(db, DocumentSearch(project_id=project.id, filename=name))
            if exists:
                duplicates.append(name)
            else:
                names.append(name)

        if not names:
            raise ValueError(f"All uploaded files already exist: {', '.join(duplicates)}")

        project_path = self.ASSETS_DIR / project_name
        project_path.mkdir(parents=True, exist_ok=True)

        for i, name in enumerate(names):
            file_path = project_path / name
            with file_path.open("wb") as fp:
                fp.write(await files[i].read())

        docs = [
            DocumentInsert(filename=name, metadata={"size": sizes[i], "type": types[i]})
            for i, name in enumerate(names)
        ]
        bulk_docs = DocumentInsertBulk(project_id=project.id, documents=docs)
        inserted_docs = await DocumentsModel().insert_documents_bulk(db, bulk_docs)

        msg = f"Uploaded {len(inserted_docs)} file(s) successfully"
        if duplicates:
            msg += f"; skipped duplicates: {', '.join(duplicates)}"

        return {"message": msg, "data": inserted_docs}


    # ------------------------- Process Documents -------------------------
    async def process_docs(self, db: AsyncSession, client, project_name: str, file_names: List[str], chunk_size: int = 1000, chunk_overlap: int = 150):
        project_search = ProjectSearch(name=project_name)
        project = await ProjectModel().search_by_name(db, project_search)
        if not project:
            raise ValueError(f"Project '{project_name}' does not exist")

        updated_docs = []

        for file_name in file_names:
            doc = await self.get_by_project_id_and_filename(db, project.id, file_name)
            if not doc:
                raise ValueError(f"File '{file_name}' not found")
            if doc["data"].is_flushed:
                raise ValueError(f"File '{file_name}' is flushed. Re-upload to process.")
            if doc["data"].is_processed:
                await ChunksModel().delete_chunks_by_document_id(db, doc["data"].id)

            chunks = self.load_and_chunk_pdf(project_name, file_name, chunk_size, chunk_overlap)
            insert_chunks = [
                ChunkInsert(
                    document_id=doc["data"].id,
                    text=chunk["text"],
                    metadata_json={
                        "filename": file_name,
                        "page_number": chunk["page_number"],
                        "chunk_order": chunk["chunk_order"]
                    },
                )
                for chunk in chunks
            ]

            await ChunksModel().delete_chunks_by_document_id(db, doc["data"].id)
            done_chunks = await ChunksModel().insert_chunks(db, insert_chunks)

            chunk_texts = [c.text for c in done_chunks]
            chunk_ids = [c.id for c in done_chunks]

            vectors = client.embed(chunk_texts)
            vectors_data = VectorInsertItems(
                project_id=project.id, document_id=doc["data"].id, chunk_id=chunk_ids, vectors=vectors
            )
            await VectorModel().insert_vectors(db, vectors_data)

            updated_doc = await DocumentsModel().update_document(db, doc["data"].id)
            updated_docs.append(updated_doc)

        return {"message": f"Processed {len(updated_docs)} file(s) successfully", "data": updated_docs}

    # ------------------------- Get Document -------------------------
    async def get_by_project_id_and_filename(self, db: AsyncSession, project_id: UUID, filename: str):
        doc = await DocumentsModel().search_document(db, DocumentSearch(project_id=project_id, filename=filename))
        return {"message": "Document retrieved", "data": doc}

    async def get_docs(self, db: AsyncSession, project_name: str, filter: str, offset: int = 0, limit: int = 10):
        project_search = ProjectSearch(name=project_name)
        project = await ProjectModel().search_by_name(db, project_search)
        if not project:
            raise ValueError(f"Project '{project_name}' does not exist")

        match filter:
            case "all":
                docs = await DocumentsModel().list_documents(db, project.id, offset, limit)
            case "processed":
                docs = await DocumentsModel().list_processed_documents(db, project.id, offset, limit)
            case "unprocessed":
                docs = await DocumentsModel().list_unprocessed_documents(db, project.id, offset, limit)
            case "flushed":
                docs = await DocumentsModel().list_flushed_documents(db, project.id, offset, limit)
            case "unflushed":
                docs = await DocumentsModel().list_unflushed_documents(db, project.id, offset, limit)

        return {"message": f"Retrieved documents with filter '{filter}'", "data": docs}

    # ------------------------- Delete Document -------------------------
    async def del_by_project_id_and_filename(self, db: AsyncSession, del_data: DocumentDelRequest):
        project_search = ProjectSearch(name=del_data.project_name)
        project = await ProjectModel().search_by_name(db, project_search)
        if not project:
            raise ValueError(f"Project '{del_data.project_name}' does not exist")

        doc_data = DocumentDelete(project_id=project.id, filename=del_data.filename)
        file_path = self.ASSETS_DIR / del_data.project_name / del_data.filename
        if file_path.exists():
            file_path.unlink()

        deleted_doc = await DocumentsModel().del_document(db, doc_data)
        return {"message": f"Deleted document '{del_data.filename}'", "data": deleted_doc}

    # ------------------------- Flush Documents -------------------------
    async def flush_documents(self, db: AsyncSession, project_name: str, filenames: List[str]):
        project_search = ProjectSearch(name=project_name)
        project = await ProjectModel().search_by_name(db, project_search)
        if not project:
            raise ValueError(f"Project '{project_name}' does not exist")

        updated_docs = []
        for file in filenames:
            file_path = self.ASSETS_DIR / project_name / file
            if file_path.exists():
                file_path.unlink()
            doc = await self.get_by_project_id_and_filename(db, project.id, file)
            if doc["data"]:
                updated_doc = await DocumentsModel().flush_document(db, doc["data"].id)
                updated_docs.append(updated_doc)

        return {"message": f"Flushed {len(updated_docs)} document(s)", "data": updated_docs}
