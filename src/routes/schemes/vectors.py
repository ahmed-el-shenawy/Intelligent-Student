# src/models/postgres/operations_schema.py
from pydantic import BaseModel, Field
from typing import List
from uuid import UUID

# ----------------------------
# Bulk insert vectors/documents
# ----------------------------
class VectorInsertItem(BaseModel):
    """
    Represents vectors for a single document.

    Attributes:
        project_table (str): Name of the table to check in the database.
        document_id (UUID): ID of the document.
        vectors (List[List[float]]): List of vector embeddings for the document's chunks.
    """
    project_table: str = Field(..., min_length=1)
    document_id: UUID
    vectors: List[List[float]] = Field(..., min_items=1)


# ----------------------------
# Delete vectors/documents
# ----------------------------
class VectorDelete(BaseModel):
    """
    Schema for deleting vectors/documents by document ID.

    Attributes:
        project_table (str): Name of the table to check in the database.
        document_id (UUID): The document ID for which all associated vectors should be deleted.
    """
    project_table: str = Field(..., min_length=1)
    document_id: UUID


# ----------------------------
# Check project table existence
# ----------------------------
class ProjectTableCheck(BaseModel):
    """
    Schema for checking if a project table exists.

    Attributes:
        project_table (str): Name of the table to check in the database.
    """
    project_table: str = Field(..., min_length=1)
