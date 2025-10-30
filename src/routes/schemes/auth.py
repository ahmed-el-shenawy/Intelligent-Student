# routes/schemes/auth.py
from pydantic import BaseModel

class UserCreate(BaseModel):
    username: str
    password: str

class UserLogin(BaseModel):
    username: str
    password: str

class UserAuthorize(BaseModel):
    username: str
    project_name: str

class RefreshTokenRequest(BaseModel):
    refresh_token: str

class UpdateRoleRequest(BaseModel):
    username: str
    new_role: int
