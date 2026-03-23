from typing import Optional
from datetime import datetime

from app.schemas.base import CustomBaseModel
from app.schemas.list_schema import ListSchema, ListSchemaUp
from app.schemas.project_user_schema import ProjectUserSchema
from app.schemas.user_schema import UserSchemaBase


class ProjectSchemaBase(CustomBaseModel):
    id: Optional[int] = None
    title: str
    description: str


class ProjectSchemaUp(ProjectSchemaBase):
    title: Optional[str] = None
    description: Optional[str] = None
    lists: Optional[list[ListSchemaUp]] = None


class ProjectSchema(ProjectSchemaBase):
    id: int
    created_at: datetime
    updated_at: Optional[datetime]

    creator: UserSchemaBase
    lists: Optional[list[ListSchema]] = []
    project_users: Optional[list[ProjectUserSchema]] = []
    # tags: Optional[list["TagSchema"]] = []


class InviteEntry(CustomBaseModel):
    email: str
    role: str = "User"  # "User", "Leader" ou "Admin"


class InviteUsersRequest(CustomBaseModel):
    invites: list[InviteEntry]


class InviteUserResult(CustomBaseModel):
    email: str
    registered: bool
    already_member: bool = False


class InviteUsersResponse(CustomBaseModel):
    results: list[InviteUserResult]
