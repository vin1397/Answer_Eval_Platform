"""
Pydantic request/response schemas for authentication.
"""
from pydantic import BaseModel, EmailStr, Field

from models.enums import UserRole


class LoginRequest(BaseModel):
    username: str = Field(..., min_length=3, max_length=64)
    password: str = Field(..., min_length=6, max_length=128)
    remember_me: bool = False


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    user: "UserOut"


class RefreshRequest(BaseModel):
    refresh_token: str


class ForgotPasswordRequest(BaseModel):
    email: EmailStr


class UserOut(BaseModel):
    id: int
    username: str
    email: EmailStr
    full_name: str
    role: UserRole
    department: str | None = None
    is_active: bool

    model_config = {"from_attributes": True}


class UserCreate(BaseModel):
    username: str = Field(..., min_length=3, max_length=64)
    email: EmailStr
    full_name: str
    password: str = Field(..., min_length=8, max_length=128)
    role: UserRole = UserRole.TEACHER
    department: str | None = None


class ChangePasswordRequest(BaseModel):
    old_password: str
    new_password: str = Field(..., min_length=8, max_length=128)


TokenResponse.model_rebuild()
