from typing import Optional

from app.schemas.base import CustomBaseModel
from app.schemas.user_schema import UserSchemaBase
from app.schemas.role_schema import RoleSchemaBase


class ProjectUserSchemaBase(CustomBaseModel):
    id: Optional[int] = None
    user_id: int
    role_id: int


class ProjectUserSchema(ProjectUserSchemaBase):
    user: Optional[UserSchemaBase] = None
    role: Optional[RoleSchemaBase] = None
