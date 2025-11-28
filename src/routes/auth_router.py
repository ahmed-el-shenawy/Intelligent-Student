from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession
from helpers.db_connection import get_db
from helpers.deps import get_current_user
from helpers.handle_exceptions import handle_exceptions
from routes.schemes.auth import UserCreate, UserLogin, RefreshTokenRequest, UserAuthorize, UpdateRoleRequest
from controllers.AuthController import AuthController
from helpers.logger import get_logger

logger = get_logger("auth_router")

auth_router = APIRouter(prefix="/auth", tags=["Auth"])
auth_controller = AuthController()

 
# --- ROUTES ---
@auth_router.post("/signup")
@handle_exceptions
async def signup(user: UserCreate, db: AsyncSession = Depends(get_db)):
    return await auth_controller.signup(db, user)

@auth_router.post("/login")
@handle_exceptions
async def login(user: UserLogin, db: AsyncSession = Depends(get_db)):
    return await auth_controller.login(db, user)

@auth_router.post("/refresh")
@handle_exceptions
async def refresh_token(payload: RefreshTokenRequest, db: AsyncSession = Depends(get_db)):
    return await auth_controller.refresh(db, payload)

@auth_router.post("/logout")
@handle_exceptions
async def logout(db: AsyncSession = Depends(get_db), current_user = Depends(get_current_user)):
    return await auth_controller.logout(db, current_user)

@auth_router.post("/authorize")
@handle_exceptions
async def authorize(data: UserAuthorize, db: AsyncSession = Depends(get_db), current_user = Depends(get_current_user)):
    return await auth_controller.authorize(db, current_user, data)

@auth_router.post("/deauthorize")
@handle_exceptions
async def deauthorize(data: UserAuthorize, db: AsyncSession = Depends(get_db), current_user = Depends(get_current_user)):
    return await auth_controller.deauthorize(db, current_user, data)

@auth_router.post("/update-role")
@handle_exceptions
async def update_role(data: UpdateRoleRequest, db: AsyncSession = Depends(get_db), current_user = Depends(get_current_user)):
    return await auth_controller.update_privilege(db, current_user, data)
