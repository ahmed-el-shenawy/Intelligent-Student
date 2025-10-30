# helpers/deps.py
from fastapi import Request, HTTPException, status

async def get_current_user(request: Request):
    user = request.scope.get("user")
    if not user or user["id"] == "anonymous":
        raise HTTPException(status_code=401, detail="Not authenticated")
    return user
