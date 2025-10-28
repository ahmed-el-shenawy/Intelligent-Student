from pydantic import BaseModel, Field
from typing import Optional
from uuid import UUID

# ----------------------------
# Chunk Operations Schemas
# ----------------------------

class ChunkInsert(BaseModel):
    """
    Schema for inserting a new chunk into the database.

    Attributes:
        document_id (UUID): The ID of the parent document.
        chunk_text (str): The actual text content of the chunk.
        chunk_metadata (Optional[dict]): Optional JSON metadata for the chunk.
        chunk_index (int): The index/order of this chunk within the document.
    """
    document_id: UUID
    chunk_text: str
    chunk_metadata: Optional[dict] = None
    chunk_index: int


class ChunkGet(BaseModel):
    """
    Schema for fetching or deleting chunks by ID.

    Attributes:
        id (UUID): Unique identifier of the chunk.
    """
    id: UUID


class ChunkResponse(BaseModel):
    """
    Schema for returning chunk data from the database.

    Attributes:
        id (UUID): Unique identifier of the chunk.
        document_id (UUID): The ID of the parent document.
        chunk_text (str): The text content of the chunk.
        chunk_metadata (Optional[dict]): Optional metadata of the chunk.
        chunk_index (int): The index/order of this chunk within the document.
    """
    id: UUID
    document_id: UUID
    chunk_text: str
    chunk_metadata: Optional[dict] = None
    chunk_index: int

    # Allows Pydantic to populate this model from ORM objects
    model_config = {"from_attributes": True}
