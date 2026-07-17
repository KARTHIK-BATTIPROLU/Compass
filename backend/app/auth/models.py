from enum import Enum
from typing import Optional

from pydantic import BaseModel, EmailStr, Field


class Role(str, Enum):
    TEACHER = "teacher"
    STUDENT = "student"


class UserCreate(BaseModel):
    email: EmailStr
    password: str = Field(min_length=6)
    name: str = Field(min_length=1)
    role: Role


class UserLogin(BaseModel):
    email: EmailStr
    password: str
    role: Role


class UserPublic(BaseModel):
    id: str
    email: EmailStr
    name: str
    role: Role


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserPublic


class TokenPayload(BaseModel):
    sub: str
    role: Role
    email: str
    name: str
    exp: Optional[int] = None
