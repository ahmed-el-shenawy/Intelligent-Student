# routes/system.py
from fastapi import APIRouter

system_router = APIRouter()

@system_router.post("/reset")
async def reset_system():
    pass
