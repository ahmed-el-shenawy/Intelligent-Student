# routes/projects.py
from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse
from .schemes.projects import (
    ProjectCreateRequest,
    ProjectDeleteRequest,
    ProjectListRequest,
    ProjectSearchRequest,
    ProjectUpdateRequest,
    ProjectOut
    )
from typing import Dict
from fastapi.encoders import jsonable_encoder
from controllers import ProjectsController

project_controller = ProjectsController()
projects_router = APIRouter(
    prefix="/projects"
)

@projects_router.post("")
async def create_project(data: ProjectCreateRequest):
    try:
        created: ProjectOut = await project_controller.create_project(name = data.name, description = data.description)
        return JSONResponse(
            content={"status": "success", "data": jsonable_encoder(created)},
            status_code=201
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal Server Error: {e}")

@projects_router.get("")
async def get_all_projects(data: ProjectListRequest):
    try:
        projects: Dict = await project_controller.list_projects(offset= data.offset, limit= data.limit)
        return JSONResponse(
            content={"status": "success", "data": jsonable_encoder(projects)},
            status_code=200
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    
@projects_router.get("/search")
async def search_by_name(data: ProjectSearchRequest ):
    try:
        project: ProjectOut | None = await project_controller.search_by_name(name = data.name)
        if not project:
            raise HTTPException(status_code=404, detail="Project not found")
        return JSONResponse(
            content={"status": "found", "project": jsonable_encoder(project)},
            status_code=200
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@projects_router.delete("")
async def delete_project(data: ProjectDeleteRequest ):
    try:
        deleted: ProjectOut | None = await project_controller.delete_project(data.name)
        if not deleted:
            raise HTTPException(status_code=404, detail="Project not found")
        return JSONResponse(
            content={"status": "success", "message": "Project deleted", "project": jsonable_encoder(deleted)},
            status_code=200
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    
@projects_router.put("")
async def update(data: ProjectUpdateRequest ):
    try:
        project: ProjectOut | None = await project_controller.update_project(old_name = data.old_name, new_name= data.new_name, description = data.description)
        if not project:
            raise HTTPException(status_code=404, detail="Project not found")
        return JSONResponse(
            content={"status": "success", "message": "Project found", "project": jsonable_encoder(project)},
            status_code=200
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

