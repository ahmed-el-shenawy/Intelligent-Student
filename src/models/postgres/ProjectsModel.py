from typing import Dict, Optional
from uuid import UUID
import logging

from sqlalchemy import select, update, delete, func
from sqlalchemy.exc import IntegrityError

from models.postgres.operations_schema.projects import ProjectList, ProjectSearch

from .BaseModel import BaseModel
from models.postgres.operations_schema import ProjectInsert, ProjectUpdate, ProjectDelete, ProjectOut
from models.postgres.tables_schema import Project

logger = logging.getLogger(__name__)


class ProjectModel(BaseModel):
    def __init__(self):
        super().__init__()

    async def insert_project(self, data: ProjectInsert) -> ProjectOut:
        async for session in self.get_session():
            new_project = Project(name=data.name, description=data.description)
            session.add(new_project)
            try:
                await session.commit()
                await session.refresh(new_project)
                return ProjectOut.model_validate(new_project)
                
            except IntegrityError as e:
                await session.rollback()
                logger.error(f"Failed to insert project '{data.name}': {e}")
                raise ValueError(f"Project with name '{data.name}' already exists.")

    async def list_projects(self, data: ProjectList) -> Dict:
        async for session in self.get_session():
            stmt = select(Project, func.count(Project.id).over().label("total_count"))
            stmt = stmt.offset(data.offset).limit(data.limit)
            result = await session.execute(stmt)
            rows = result.all()
            items = [ProjectOut.model_validate(row.Project) for row in rows]
            total_count = rows[0].total_count if rows else 0
            return {"total": total_count, "offset": data.offset, "limit": data.limit, "items": items}

 
    async def del_project(self, data: ProjectDelete) -> Optional[ProjectOut]: 
        async for session in self.get_session():
            stmt = delete(Project).where(Project.name == data.name).returning(Project)
            result = await session.execute(stmt)
            await session.commit()
            deleted_project = result.scalar_one_or_none()
            return ProjectOut.model_validate(deleted_project) if deleted_project else None

    async def search_by_name(self, data: ProjectSearch) -> Optional[ProjectOut]:
        async for session in self.get_session():
            stmt = select(Project).where(Project.name == data.name)
            result = await session.execute(stmt)
            await session.commit()
            project = result.scalar_one_or_none()
            return ProjectOut.model_validate(project) if project else None


    async def update_project(self, data: ProjectUpdate) -> Optional[ProjectOut]:
        async for session in self.get_session():
            update_values = {}
            if data.new_name:
                update_values["name"] = data.new_name
            if data.description:
                update_values["description"] = data.description

            stmt = (
                update(Project)
                .where(Project.name == data.old_name)
                .values(**update_values)
                .returning(Project)
            )
            result = await session.execute(stmt)
            await session.commit()
            updated_project = result.scalar_one_or_none()
            return ProjectOut.model_validate(updated_project) if updated_project else None


