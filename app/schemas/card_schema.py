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
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    priority: Optional[int] = None
    description: Optional[str] = None
    planned_hours: Optional[int] = None
    completed_hours: Optional[int] = None
    story_points: Optional[int] = None
    list_id: Optional[int] = None
    blocked: Optional[bool] = None
    sort_order: Optional[int] = None

    tag_cards: list[TagCardSchemaBase] = None
    approvers: list[ApproverSchemaBase] = None
    comments: list[CommentCreateSchema] = None
    tasks_card: list[TaskCardSchemaBase] = None


class CardReorderItem(CustomBaseModel):
    card_id: int
    sort_order: int


class CardReorderRequest(CustomBaseModel):
    items: list[CardReorderItem]


class CardSchema(CardSchemaUp):
    id: int
    card_number: int

    created_at: datetime
    updated_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None

    user: Optional[UserSchemaBase] = None
    tag_cards: Optional[list[TagCardSchema]] = None
    comments: Optional[list[CommentSchema]] = None
    approvers: Optional[list[ApproverSchema]] = None
    tasks_card: Optional[list[TaskCardSchema]] = None


class CardHistorySchema(CustomBaseModel):
    id: int
    action: str
    old_value: Optional[str] = None
    new_value: Optional[str] = None
    created_at: datetime


class CardDependencyItem(CustomBaseModel):
    """Representação resumida de um card dentro de uma dependência."""
    id: int
    card_number: int
    title: str


class CardDependenciesResponse(CustomBaseModel):
    dependencies: list[CardDependencyItem]


class CardDependencyAdd(CustomBaseModel):
    related_card_id: int


class CardSearchResult(CustomBaseModel):
    id: int
    card_number: int
    title: str


class CardPageResponse(CustomBaseModel):
    cards: list[CardSchema]
    total: int
    page: int
    has_more: bool
