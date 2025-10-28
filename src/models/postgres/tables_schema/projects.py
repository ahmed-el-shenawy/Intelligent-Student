import uuid
import sqlalchemy as sa
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID
from .base import Base

class Project(Base):
    __tablename__ = "projects"

    id = sa.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = sa.Column(sa.String(50), nullable=False, unique=True)
    description = sa.Column(sa.Text, nullable=True)
    created_at = sa.Column(sa.DateTime(timezone=True), server_default=func.now())

    documents = relationship("Document", back_populates="project", cascade="all, delete-orphan")


