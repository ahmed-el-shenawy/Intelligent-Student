# models/tables_schema.py
import uuid
import sqlalchemy as sa
from sqlalchemy import Index
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID,JSONB
from .base import Base

class Document(Base):
    __tablename__ = "documents"

    id = sa.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    project_id = sa.Column(UUID(as_uuid=True), sa.ForeignKey("projects.id", ondelete="CASCADE"), nullable=False)
    filename = sa.Column(sa.String(255), nullable=False)
    doc_metadata = sa.Column(JSONB, nullable=True)
    created_at = sa.Column(sa.DateTime(timezone=True), server_default=func.now(), nullable=False)
    
    project = relationship("Project", back_populates="documents")
    chunks = relationship("Chunk", back_populates="document", cascade="all, delete-orphan")
 
    __table_args__ = (
    Index('idx_documents_project_file', 'project_id', 'filename'),
    sa.UniqueConstraint('project_id', 'filename', name='uq_project_file')
    )