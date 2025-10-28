from sqlalchemy import Table, Column, Integer, ForeignKey, MetaData
from sqlalchemy.dialects.postgresql import UUID
from pgvector.sqlalchemy import Vector
from helpers.db_connection import engine  # async engine
from sqlalchemy.ext.asyncio import AsyncEngine

# Single MetaData for all dynamic tables
metadata = MetaData()

def get_dynamic_vector_table(table_name: str) -> Table:
    """
    Return a SQLAlchemy Table object for dynamic vector storage.
    """
    return Table(
        table_name,
        metadata,
        Column("id", Integer, primary_key=True),
        Column("document_id", UUID(as_uuid=True), nullable=False),
        Column("chunk_id", UUID(as_uuid=True), nullable=False),
        Column("embedding", Vector(768), nullable=False),
        extend_existing=True,
    )

async def create_project_vector_table(project_name: str) -> str:
    """
    Create a dynamic embeddings table for a project if it doesn't exist.
    """
    table_name = f"{project_name}_vectors"
    table = get_dynamic_vector_table(table_name)

    async with engine.begin() as conn:
        await conn.run_sync(metadata.create_all, tables=[table])

    return table_name

async def drop_project_vector_table(project_name: str):
    """
    Drop the embeddings table for a project if it exists.
    """
    table_name = f"embeddings_project_{project_name}"
    table = get_dynamic_vector_table(table_name)

    async with engine.begin() as conn:
        await conn.run_sync(table.drop, checkfirst=True)
