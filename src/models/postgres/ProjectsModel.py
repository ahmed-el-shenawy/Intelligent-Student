from sqlalchemy import select, update, delete, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import IntegrityError
from models.postgres.tables_schema.tables import Project
from models.postgres.operations_schema.projects import ProjectInsert, ProjectUpdate, ProjectDelete, ProjectList, ProjectSearch, ProjectOut
from routes.exceptions import DatabaseError, ProjectNotFound
from helpers.logger import get_logger

logger = get_logger("ProjectModel")

class ProjectModel:

    async def insert_project(self, db: AsyncSession, data: ProjectInsert) -> ProjectOut:
        logger.info(f"Inserting project '{data.name}'")
        new_project = Project(name=data.name, description=data.description)
        db.add(new_project)
        try:
            await db.commit()
            await db.refresh(new_project)
            logger.info(f"Project '{data.name}' inserted successfully")
            return ProjectOut.model_validate(new_project)
        except IntegrityError as e:
            await db.rollback()
            logger.warning(f"Project insert failed, already exists: {data.name}")
            raise DatabaseError(f"Project '{data.name}' already exists")
        except Exception as e:
            await db.rollback()
            logger.exception(f"Unexpected error inserting project '{data.name}': {e}")
            raise DatabaseError(str(e))

    async def list_projects(self, db: AsyncSession, data: ProjectList) -> dict:
        logger.info(f"Listing projects with offset={data.offset}, limit={data.limit}")
        try:
            stmt = select(Project, func.count(Project.id).over().label("total_count")).offset(data.offset).limit(data.limit)
            result = await db.execute(stmt)
            rows = result.all()
            items = [ProjectOut.model_validate(row.Project) for row in rows]
            total_count = rows[0].total_count if rows else 0
            logger.info(f"Retrieved {len(items)} projects")
            return {"total": total_count, "offset": data.offset, "limit": data.limit, "items": items}
        except Exception as e:
            logger.exception(f"Failed to list projects: {e}")
            raise DatabaseError(str(e))

    async def search_by_name(self, db: AsyncSession, data: ProjectSearch) -> ProjectOut | None:
        logger.info(f"Searching project by name '{data.name}'")
        try:
            stmt = select(Project).where(Project.name == data.name)
            result = await db.execute(stmt)
            project = result.scalar_one_or_none()
            if project:
                logger.info(f"Project '{data.name}' found")
                return ProjectOut.model_validate(project)
            else:
                logger.warning(f"Project '{data.name}' not found")
                return None
        except Exception as e:
            logger.exception(f"Failed to search project '{data.name}': {e}")
            raise DatabaseError(str(e))

    async def update_project(self, db: AsyncSession, data: ProjectUpdate) -> ProjectOut | None:
        logger.info(f"Updating project '{data.old_name}'")
        update_values = {}
        if data.new_name:
            update_values["name"] = data.new_name
        if data.description:
            update_values["description"] = data.description

        try:
            stmt = update(Project).where(Project.name == data.old_name).values(**update_values).returning(Project)
            result = await db.execute(stmt)
            await db.commit()
            updated_project = result.scalar_one_or_none()
            if updated_project:
                logger.info(f"Project '{data.old_name}' updated successfully")
                return ProjectOut.model_validate(updated_project)
            else:
                logger.warning(f"Project '{data.old_name}' not found for update")
                return None
        except Exception as e:
            await db.rollback()
            logger.exception(f"Failed to update project '{data.old_name}': {e}")
            raise DatabaseError(str(e))

    async def del_project(self, db: AsyncSession, data: ProjectDelete) -> ProjectOut | None:
        logger.info(f"Deleting project '{data.name}'")
        try:
            stmt = delete(Project).where(Project.name == data.name).returning(Project)
            result = await db.execute(stmt)
            await db.commit()
            deleted_project = result.scalar_one_or_none()
            if deleted_project:
                logger.info(f"Project '{data.name}' deleted successfully")
                return ProjectOut.model_validate(deleted_project)
            else:
                logger.warning(f"Project '{data.name}' not found for deletion")
                raise ProjectNotFound(f"Project '{data.name}' not found")   
        except Exception as e:
            await db.rollback()
            logger.exception(f"Failed to delete project '{data.name}': {e}")
            raise 
