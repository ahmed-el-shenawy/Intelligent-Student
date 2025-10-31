from datetime import datetime, timezone
from sqlalchemy import select
from helpers.security import verify_password, create_access_token, create_refresh_token, decode_token
from models.postgres.AuthModel import AuthModel
from models.postgres.ProjectsModel import ProjectModel
from models.postgres.operations_schema.projects import ProjectSearch
from models.postgres.tables_schema.tables import ProjectUser
from routes.exceptions import UserAlreadyExists, UserNotFound, InvalidCredentials, NotPermitted, TokenError
from helpers.logger import get_logger

logger = get_logger("auth_controller")

auth_model = AuthModel()
project_model = ProjectModel()

class AuthController:

    async def signup(self, db, user):
        logger.info(f"Signup attempt for username={user.username}")
        existing_user = await auth_model.get_user_by_username(db, user.username)
        if existing_user:
            logger.warning(f"Signup failed: username exists: {user.username}")
            raise UserAlreadyExists()
        
        _ = await auth_model.create_user(db, user.username, user.password)
        logger.info(f"User created successfully: {user.username}")
        return {"data": None, "message": "User created successfully"}

    async def login(self, db, user):
        logger.info(f"Login attempt for username={user.username}")
        db_user = await auth_model.get_user_by_username(db, user.username)
        if not db_user or not verify_password(user.password, db_user.hashed_password):
            logger.warning(f"Invalid login for username={user.username}")
            raise InvalidCredentials()

        await auth_model.remove_token(db, db_user.id)

        access_token = create_access_token({"sub": str(db_user.id)})
        refresh_token = create_refresh_token(db_user.id)
        await auth_model.store_refresh_token(db, db_user.id, refresh_token)

        logger.info(f"User logged in successfully: {user.username}")
        return {
            "data": {"access_token": access_token, "refresh_token": refresh_token, "token_type": "bearer"},
            "message": "Login successful"
        }

    async def refresh(self, db, payload):
        logger.info("Refresh token attempt")
        token_data = decode_token(payload.refresh_token)
        if not token_data or token_data.get("type") != "refresh":
            logger.warning("Invalid refresh token")
            raise TokenError("Invalid refresh token")

        token_entry = await auth_model.get_refresh_token(db, payload.refresh_token)
        if not token_entry or token_entry.expires_at < datetime.now(timezone.utc):
            logger.warning("Expired or revoked refresh token")
            raise TokenError("Expired or revoked refresh token")

        new_access = create_access_token({"sub": token_data.get("sub")})
        logger.info("Access token refreshed successfully")
        return {"data": {"access_token": new_access, "token_type": "bearer"}, "message": "Token refreshed successfully"}

    async def logout(self, db, current_user):
        logger.info(f"Logout attempt user_id={current_user['id']}")
        await auth_model.remove_token(db, current_user["id"])
        logger.info(f"User {current_user['id']} logged out successfully")
        return {"data": None, "message": "Logged out successfully"}

    async def authorize(self, db, current_user, data):
        logger.info(f"Authorize attempt user_id={current_user['id']} project={data.project_name}")
        if current_user["role"] != 0:
            logger.warning("Unauthorized authorize attempt")
            raise NotPermitted()

        project = await project_model.search_by_name(db, ProjectSearch(name=data.project_name))
        target_user = await auth_model.get_user_by_username(db, data.username)
        if not target_user:
            logger.warning(f"Target user not found: {data.username}")
            raise UserNotFound()

        existing_relation = await db.execute(
            select(ProjectUser).where(
                ProjectUser.user_id == target_user.id,
                ProjectUser.project_id == project.id
            )
        )
        if existing_relation.scalar_one_or_none():
            logger.warning(f"User {data.username} already authorized for project {data.project_name}")
            raise TokenError("User already authorized for this project")

        await auth_model.create_project_user(db, project.id, target_user.id)
        logger.info(f"User {data.username} authorized for project {data.project_name}")
        return {"data": None, "message": "Project authorized successfully"}

    async def deauthorize(self, db, current_user, data):
        logger.info(f"Deauthorize attempt user_id={current_user['id']} target_user={data.username}")
        if current_user["role"] != 0:
            logger.warning("Unauthorized deauthorize attempt")
            raise NotPermitted()

        project = await project_model.search_by_name(ProjectSearch(name=data.project_name))
        target_user = await auth_model.get_user_by_username(db, data.username)
        if not target_user:
            logger.warning(f"Target user not found: {data.username}")
            raise UserNotFound()

        await auth_model.deauthorize_user(db, target_user.id, project.id)
        logger.info(f"User {data.username} deauthorized from project {data.project_name}")
        return {"data": None, "message": f"User {data.username} deauthorized from project {data.project_name}"}

    async def update_privilege(self, db, current_user, data):
        logger.info(f"Update privilege attempt user_id={current_user['id']} target_user={data.username}")
        if current_user["role"] != 0:
            logger.warning("Unauthorized update_privilege attempt")
            raise NotPermitted()

        target_user = await auth_model.get_user_by_username(db, data.username)
        if not target_user:
            logger.warning(f"Target user not found: {data.username}")
            raise UserNotFound()

        await auth_model.update_user_role(db, target_user.id, data.new_role)
        logger.info(f"User {data.username} role updated to {data.new_role}")
        return {"data": None, "message": f"User {data.username} role updated to {data.new_role}"}
