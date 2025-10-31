import logging
from uuid import UUID
from typing import List

from models.postgres.VectorsModel import VectorModel
from models.postgres.ChunksModel import ChunksModel
from models.postgres.ProjectsModel import ProjectModel
from models.postgres.UserHistoryModel import UserHistoryModel
from models.postgres.ProjectUserModel import ProjectUserModel
from models.postgres.operations_schema.projects import ProjectSearch
from routes.exceptions import NotPermitted
from .BaseController import BaseController
from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger("QueryController")

chunk_model = ChunksModel()
project_model = ProjectModel()
vec_model = VectorModel()
history_model = UserHistoryModel()
project_user_model = ProjectUserModel()


class QueryController(BaseController):
    def __init__(self):
        super().__init__()

    async def get_top_k(
        self,
        db: AsyncSession,
        user_id: UUID,
        embed_client,
        gen_client,
        project_name: str,
        query: str,
        k: int,
    ):
        try:
            logger.info(f"User {user_id} querying project '{project_name}'")

            # 1️⃣ Find project
            project_search = ProjectSearch(name=project_name)
            project = await project_model.search_by_name(db=db, data=project_search)
            if not project:
                raise ValueError(f"Project '{project_name}' does not exist")
            logger.info(f"Project '{project_name}' found (ID={project.id})")

            if not await project_user_model.user_has_access(db, user_id=user_id, project_id=project.id):
                logger.warning(f"Unauthorized access: User {user_id} tried to query project '{project_name}'")
                raise NotPermitted(f"User {user_id} is not authorized to access project '{project_name}'")


            # 2️⃣ Embed query and retrieve top-k context
            embedding = embed_client.embed([query])[0]
            results = await vec_model.top_k_similar_vector_text(
                db=db, project_id=project.id, query_vector=embedding, top_k=k
            )
            context_texts = [c.text for c in results]
            logger.info(f"Retrieved {len(context_texts)} context chunks for project '{project_name}'")

            # 3️⃣ Fetch user history
            history = await history_model.get_history(db=db, user_id=user_id, project_id=project.id)

            # 4️⃣ Construct messages for LLM
            messages = [{"role": "system", "content": "You are a helpful assistant. Answer the user's questions based on context. If the context does not provide enough info, respond with 'I don't know.'"}]
            messages.extend(history)
            if context_texts:
                context_prompt = "\n---\n".join(context_texts)
                messages.append({"role": "system", "content": f"Context:\n{context_prompt}"})
            messages.append({"role": "user", "content": query})

            # 5️⃣ Get LLM response
            answer = gen_client.response(messages)
            logger.info(f"Generated answer for user {user_id} in project '{project_name}'")

            # 6️⃣ Update history
            history.append({"role": "user", "content": query})
            history.append({"role": "assistant", "content": answer})
            history = history[-12:]  # keep last 12 messages

            await history_model.update_history(db=db, user_id=user_id, project_id=project.id, history=history)
            logger.info(f"Updated user {user_id} history for project '{project_name}'")

            return answer

        except Exception as e:
            logger.error(f"Failed to get top-k answer for user {user_id}, project '{project_name}': {e}")
            raise
