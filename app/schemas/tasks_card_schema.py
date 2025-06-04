from typing import Optional

from app.schemas.base import CustomBaseModel
from app.schemas.user_schema import UserSchemaBase


class TaskCardSchemaBase(CustomBaseModel):
    id: Optional[int] = None
    title: Optional[str] = None
    date: Optional[str] = None
    completed: Optional[bool] = False
    user_id: Optional[int] = None


class TaskCardSchema(CustomBaseModel):
    id: int
    title: Optional[str] = None
    date: Optional[str] = None
    completed: bool

    user: Optional[UserSchemaBase] = None
