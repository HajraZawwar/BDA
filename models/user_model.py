from pydantic import BaseModel, EmailStr
from typing import Optional
from datetime import datetime

class UserBase(BaseModel):
    username: str
    email: EmailStr

class UserCreate(UserBase):
    password: str
    avatar_url: Optional[str] = None  # avatar image URL stored in S3

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class UserInDB(UserBase):
    id: str
    avatar_url: Optional[str] = None
    created_at: datetime

class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
