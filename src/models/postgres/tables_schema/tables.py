# models/schema.py
import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy import (
    MetaData, Column, String, Boolean, DateTime, Text, Integer,
    ForeignKey, Index, UniqueConstraint, func, Table, text
)
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import declarative_base, relationship, Mapped, mapped_column
from pgvector.sqlalchemy import Vector

# ============================================================
# NAMING CONVENTION (ensures consistent constraint/index names)
# ============================================================
metadata = MetaData(
    naming_convention={
        "ix": "ix_%(table_name)s_%(column_0_label)s",
        "uq": "uq_%(table_name)s_%(column_0_name)s",
        "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
        "pk": "pk_%(table_name)s"
    }
)

Base = declarative_base(metadata=metadata)


# ============================================================
# USERS TABLE
# ============================================================
class User(Base):
    """
    Stores basic user information and authentication details.
    """
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    username: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    hashed_password: Mapped[str] = mapped_column(String, nullable=False)
    role: Mapped[int] = mapped_column(Integer, nullable=False, server_default="1")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    projects = relationship("ProjectUser", back_populates="user", cascade="all, delete-orphan")
    refresh_tokens = relationship("RefreshToken", back_populates="user", cascade="all, delete-orphan")


# ============================================================
# PROJECTS TABLE
# ============================================================
class Project(Base):
    """
    Represents a user-owned or shared project that groups documents.
    """
    __tablename__ = "projects"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    documents = relationship("Document", back_populates="project", cascade="all, delete-orphan")
    users = relationship("ProjectUser", back_populates="project", cascade="all, delete-orphan")


# ============================================================
# PROJECT-USER ASSOCIATION TABLE
# ============================================================
class ProjectUser(Base):
    """
    Associates users with projects (many-to-many).
    """
    __tablename__ = "project_users"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    project_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("projects.id", ondelete="CASCADE"), nullable=False
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )

    # Relationships
    project = relationship("Project", back_populates="users")
    user = relationship("User", back_populates="projects")

    __table_args__ = (
        UniqueConstraint("project_id", "user_id", name="uq_project_user"),
    )


# ============================================================
# DOCUMENTS TABLE
# ============================================================
class Document(Base):
    """
    Stores uploaded documents for each project.
    """
    __tablename__ = "documents"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    project_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("projects.id", ondelete="CASCADE"), nullable=False
    )
    filename: Mapped[str] = mapped_column(String(255), nullable=False)
    metadata_json: Mapped[Optional[dict]] = mapped_column(JSONB)
    is_processed: Mapped[bool] = mapped_column(Boolean, server_default="FALSE", nullable=False)
    is_flushed: Mapped[bool] = mapped_column(Boolean, server_default="FALSE", nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    project = relationship("Project", back_populates="documents")
    chunks = relationship("Chunk", back_populates="document", cascade="all, delete-orphan")
    vectors = relationship("VectorEmbedding", back_populates="document", cascade="all, delete-orphan")

    __table_args__ = (
        UniqueConstraint("project_id", "filename", name="uq_project_filename"),
        Index("idx_documents_project_filename", "project_id", "filename"),
        Index("idx_documents_is_processed", "is_processed"),
    )


# ============================================================
# CHUNKS TABLE
# ============================================================
class Chunk(Base):
    """
    Represents a chunk of a document, used for embeddings and retrieval.
    """
    __tablename__ = "chunks"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    document_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("documents.id", ondelete="CASCADE"), nullable=False
    )
    text: Mapped[str] = mapped_column(Text, nullable=False)
    metadata_json: Mapped[Optional[dict]] = mapped_column(JSONB)

    # Relationships
    document = relationship("Document", back_populates="chunks")
    vectors = relationship("VectorEmbedding", back_populates="chunk", cascade="all, delete-orphan")


# ============================================================
# USER HISTORY TABLE
# ============================================================
class UserHistory(Base):
    """
    Stores history per user per project.
    """
    __tablename__ = "user_history"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    project_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("projects.id", ondelete="CASCADE"), nullable=False
    )
    history: Mapped[list] = mapped_column(JSONB, nullable=False, server_default=text("'[]'::jsonb"))
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False
    )

    __table_args__ = (
        UniqueConstraint("user_id", "project_id", name="uq_user_project_history"),
        Index("ix_user_history_user_project", "user_id", "project_id"),
    )


# ============================================================
# REFRESH TOKENS TABLE
# ============================================================
class RefreshToken(Base):
    """
    Stores refresh tokens for session management and authentication.
    """
    __tablename__ = "refresh_tokens"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    hashed_token: Mapped[str] = mapped_column(String, unique=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    # Relationship
    user = relationship("User", back_populates="refresh_tokens")


# ============================================================
# VECTORS TABLE (single table for all projects)
# ============================================================
class VectorEmbedding(Base):
    """
    Stores vector embeddings for all projects in a single table.
    """
    __tablename__ = "vector_embeddings"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    project_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("projects.id", ondelete="CASCADE"), nullable=False
    )
    document_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("documents.id", ondelete="CASCADE"), nullable=False
    )
    chunk_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True),ForeignKey("chunks.id", ondelete="CASCADE"),  nullable=False)
    embedding: Mapped[list] = mapped_column(Vector(768), nullable=False)
    
    __table_args__ = (
            Index(
        "idx_vectors_embedding","embedding",
        postgresql_using="ivfflat",
        postgresql_with={"lists": "100"},
        postgresql_ops={"embedding": "vector_cosine_ops"}),
    UniqueConstraint("project_id", "document_id", "chunk_id", name="uq_project_document_chunk"),

    )

    # Relationships
    project = relationship("Project")
    document = relationship("Document", back_populates="vectors")
    chunk = relationship("Chunk", back_populates="vectors")
