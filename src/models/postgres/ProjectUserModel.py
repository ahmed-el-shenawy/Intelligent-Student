from uuid import UUID
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from models.postgres.tables_schema.tables import ProjectUser

from .BaseModel import BaseModel

class ProjectUserModel(BaseModel):
    # ... existing methods ...

    async def user_has_access(self, db: AsyncSession, user_id: UUID, project_id: UUID) -> bool:
        result = await db.execute(
            select(ProjectUser).where(
                ProjectUser.project_id == project_id,
                ProjectUser.user_id == user_id
            )
        )
        return result.scalar_one_or_none() is not None
