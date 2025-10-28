from pydantic import BaseModel, Field
from typing import Optional
from uuid import UUID

# ----------------------------
# Chunk Operations Schemas
# ----------------------------

class ChunkInsert(BaseModel):
    document_id: UUID
    text: str
    metadata_json: Optional[dict] = None

    model_config = {"from_attributes": True}


class ChunkOut(BaseModel):
    id: UUID
    document_id: UUID
    text: str
    chunk_metadata: Optional[dict] = None

    model_config = {"from_attributes": True}
