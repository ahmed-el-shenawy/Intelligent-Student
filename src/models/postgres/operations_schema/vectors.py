# src/models/postgres/operations_schema.py
from pydantic import BaseModel, Field
from typing import List
from uuid import UUID
from typing import Optional

class VectorInsertItems(BaseModel):
    project_id: UUID
    document_id: UUID
    chunk_id: List[UUID]
    vectors: List[List[float]] = Field(..., min_items=1)

    model_config = {"from_attributes": True}

class VectorOut(BaseModel):
    text: str
    distance: float


