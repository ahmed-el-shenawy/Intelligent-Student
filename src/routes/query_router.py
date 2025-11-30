from fastapi import APIRouter, Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi.encoders import jsonable_encoder

from helpers.deps import get_current_user
from helpers.db_connection import get_db
from helpers.handle_exceptions import handle_exceptions
from models.postgres.tables_schema.tables import User
from routes.schemes.query import QueryRequest
from controllers.QueryController import QueryController

query_controller = QueryController()
query_router = APIRouter(prefix="/query")


@query_router.post("")
@handle_exceptions
async def answer_question(
    request: Request,
    data: QueryRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # Authorization
    # if current_user["role"] != 0 and data.project_name not in current_user["projects"]:
    #     from routes.exceptions import NotPermitted
    #     raise NotPermitted(f"You are not authorized to query project '{data.project_name}'")

    # Get top-k answer
    answer = await query_controller.get_top_k(
        db=db,
        user_id=current_user["id"],
        embed_client=request.app.state.embedding_client,
        gen_client=request.app.state.generation_client,
        project_name=data.project_name,
        query=data.query,
        voice=data.voice,
        k=data.k
    )

    return {"data": answer, "message": f"Answered query for project '{data.project_name}'"}
