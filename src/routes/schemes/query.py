from pydantic import BaseModel, Field
from typing import Optional

class QueryRequest(BaseModel):
    project_name: str
    query: str
    k: Optional[int] = 5

    model_config = {"from_attributes": True}