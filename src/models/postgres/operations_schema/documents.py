# operations_schema.py
from pydantic import BaseModel, Field
from typing import Optional
from uuid import UUID
from datetime import datetime

class DocumentInsert(BaseModel):
    filename: str = Field(..., max_length=255, description="Document filename")
    metadata: Optional[dict]

    model_config = {"from_attributes": True}

class DocumentInsertBulk(BaseModel):
    project_id: UUID
    documents: list[DocumentInsert]

    model_config = {"from_attributes": True}

class DocumentUpdate(BaseModel):
    document_id: UUID

    model_config = {"from_attributes": True}

# ----------------------------
# Document Delete Schema
# ----------------------------
class DocumentDelete(BaseModel):
    project_id: UUID = Field(..., description="Project ID to which the document belongs")
    filename: str = Field(..., description="Filename of the document to delete")


# ----------------------------
# Document Search Schema
# ----------------------------
class DocumentSearch(BaseModel): 
    project_id: UUID = Field(..., description="Project ID to search in")
    filename: str = Field(..., description="Filename to search for")


# ----------------------------
# Document Output Schema
# ----------------------------
class DocumentOut(BaseModel):
    id: UUID
    project_id: UUID
    filename: str
    metadata_json: Optional[dict] = None
    is_processed: bool
    is_flushed: bool
    created_at: datetime

    model_config = {"from_attributes": True}
