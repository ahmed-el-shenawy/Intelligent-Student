# routes/query.py
from fastapi import APIRouter, Depends, HTTPException, Request
from helpers.deps import get_current_user
from models.postgres.VectorsModel import VectorModel
from controllers import QueryController
from fastapi.responses import JSONResponse
from fastapi.encoders import jsonable_encoder

from models.postgres.tables_schema.tables import User
from routes.schemes.query import QueryRequest

query_controller = QueryController()
vec_mode = VectorModel()

query_router = APIRouter(
    prefix="/query"
)

@query_router.post("")
async def answer_question(request: Request ,data: QueryRequest, current_user: User = Depends(get_current_user)):
    if current_user["role"] != 0:
        if data.project_name not in current_user["projects"]:
            raise HTTPException(status_code=500, detail=("You are not authorized to query that project"))
    #get user history
    result = await query_controller.get_top_k(user_id= current_user["id"], embed_client=request.app.state.embedding_client,
                                               gen_client= request.app.state.generation_client,
                                               project_name= data.project_name,
                                               query=data.query,
                                               k=data.k)
    #update user history
    return JSONResponse(
            content={"status": "success", "data": jsonable_encoder(result),"user":jsonable_encoder(current_user)},
            status_code=200
        )
