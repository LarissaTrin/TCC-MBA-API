from typing import Optional
from datetime import datetime

from app.schemas.approver_schema import ApproverSchema, ApproverSchemaBase
from app.schemas.base import CustomBaseModel
from app.schemas.comment_schema import CommentCreateSchema, CommentSchema
from app.schemas.tag_card_schema import TagCardSchema, TagCardSchemaBase
from app.schemas.tasks_card_schema import TaskCardSchema, TaskCardSchemaBase
from app.schemas.user_schema import UserSchemaBase


class CardSchemaBase(CustomBaseModel):
    title: str


class CardSchemaUp(CustomBaseModel):
    id: Optional[int] = None
    title: Optional[str] = None
    user_id: Optional[int] = None
    date: Optional[datetime] = None
    priority: Optional[int] = None
    description: Optional[str] = None
    planned_hours: Optional[int] = None
    completed_hours: Optional[int] = None
    story_points: Optional[int] = None
    list_id: Optional[int] = None

    tag_cards: list[TagCardSchemaBase] = None
    approvers: list[ApproverSchemaBase] = None
    comments: list[CommentCreateSchema] = None
    tasks_card: list[TaskCardSchemaBase] = None


class CardSchema(CardSchemaUp):
    id: int
    card_number: int

    created_at: datetime
    updated_at: Optional[datetime] = None

    user: Optional[UserSchemaBase] = None
    tag_cards: Optional[list[TagCardSchema]] = None
    comments: Optional[list[CommentSchema]] = None
    approvers: Optional[list[ApproverSchema]] = None
    tasks_card: Optional[list[TaskCardSchema]] = None
