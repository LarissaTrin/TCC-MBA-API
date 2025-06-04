from typing import Optional
from datetime import datetime

from app.schemas.base import CustomBaseModel
from app.schemas.user_schema import UserSchemaBase


class CommentSchemaBase(CustomBaseModel):
    id: Optional[int] = None
    description: Optional[str] = None


class CommentCreateSchema(CommentSchemaBase):
    description: str
    card_id: int


class CommentSchema(CommentSchemaBase):
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    user: Optional[UserSchemaBase] = None
