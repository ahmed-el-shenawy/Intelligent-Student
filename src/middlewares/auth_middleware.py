# middlewares/auth_middleware.py
from starlette.types import ASGIApp, Receive, Scope, Send
from fastapi import Request
from helpers.security import decode_token
from sqlalchemy import UUID, select
from helpers.logger import current_user_id
from helpers.config import settings
from helpers.db_connection import async_session
from models.postgres.tables_schema.tables import User

class AuthMiddleware:
    def __init__(self, app: ASGIApp):
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send):
        if scope["type"] == "http":
            request = Request(scope, receive)
            user_data = {"id": "anonymous", "username": "anonymous", "role": None}

            try:
                auth_header = request.headers.get("Authorization")
                if auth_header and auth_header.startswith("Bearer "):
                    token = auth_header[7:]
                    payload = decode_token(token)
                    uid = payload.get("sub")
                    if uid:
                        async with async_session() as db:
                            result = await db.execute(select(User).where(User.id == uid))
                            user = result.scalar_one_or_none()
                            if user:
                                user_data = {
                                    "id": user.id,
                                    "username": user.username,
                                    "role": user.role
                                }
            except Exception:
                pass

            # set ContextVar for logging
            current_user_id.set(user_data["id"])
            # store full user in request scope for routes
            scope["user"] = user_data

        await self.app(scope, receive, send)
