from typing import Dict, List
import uuid
from sqlalchemy import select
from .BaseModel import BaseModel
from models.postgres.tables_schema.tables import UserHistory
from sqlalchemy.dialects.postgresql import insert

class UserHistoryModel(BaseModel):
    """
    Provides access to user history per project.
    """

    def __init__(self):
        super().__init__()

    async def get_history(self, user_id: uuid.UUID, project_id: uuid.UUID) -> List[Dict]:
        """
        Retrieve the chat history for a given user and project.

        Args:
            user_id (uuid.UUID): The user ID.
            project_id (uuid.UUID): The project ID.

        Returns:
            list: The history list if found, otherwise an empty list.
        """
        async for session in self.get_session():
            result = await session.execute(
                select(UserHistory.history).where(
                    UserHistory.user_id == user_id,
                    UserHistory.project_id == project_id
                )
            )
            history = result.scalar_one_or_none()
            return history or []

    async def update_history(self, user_id: uuid.UUID, project_id: uuid.UUID, history: List[Dict]):
        """
        Upsert the chat history for a given user and project.
        """
        async for session in self.get_session():
            stmt = insert(UserHistory).values(
                user_id=user_id,
                project_id=project_id,
                history=history
            ).on_conflict_do_update(
                index_elements=['user_id', 'project_id'],
                set_={'history': history}
            ).returning(UserHistory)

            result = await session.execute(stmt)
            await session.commit()
            updated_record = result.scalar_one_or_none()
            return updated_record
