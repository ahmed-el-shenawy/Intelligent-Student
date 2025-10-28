# models/chunks.py
import uuid
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import relationship
from .base import Base

class Chunk(Base):
    __tablename__ = "chunks"

    id = sa.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    document_id = sa.Column(UUID(as_uuid=True), sa.ForeignKey("documents.id", ondelete="CASCADE"))
    chunk_text = sa.Column(sa.Text, nullable=False)
    chunk_metadata = sa.Column(JSONB, nullable=True)
    chunk_index = sa.Column(sa.Integer, nullable=False)

    document = relationship("Document", back_populates="chunks")
