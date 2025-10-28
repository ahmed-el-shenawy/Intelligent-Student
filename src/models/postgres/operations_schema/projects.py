from pydantic import BaseModel
from typing import Optional
from uuid import UUID
from datetime import datetime

class ProjectInsert(BaseModel):
    name: str
    description: Optional[str]

    model_config = {"from_attributes": True}

class ProjectList(BaseModel):
    offset: int
    limit: int

    model_config = {"from_attributes": True}

class ProjectDelete(BaseModel):
    name: str

    model_config = {"from_attributes": True}

class ProjectSearch(BaseModel):
    name: str

    model_config = {"from_attributes": True}

class ProjectUpdate(BaseModel):
    old_name: str
    new_name: Optional[str] = None 
    description: Optional[str] = None

    model_config = {"from_attributes": True}

class ProjectOut(BaseModel):
    id: UUID
    name: str
    description: Optional[str]
    created_at: datetime

    model_config = {"from_attributes": True}
