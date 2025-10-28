# operations_schema.py
from enum import Enum
from fastapi import UploadFile
from pydantic import BaseModel, Field
from typing import Optional, List
from uuid import UUID
from datetime import datetime

class DocumentProcessRequest(BaseModel):
    project_name: str
    chunk_size: int
    chunk_overlap: int
    file_names: List[str]

    model_config = {"from_attributes": True}

class DocumentFlushRequest(BaseModel):
    project_name: str
    file_names: List[str]

    model_config = {"from_attributes": True}

class DocumentDelete(BaseModel):
    project_id: UUID
    filename: List[str]

    model_config = {"from_attributes": True}

class DocumentFilter(str, Enum):
    all = "all"
    processed = "processed"
    unprocessed = "unprocessed"
    flushed = "flushed"
    unflushed = "unflushed"

class DocumentGetRequest(BaseModel):
    project_name: str
    offset: int
    limit: int
    filter: DocumentFilter = DocumentFilter.all

    model_config = {"from_attributes": True}

class DocumentSearch(BaseModel):
    project_id: UUID
    filename: str

    model_config = {"from_attributes": True}

class DocumentOut(BaseModel):
    id: UUID
    project_id: UUID
    filename: str
    metadata_json: Optional[dict] = None
    is_processed: bool
    created_at: datetime

    model_config = {"from_attributes": True}

class DocumentDelRequest(BaseModel):
    project_name: str
    filename: str

    model_config = {"from_attributes": True}