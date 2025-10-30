from functools import wraps
from fastapi import APIRouter, Depends
from fastapi.encoders import jsonable_encoder
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession
from helpers.db_connection import get_db
from controllers.ProjectsController import ProjectsController
from helpers.deps import get_current_user
from helpers.handle_exceptions import handle_exceptions
from routes.schemes.projects import (
    ProjectCreateRequest,
    ProjectDeleteRequest,
    ProjectListRequest,
    ProjectSearchRequest,
    ProjectUpdateRequest
)
from helpers.logger import get_logger
from routes.exceptions import DatabaseError, ProjectNotFound, ProjectExists

logger = get_logger("projects_router")

projects_router = APIRouter(prefix="/projects", tags=["Projects"])
project_controller = ProjectsController()

 

# --- ROUTES ---
@projects_router.post("")
@handle_exceptions
async def create_project(data: ProjectCreateRequest, db: AsyncSession = Depends(get_db), current_user = Depends(get_current_user)):
    return await project_controller.create_project(db, data, current_user)

@projects_router.get("")
@handle_exceptions
async def get_all_projects(data: ProjectListRequest, db: AsyncSession = Depends(get_db), current_user = Depends(get_current_user)):
    return await project_controller.list_projects(db, data)

@projects_router.get("/search")
@handle_exceptions
async def search_by_name(data: ProjectSearchRequest, db: AsyncSession = Depends(get_db), current_user = Depends(get_current_user)):
    return await project_controller.search_by_name(db, data)

@projects_router.put("")
@handle_exceptions
async def update_project(data: ProjectUpdateRequest, db: AsyncSession = Depends(get_db), current_user = Depends(get_current_user)):
    return await project_controller.update_project(db, data, current_user)

@projects_router.delete("")
@handle_exceptions
async def delete_project(data: ProjectDeleteRequest, db: AsyncSession = Depends(get_db), current_user = Depends(get_current_user)):
    return await project_controller.delete_project(db, data, current_user)
