import logging
from datetime import datetime, timedelta, timezone
from sqlalchemy import select, delete, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import SQLAlchemyError
from models.postgres.tables_schema.tables import User, RefreshToken, ProjectUser
from helpers.security import hash_password
from routes.exceptions import DatabaseError
from helpers.logger import get_logger

logger = get_logger("AuthModel")


class AuthModel:

    async def get_user_by_username(self, db: AsyncSession, username: str) -> User | None:
        logger.info(f"Fetching user by username: {username}")
        try:
            result = await db.execute(select(User).where(User.username == username))
            user = result.scalar_one_or_none()
            if user:
                logger.info(f"User found: {username}")
            else:
                logger.warning(f"User not found: {username}")
            return user
        except SQLAlchemyError as e:
            logger.exception(f"DB error fetching user {username}: {e}")
            raise DatabaseError(str(e))

    async def create_user(self, db: AsyncSession, username: str, password: str) -> User:
        logger.info(f"Creating user: {username}")
        new_user = User(username=username, hashed_password=hash_password(password))
        db.add(new_user)
        try:
            await db.commit()
            await db.refresh(new_user)
            logger.info(f"User created successfully: {username}")
            return new_user
        except SQLAlchemyError as e:
            await db.rollback()
            logger.exception(f"DB error creating user {username}: {e}")
            raise DatabaseError(str(e))

    async def remove_token(self, db: AsyncSession, user_id: str):
        logger.info(f"Removing tokens for user {user_id}")
        try:
            await db.execute(delete(RefreshToken).where(RefreshToken.user_id == user_id))
            await db.commit()
            logger.info(f"Tokens removed for user {user_id}")
        except SQLAlchemyError as e:
            await db.rollback()
            logger.exception(f"DB error removing token for user {user_id}: {e}")
            raise DatabaseError(str(e))

    async def store_refresh_token(self, db: AsyncSession, user_id: str, token: str):
        logger.info(f"Storing refresh token for user {user_id}")
        db.add(
            RefreshToken(
                user_id=user_id,
                hashed_token=token,
                expires_at=datetime.now(timezone.utc) + timedelta(days=7)
            )
        )
        try:
            await db.commit()
            logger.info(f"Refresh token stored for user {user_id}")
        except SQLAlchemyError as e:
            await db.rollback()
            logger.exception(f"DB error storing refresh token for user {user_id}: {e}")
            raise DatabaseError(str(e))

    async def get_refresh_token(self, db: AsyncSession, token: str) -> RefreshToken | None:
        logger.info("Fetching refresh token")
        try:
            result = await db.execute(select(RefreshToken).where(RefreshToken.hashed_token == token))
            token_entry = result.scalar_one_or_none()
            if token_entry:
                logger.info("Refresh token found")
            else:
                logger.warning("Refresh token not found")
            return token_entry
        except SQLAlchemyError as e:
            logger.exception(f"DB error fetching refresh token: {e}")
            raise DatabaseError(str(e))

    async def create_project_user(self, db: AsyncSession, project_id: str, user_id: str):
        logger.info(f"Creating project-user relation: user={user_id}, project={project_id}")
        relation = ProjectUser(project_id=project_id, user_id=user_id)
        db.add(relation)
        try:
            await db.commit()
            await db.refresh(relation)
            logger.info(f"Project-user relation created successfully: user={user_id}, project={project_id}")
            return relation
        except SQLAlchemyError as e:
            await db.rollback()
            logger.exception(f"DB error creating project-user relation: user={user_id}, project={project_id}: {e}")
            raise DatabaseError(str(e))

    async def deauthorize_user(self, db: AsyncSession, user_id: str, project_id: str):
        logger.info(f"Deauthorizing user {user_id} from project {project_id}")
        try:
            await db.execute(
                delete(ProjectUser).where(ProjectUser.user_id == user_id).where(ProjectUser.project_id == project_id)
            )
            await db.commit()
            logger.info(f"User {user_id} deauthorized from project {project_id}")
        except SQLAlchemyError as e:
            await db.rollback()
            logger.exception(f"DB error deauthorizing user {user_id} from project {project_id}: {e}")
            raise DatabaseError(str(e))

    async def update_user_role(self, db: AsyncSession, user_id: str, new_role: int):
        logger.info(f"Updating role for user {user_id} to {new_role}")
        try:
            await db.execute(update(User).where(User.id == user_id).values(role=new_role))
            await db.commit()
            logger.info(f"User {user_id} role updated successfully to {new_role}")
        except SQLAlchemyError as e:
            await db.rollback()
            logger.exception(f"DB error updating role for user {user_id}: {e}")
            raise DatabaseError(str(e))
