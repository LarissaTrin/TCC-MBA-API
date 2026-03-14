from datetime import datetime
from typing import Optional

from app.schemas.base import CustomBaseModel
from app.schemas.user_schema import UserSchemaBase


class DashboardCardSchema(CustomBaseModel):
    id: int
    card_number: int
    title: str
    priority: Optional[int] = None
    date: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    list_id: int
    list_name: str
    project_id: int
    project_title: str
    user: Optional[UserSchemaBase] = None


class MyDayResponse(CustomBaseModel):
    due_today: list[DashboardCardSchema]
    overdue: list[DashboardCardSchema]


class PendingApprovalsResponse(CustomBaseModel):
    pending: list[DashboardCardSchema]


class ListDistribution(CustomBaseModel):
    list_name: str
    is_final: bool
    count: int


class PriorityDistribution(CustomBaseModel):
    priority: Optional[int] = None
    count: int


class TagDistribution(CustomBaseModel):
    tag_name: str
    count: int


class ProjectStatsResponse(CustomBaseModel):
    total_cards: int
    by_list: list[ListDistribution]
    by_priority: list[PriorityDistribution]
    by_tag: list[TagDistribution]
    lead_time_days: Optional[float] = None   # avg(completed_at - created_at)
    cycle_time_days: Optional[float] = None  # avg(completed_at - primeiro "moved")


class BurndownPoint(CustomBaseModel):
    date: str       # "YYYY-MM-DD"
    remaining: int  # story points (ou contagem) ainda em aberto naquele dia
    ideal: float    # linha ideal interpolada


class BurndownResponse(CustomBaseModel):
    start: str
    end: str
    total: int
    points: list[BurndownPoint]
