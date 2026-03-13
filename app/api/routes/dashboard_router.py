from datetime import date, datetime, time, timezone

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional

from app.core.deps import get_current_user, get_session
from app.db.models.approver_model import ApproverModel
from app.db.models.card_model import CardModel
from app.db.models.list_model import ListModel
from app.db.models.project_model import ProjectModel
from app.schemas.base import CustomBaseModel
from app.schemas.user_schema import UserSchema, UserSchemaBase

router = APIRouter()


# ── Response schemas (lightweight — no full card relationship tree) ──────────


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


# ── Helper ───────────────────────────────────────────────────────────────────


def _to_dashboard_card(card: CardModel) -> DashboardCardSchema:
    lst: ListModel = card.list
    project: ProjectModel = lst.project
    return DashboardCardSchema(
        id=card.id,
        card_number=card.card_number,
        title=card.title,
        priority=card.priority,
        date=card.date,
        completed_at=card.completed_at,
        list_id=card.list_id,
        list_name=lst.name,
        project_id=project.id,
        project_title=project.title,
        user=card.user,
    )


# ── Routes ───────────────────────────────────────────────────────────────────


@router.get("/my-day", response_model=MyDayResponse)
async def my_day(
    current_user: UserSchema = Depends(get_current_user),
    db: AsyncSession = Depends(get_session),
):
    """
    Returns cards assigned to the current user that:
    - are due today, OR
    - are overdue (past due date and not yet completed)

    Uses a single lightweight query — does NOT load board data.
    """
    today_start = datetime.combine(date.today(), time.min)
    today_end = datetime.combine(date.today(), time.max)

    query = (
        select(CardModel)
        .join(CardModel.list)
        .join(ListModel.project)
        .where(
            CardModel.user_id == current_user.id,
            CardModel.completed_at.is_(None),
            CardModel.date.isnot(None),
        )
    )
    result = await db.execute(query)
    cards = result.scalars().unique().all()

    due_today = [
        _to_dashboard_card(c)
        for c in cards
        if today_start <= c.date <= today_end
    ]
    overdue = [
        _to_dashboard_card(c)
        for c in cards
        if c.date < today_start
    ]

    return MyDayResponse(due_today=due_today, overdue=overdue)


@router.get("/pending-approvals", response_model=PendingApprovalsResponse)
async def pending_approvals(
    current_user: UserSchema = Depends(get_current_user),
    db: AsyncSession = Depends(get_session),
):
    """
    Returns cards where the current user is listed as an approver
    and the card is not yet in a final list (i.e., still pending approval).
    """
    query = (
        select(CardModel)
        .join(CardModel.approvers)
        .join(CardModel.list)
        .join(ListModel.project)
        .where(
            ApproverModel.user_id == current_user.id,
            CardModel.completed_at.is_(None),
        )
    )
    result = await db.execute(query)
    cards = result.scalars().unique().all()

    return PendingApprovalsResponse(
        pending=[_to_dashboard_card(c) for c in cards]
    )
