from typing import Dict, List
import uuid
import logging
from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from .BaseModel import BaseModel
from models.postgres.tables_schema.tables import UserHistory
from routes.exceptions import DatabaseError

logger = logging.getLogger("UserHistoryModel")

class UserHistoryModel(BaseModel):
    """
    Provides access to user history per project.
    """

    def __init__(self):
        super().__init__()

    # ------------------------- Get History -------------------------
    async def get_history(self, db: AsyncSession, user_id: uuid.UUID, project_id: uuid.UUID) -> List[Dict]:
        """
        Retrieve the chat history for a given user and project.
        """
        try:
            logger.info(f"Attempting to fetch history [user={user_id}, project={project_id}]")
            stmt = select(UserHistory.history).where(
                UserHistory.user_id == user_id,
                UserHistory.project_id == project_id
            )
            result = await db.execute(stmt)
            history = result.scalar_one_or_none()
            logger.info(f"Successfully fetched history [user={user_id}, project={project_id}]")
            return history or []

        except Exception as e:
            logger.error(f"Failed to fetch history [user={user_id}, project={project_id}] - {str(e)}")
            raise DatabaseError(f"Failed to fetch history: {str(e)}") from e

    # ------------------------- Update / Upsert History -------------------------
    async def update_history(self, db: AsyncSession, user_id: uuid.UUID, project_id: uuid.UUID, history: List[Dict]):
        """
        Upsert the chat history for a given user and project.
        """
        try:
            logger.info(f"Attempting to update history [user={user_id}, project={project_id}]")
            stmt = insert(UserHistory).values(
                user_id=user_id,
                project_id=project_id,
                history=history
            ).on_conflict_do_update(
                index_elements=['user_id', 'project_id'],
                set_={'history': history}
            ).returning(UserHistory)

            result = await db.execute(stmt)
            await db.commit()
            updated_record = result.scalar_one_or_none()
            logger.info(f"Successfully updated history [user={user_id}, project={project_id}]")
            return updated_record

        except Exception as e:
            await db.rollback()
            logger.error(f"Failed to update history [user={user_id}, project={project_id}] - {str(e)}")
            raise DatabaseError(f"Failed to update history: {str(e)}") from e
