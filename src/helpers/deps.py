# core/deps.py
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from models.postgres.tables_schema.tables import Project, ProjectUser, User
from helpers.security import SECRET_KEY, ALGORITHM
from helpers.db_connection import get_db

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")

async def get_current_user(token: str = Depends(oauth2_scheme), db: AsyncSession = Depends(get_db)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: str = payload.get("sub")
        if user_id is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception

    # Fetch user
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if user is None:
        raise credentials_exception

    # Fetch projects the user belongs to
    result = await db.execute(
        select(Project).join(ProjectUser).where(ProjectUser.user_id == user.id)
    )
    projects = [project.name for project in result.scalars().all()]

    return {
        "id":user.id,
        "user": user.username,
        "role": user.role,
        "projects": projects
    }
