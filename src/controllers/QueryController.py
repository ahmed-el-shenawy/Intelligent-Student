from uuid import UUID
from models.postgres.operations_schema.projects import ProjectSearch
from .BaseController import BaseController
from models.postgres.VectorsModel import VectorModel
from models.postgres.ChunksModel import ChunksModel
from models.postgres.ProjectsModel import ProjectModel
from models.postgres.UserHistoryModel import UserHistoryModel

chunk_model = ChunksModel()
project_model = ProjectModel()
vec_model = VectorModel()
history_model = UserHistoryModel()

class QueryController(BaseController):
    def __init__(self):
        pass

    async def get_top_k(self, user_id: UUID, embed_client, gen_client, project_name, query, k):
        # 1️⃣ Find project
        project_search = ProjectSearch(name=project_name)
        project = await project_model.search_by_name(data=project_search)
        if not project:
            raise ValueError(f"Project '{project_name}' does not exist")

        # 2️⃣ Embed query and retrieve top-k context
        embedding = embed_client.embed([query])[0]
        results = await vec_model.top_k_similar_vector_text(
            project_id=project.id, query_vector=embedding, top_k=k
        )
        context_texts = [c.text for c in results]

        # 3️⃣ Fetch user history
        history = await history_model.get_history(user_id=user_id, project_id=project.id)

        # 4️⃣ Construct messages for chat-based LLM
        # Start with previous history, then current system/context instructions, then user question
        messages = []

        # Include system instruction (optional)
        system_prompt = (
            "You are a helpful assistant. Answer the user's questions based on context. "
            "If the context does not provide enough info, respond with 'I don't know.'"
        )
        messages.append({"role": "system", "content": system_prompt})

        # Include previous chat history
        messages.extend(history)

        # Include current context as assistant "system message"
        if context_texts:
            context_prompt = "\n---\n".join(context_texts)
            messages.append({"role": "system", "content": f"Context:\n{context_prompt}"})

        # Include current user query
        messages.append({"role": "user", "content": query})

        # 5️⃣ Get LLM response
        answer = gen_client.response(messages)

        # 6️⃣ Append current interaction to history
        history.append({"role": "user", "content": query})
        history.append({"role": "assistant", "content": answer})

        # Keep history length under 12 messages
        history = history[-12:]

        # 7️⃣ Update history in DB
        await history_model.update_history(user_id=user_id, project_id=project.id, history=history)

        return answer
