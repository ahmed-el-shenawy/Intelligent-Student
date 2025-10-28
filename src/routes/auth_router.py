# routers/auth_router.py
from fastapi import APIRouter, HTTPException, Depends, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import delete, select
from datetime import datetime, timedelta, timezone

from helpers.deps import get_current_user
from models.postgres.ProjectsModel import ProjectModel
from models.postgres.operations_schema.projects import ProjectSearch
from models.postgres.tables_schema.tables import ProjectUser, User, RefreshToken
from helpers.security import hash_password, verify_password, create_access_token, create_refresh_token, decode_token
from helpers.db_connection import get_db
import uuid

from pydantic import BaseModel

class UserCreate(BaseModel):
    username: str
    password: str

class RefreshTokenRequest(BaseModel):
    refresh_token: str
    
class UserLogin(BaseModel):
    username: str
    password: str

class UserAouthorize(BaseModel):
    username:str
    project_name:str

auth_router = APIRouter(prefix="/auth", tags=["Auth"])

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")

project_model = ProjectModel()
# ---------- Signup ----------
@auth_router.post("/signup")
async def signup(user: UserCreate, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(User).where(User.username == user.username))
    if result.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Username already exists")

    new_user = User(username=user.username, hashed_password=hash_password(user.password))
    db.add(new_user)
    await db.commit()
    return {"msg": "User created successfully"}

# ---------- Authroize ----------
@auth_router.post("/authorize")
async def authorize(data: UserAouthorize, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user) ):
    if not current_user["role"] == 0:
        raise HTTPException(status_code=400, detail="You are not permited to do that")
    project_search = ProjectSearch(name = data.project_name)
    project = await project_model.search_by_name(data = project_search)

    result = await db.execute(select(User).where(User.username == data.username))
    user =  result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=400, detail="that user does not exist")
    
    result = await db.execute(select(ProjectUser).where(ProjectUser.user_id == user.id, ProjectUser.project_id == project.id))
    if result.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Username already authorized with that project")
    new_user_project = ProjectUser(project_id=project.id, user_id = user.id)
    db.add(new_user_project)
    await db.commit()
    return {"msg": "Project authorized successfully"}

# ---------- Login ----------
@auth_router.post("/login")
async def login(user: UserLogin, db: AsyncSession = Depends(get_db)):
    # Fetch the user from DB
    result = await db.execute(select(User).where(User.username == user.username))
    db_user = result.scalar_one_or_none()

    if not db_user or not verify_password(user.password, db_user.hashed_password):
        raise HTTPException(status_code=401, detail="Invalid credentials")

    # remove expired tokens
    await db.execute(
        delete(RefreshToken)
        .where(RefreshToken.user_id == db_user.id)
        .where(RefreshToken.expires_at < datetime.now(timezone.utc)))
    await db.commit()

    access_token = create_access_token({"sub": str(db_user.id)})
    refresh_token = create_refresh_token(db_user.id)

    # Store refresh token
    db.add(RefreshToken(
        user_id=db_user.id,
        hashed_token=refresh_token,
        expires_at=datetime.now(timezone.utc) + timedelta(days=7)
    ))
    await db.commit()

    return {"access_token": access_token, "refresh_token": refresh_token, "token_type": "bearer"}

# ---------- Refresh Token ----------
@auth_router.post("/refresh")
async def refresh_token(payload: RefreshTokenRequest, db: AsyncSession = Depends(get_db)):
    token_data = decode_token(payload.refresh_token)
    if not token_data or token_data.get("type") != "refresh":
        raise HTTPException(status_code=401, detail="Invalid refresh token")

    user_id = token_data.get("sub")
    token_query = await db.execute(
        select(RefreshToken).where(RefreshToken.hashed_token == payload.refresh_token)
    )
    token_entry = token_query.scalar_one_or_none()

    if not token_entry or token_entry.revoked or token_entry.expires_at < datetime.now(timezone.utc):
        raise HTTPException(status_code=401, detail="Expired or revoked refresh token")

    new_access = create_access_token({"sub": user_id})
    return {"access_token": new_access, "token_type": "bearer"}
