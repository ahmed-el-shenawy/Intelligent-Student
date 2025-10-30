from sqlalchemy.ext.asyncio import AsyncSession
from models.postgres.ProjectsModel import ProjectModel
from routes.schemes.projects import ProjectCreateRequest, ProjectDeleteRequest, ProjectListRequest, ProjectSearchRequest, ProjectUpdateRequest
from routes.exceptions import NotPermitted, ProjectNotFound, ProjectExists, DatabaseError
from helpers.logger import get_logger
import shutil
from pathlib import Path

logger = get_logger("ProjectsController")
project_model = ProjectModel()

class ProjectsController:
    ASSETS_DIR = Path("assets")  # Change if needed

    async def create_project(self, db: AsyncSession, data: ProjectCreateRequest, current_user: dict):
        logger.info(f"User {current_user['id']} attempting to create project '{data.name}'")
        if current_user["role"] not in (0, 1):
            logger.warning(f"Unauthorized create attempt by user {current_user['id']}")
            raise NotPermitted()

        project_path = self.ASSETS_DIR / data.name
        if project_path.exists():
            logger.warning(f"Project already exists in filesystem: {data.name}")
            raise ProjectExists(f"Project '{data.name}' already exists in filesystem")
        project_path.mkdir(parents=True, exist_ok=False)

        try:
            project = await project_model.insert_project(db, data)
            logger.info(f"Project '{data.name}' created successfully")
            return {"data": project, "message": "Project created successfully"}
        except Exception as e:
            logger.error(f"Failed to create project '{data.name}': {e}")
            raise DatabaseError(str(e))

    async def list_projects(self, db: AsyncSession, data: ProjectListRequest):
        logger.info("Listing projects")
        try:
            projects = await project_model.list_projects(db, data)
            logger.info("Projects retrieved successfully")
            return {"data": projects, "message": "Projects retrieved successfully"}
        except Exception as e:
            logger.error(f"Failed to list projects: {e}")
            raise DatabaseError(str(e))

    async def search_by_name(self, db: AsyncSession, data: ProjectSearchRequest):
        logger.info(f"Searching for project '{data.name}'")
        project = await project_model.search_by_name(db, data)
        if not project:
            logger.warning(f"Project '{data.name}' not found")
            raise ProjectNotFound(f"Project '{data.name}' not found")
        logger.info(f"Project '{data.name}' found")
        return {"data": project, "message": "Project found"}

    async def update_project(self, db: AsyncSession, data: ProjectUpdateRequest, current_user: dict):
        logger.info(f"User {current_user['id']} attempting to update project '{data.old_name}'")
        if current_user["role"] not in (0, 1):
            logger.warning(f"Unauthorized update attempt by user {current_user['id']}")
            raise NotPermitted()

        if data.old_name != data.new_name:
            old_path = self.ASSETS_DIR / data.old_name
            new_path = self.ASSETS_DIR / data.new_name
            if not old_path.exists():
                logger.warning(f"Project '{data.old_name}' not found in filesystem")
                raise ProjectNotFound(f"Project '{data.old_name}' not found in filesystem")
            old_path.rename(new_path)

        project = await project_model.update_project(db, data)
        if not project:
            logger.warning(f"Project '{data.old_name}' not found in database")
            raise ProjectNotFound(f"Project '{data.old_name}' not found")
        logger.info(f"Project '{data.old_name}' updated successfully")
        return {"data": project, "message": "Project updated successfully"}

    async def delete_project(self, db: AsyncSession, data: ProjectDeleteRequest, current_user: dict):
        logger.info(f"User {current_user['id']} attempting to delete project '{data.name}'")
        if current_user["role"] not in (0, 1):
            logger.warning(f"Unauthorized delete attempt by user {current_user['id']}")
            raise NotPermitted()

        project_path = self.ASSETS_DIR / data.name
        if project_path.exists():
            shutil.rmtree(project_path)
            logger.info(f"Filesystem for project '{data.name}' deleted")

        try:
            deleted = await project_model.del_project(db, data)
            if not deleted:
                logger.warning(f"Project '{data.name}' not found in database")
                raise ProjectNotFound(f"Project '{data.name}' not found")
            logger.info(f"Project '{data.name}' deleted successfully")
            return {"data": deleted, "message": "Project deleted successfully"}
        except Exception as e:
            logger.error(f"Failed to delete project '{data.name}': {e}")
            raise DatabaseError(str(e))
