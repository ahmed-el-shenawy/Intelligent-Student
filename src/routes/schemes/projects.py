from pydantic import BaseModel, Field, model_validator
from typing import Optional
from uuid import UUID
from datetime import datetime

class ProjectCreateRequest(BaseModel):
    name: str = Field(..., min_length=3, max_length=50)
    description: Optional[str]

    model_config = {"from_attributes": True}

class ProjectListRequest(BaseModel):
    offset: int
    limit:int

    model_config = {"from_attributes": True}

class ProjectDeleteRequest(BaseModel):
    name: str = Field(..., min_length=3, max_length=50)

    model_config = {"from_attributes": True}

class ProjectSearchRequest(BaseModel):
    name: str = Field(..., min_length=3, max_length=50)

    model_config = {"from_attributes": True}

class ProjectUpdateRequest(BaseModel):
    old_name: str = Field(..., min_length=3, max_length=50)
    new_name: Optional[str] = Field(None, min_length=3, max_length=50)
    description: Optional[str] = None

    model_config = {"from_attributes": True}

    @model_validator(mode="after")
    def validate_update_fields(self):
        if not self.new_name and not self.description:
            raise ValueError("At least one of 'new_name' or 'description' must be provided.")
        return self


class ProjectOut(BaseModel):
    id: UUID
    name: str
    description: Optional[str]
    created_at: datetime

    model_config = {"from_attributes": True}
