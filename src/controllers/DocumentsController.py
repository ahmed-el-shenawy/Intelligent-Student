from models.postgres.operations_schema.projects import ProjectSearch
from .BaseController import BaseController
from models.postgres.DocumentsModel import DocumentsModel
from models.postgres.VectorsModel import VectorModel
from models.postgres.ProjectsModel import ProjectModel
from models.postgres.ChunksModel import ChunksModel
from models.postgres.operations_schema import VectorInsertItems
from models.postgres.operations_schema.documents import DocumentInsert, DocumentInsertBulk, DocumentSearch,DocumentDelete
from models.postgres.operations_schema.chunks import ChunkInsert
from routes.schemes.documents import DocumentProcessRequest,DocumentDelRequest
from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from models.postgres.tables_schema.vectors import metadata
from helpers.db_connection import engine
from fastapi import UploadFile
from pgvector.sqlalchemy import Vector
from helpers import settings
from typing import List
import hashlib
import magic
import re
from uuid import UUID
from pathlib import Path

import logging

logger = logging.getLogger(__name__)
doc_model = DocumentsModel()
project_model = ProjectModel()
vec_model = VectorModel()
chunk_model = ChunksModel()

class DocumentsController(BaseController):
    def __init__(self):
        super().__init__()
        self.max_file_size_bytes = settings.MAX_FILE_SIZE_MB * 1024 * 1024
        self.allowed_mime_types = settings.ALLOWED_MIME_TYPES

    def file_hash(self, content: bytes) -> str:
        """
        Compute a SHA256 hash of the given file content.

        Args:
            content (bytes): The binary content of the file.

        Returns:
            str: Hexadecimal string representation of the SHA256 hash.
        """
        sha256 = hashlib.sha256()
        sha256.update(content)
        return sha256.hexdigest()

    def validate_content_type(self, file: UploadFile)-> str:
        """
        Validate the MIME type of the uploaded file.

        This function reads a small portion of the file to detect its MIME type
        using the `python-magic` library and compares it with allowed types.

        Args:
            file (UploadFile): The uploaded file object.

        Raises:
            HTTPException: If the file type is not allowed.
        """
        mime = magic.Magic(mime=True)
        content_type = mime.from_buffer(file.file.read(1024))
        file.file.seek(0)

        if content_type not in self.allowed_mime_types:
            raise ValueError("Only PDF files are allowed.")
        return content_type     

    def validate_file_size(self, file: UploadFile) -> int:
        """
        Validate that the uploaded file does not exceed the maximum allowed size.

        This method reads the file in small chunks to prevent memory overload
        and ensure the total size remains within the defined limit.

        Args:
            file (UploadFile): The uploaded file object.

        Raises:
            HTTPException: If the file size exceeds the configured maximum.
        """
        file_size = 0
        while chunk := file.file.read(1024):
            file_size += len(chunk)
            if file_size > self.max_file_size_bytes:
                raise ValueError(f"{file.filename} size exceeds the {settings.MAX_FILE_SIZE_MB} MB limit.")
        file.file.seek(0)
        return file_size

    def validate_filename(self,filename: str) -> str:
        """
        Validate filename to only contain alphanumeric characters, underscores, and an optional extension.
        Raises HTTPException if invalid.
        """
        name = Path(filename).name  # Remove any directory parts
        
        # Regex: allow letters, digits, underscores, and a single optional dot for extension
        if not re.match(r'^[A-Za-z0-9_]+(\.[A-Za-z0-9_]+)?$', name):
            raise ValueError(f"Invalid filename '{filename}'. Only letters, digits, and underscores are allowed.")
        return name

    async def upload_docs(self, project_name: str, files: List[UploadFile]):
        #Check if project exist
        project_search = ProjectSearch(name = project_name)
        project = await project_model.search_by_name(data = project_search)
        if not project:
            raise ValueError(f"Project '{project_name}' does not exist")

        #Validate files
        names = []
        sizes = []
        types = []
        for f in files:
            try:
                sizes.append(self.validate_file_size(f))
                types.append(self.validate_content_type(f))
                names.append(self.validate_filename(f.filename))
                f.file.seek(0)
            except ValueError as e:
                raise ValueError(e)

        #Upload files into the disk
        project_path = self.ASSETS_DIR / project_name
        project_path.mkdir(parents=True, exist_ok=True)
        file_paths = [project_path / name for name in names]
        for i, file_path in enumerate(file_paths):
            with file_path.open("wb") as f:
                f.write(await files[i].read())

        #Insert into db
        docs = [DocumentInsert(filename=name, metadata={"size":sizes[i], "type":types[i]}) for i, name in enumerate(names)]
        bulk_docs = DocumentInsertBulk(project_id=project.id, documents=docs)
        inserted_docs = await doc_model.insert_documents_bulk(bulk_docs)
        return inserted_docs

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

    async def process_docs(self, client, project_name: str, file_names: List[str], chunk_size: int, chunk_overlap: int):
        project_search = ProjectSearch(name = project_name)
        project = await project_model.search_by_name(data = project_search)
        if not project:
            raise ValueError(f"Project '{project_name}' does not exist")

        for file_name in file_names:
            try:
                doc = await self.get_by_project_id_and_filename(project_id=project.id, filename=file_name)
                if not doc:
                    raise ValueError(f"File {file_name} is not found in {project_name}")
                if doc.is_flushed:
                    raise ValueError(f"The file ({file_name}) is flushed from the disk.If you need to process it -> delete it and upload it again so you can process it")
                if doc.is_processed:
                    await chunk_model.delete_chunks_by_document_id(document_id = doc.id)

                chunks = self.load_and_chunk_pdf(
                    project_name=project_name,
                    file_name=file_name,
                    chunk_size=chunk_size,
                    chunk_overlap=chunk_overlap
                )

                insert_chunks = [
                    ChunkInsert(
                        document_id=doc.id,
                        text=chunk["text"],
                        metadata_json={
                            "filename": file_name,
                            "page_number": chunk["page_number"],
                            "chunk_order": chunk["chunk_order"]
                        }
                    )
                    for chunk in chunks
                ]

                #Insert chunks into DB
                await chunk_model.delete_chunks_by_document_id(document_id=doc.id)
                done_chunks = await chunk_model.insert_chunks(insert_chunks)

                # Extract chunk texts & IDs
                chunk_texts = [chunk.text for chunk in done_chunks]
                chunk_ids = [chunk.id for chunk in done_chunks]

                # ✅ Compute embeddings
                vectors = client.embed(chunk_texts)
                # Ensure proper list format


                # ✅ Prepare vector insertion data
                vectors_data = VectorInsertItems(
                    project_id=project.id,
                    document_id=doc.id,
                    chunk_id=chunk_ids,
                    vectors=vectors
                )

                # ✅ Insert vectors into dynamic table
                await vec_model.insert_vectors(data=vectors_data)
                updated_doc = await doc_model.update_document(document_id=doc.id)
                

            except Exception as e:
                raise ValueError(e)

        return updated_doc

    async def get_by_project_id_and_filename(self, project_id:UUID, filename:str):
        doc = await doc_model.search_document(DocumentSearch(project_id=project_id,filename=filename))
        return doc
    
    
    async def get_docs(self, project_name:str, filter:str , offset: int = 0, limit: int = 10):
        project_search = ProjectSearch(name = project_name)
        project = await project_model.search_by_name(data = project_search)
        if not project:
            raise ValueError(f"project {project_name} does not exist")
        match filter:
            case "all":
                result = await doc_model.list_documents(project_id=project.id, offset=offset, limit=limit)
            case "processed":
                result = await doc_model.list_processed_documents(project_id=project.id, offset=offset, limit=limit)
            case "unprocessed":
                result = await doc_model.list_unprocessed_documents(project_id=project.id, offset=offset, limit=limit)
            case "flushed":
                result = await doc_model.list_flushed_documents(project_id=project.id, offset=offset, limit=limit)
            case "unflushed":
                result = await doc_model.list_unflushed_documents(project_id=project.id, offset=offset, limit=limit)
        return result
    
    async def del_by_project_id_and_filename(self, del_data: DocumentDelRequest):
        project_search = ProjectSearch(name = del_data.project_name)
        project = await project_model.search_by_name( data=project_search)
        if not project:
            raise ValueError(f"Project {del_data.project_name} does not exist")

        # Step 2: Build DocumentDelete using the project ID
        doc_data = DocumentDelete(
            project_id=project.id,  # fetched from DB
            filename=del_data.filename
        )
        
        file_path = self.ASSETS_DIR / del_data.project_name / del_data.filename
        if file_path.exists():
            file_path.unlink()

        # Step 3: Delete the document
        doc = await doc_model.del_document(doc_data)

        return doc
    
    async def flush_documents(self, project_name:str, filenames:List[str]):
        try:
            project_search = ProjectSearch(name = project_name)
            project = await project_model.search_by_name(data = project_search)
            for file in filenames:
                file_path = self.ASSETS_DIR / project_name / file
                if file_path.exists():
                    file_path.unlink()
                doc = await self.get_by_project_id_and_filename(project_id=project.id, filename=file)
                updated_doc = await doc_model.flush_document(document_id= doc.id)
            return updated_doc
        except ValueError as e:
            raise ValueError(e)
