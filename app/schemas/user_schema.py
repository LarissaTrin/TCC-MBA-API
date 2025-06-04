from datetime import datetime
import re
from typing import Optional

from pydantic import EmailStr, field_validator

from app.schemas.base import CustomBaseModel


class UserSchemaBase(CustomBaseModel):
    id: Optional[int] = None
    username: str
    first_name: str
    last_name: str
    email: EmailStr
    is_admin: bool = False

    @field_validator("username")
    def validate_username(cls, value):
        if not re.match("^([a-z]|[A-Z]|[0-9]|-|_|@)+$", value):
            raise ValueError("Invalid username")
        return value


class UserLoginSchema(CustomBaseModel):
    password: str
    username: str


class UserSchemaCreate(UserSchemaBase):
    password: str
    username: str


class UserSchema(UserSchemaBase):
    username: str


class UserSchemaByEmail(CustomBaseModel):
    first_name: str
    last_name: str
    email: EmailStr


class UserSchemaUp(UserSchemaBase):
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    password: Optional[str] = None
    email: Optional[EmailStr] = None
    is_admin: Optional[bool] = None


class TokenData(CustomBaseModel):
    access_token: str
    expires_at: datetime


class ForgotPasswordRequest(CustomBaseModel):
    email: EmailStr


class ResetPasswordRequest(CustomBaseModel):
    new_password: str
