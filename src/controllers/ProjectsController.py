from models.postgres.operations_schema.projects import ProjectDelete, ProjectInsert, ProjectList, ProjectSearch, ProjectUpdate
from .BaseController import BaseController
from routes.schemes.projects import ProjectOut
from models.postgres.ProjectsModel import ProjectModel
import shutil
import logging

logger = logging.getLogger(__name__)
project_model = ProjectModel()

class ProjectsController(BaseController):

    def __init__(self):
        super().__init__()

    async def create_project(self, name: str, description: str):
        try:
            #Create a dir with project name inside assests/
            project_path = self.ASSETS_DIR / name
            if project_path.exists():
                raise ValueError
            project_path.mkdir(parents=True)

            #Insert into db
            project_data = ProjectInsert(name= name, description= description)
            created: ProjectOut = await project_model.insert_project(data=project_data)
            return created
        except ValueError as e:
            raise ValueError(f"Project with name '{project_data.name}' already exists.")
        
    async def search_by_name(self, name: str):
        project_search = ProjectSearch(name = name)
        project = await project_model.search_by_name(project_search)
        return project
    
    async def list_projects(self, offset: int, limit: int):
        list_date = ProjectList(offset= offset, limit= limit)
        projects = await project_model.list_projects( data = list_date)
        return projects
    
    async def update_project(self, old_name: str, new_name: str, description: str = None):
        project_path = self.ASSETS_DIR / old_name
        if not project_path.exists():
                raise ValueError(f"project with name ({old_name}) does not exist")
        if new_name:
            new_path = self.ASSETS_DIR / new_name
            project_path.rename(new_path)
        update_data = ProjectUpdate(old_name = old_name, new_name = new_name, description = description)
        project = await project_model.update_project(update_data)
        return project

    async def delete_project(self, name: str):
        try:
            #Delete from assets dir (if exists)
            project_path = self.ASSETS_DIR / name
            if project_path.exists():
                shutil.rmtree(project_path)
            else:
                logger.warning(f"Assets directory for project {name} not found")

            #Delete from db
            data = ProjectDelete(name = name)
            deleted: ProjectOut | None = await project_model.del_project(data)
            return deleted

        except Exception as e:
            logger.error(f"Failed to delete project {name}: {e}")
            raise ValueError(f"Could not delete project {name}: {e}")

