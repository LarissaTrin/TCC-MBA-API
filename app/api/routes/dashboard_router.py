from datetime import date

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_current_user, get_session
from app.rules.dashboard import DashboardRules
from app.schemas.dashboard_schema import (
    BurndownResponse,
    MyCardsResponse,
    MyDayResponse,
    PendingApprovalsResponse,
    ProjectStatsResponse,
)
from app.schemas.user_schema import UserSchema

router = APIRouter()


@router.get("/my-cards", response_model=MyCardsResponse)
async def my_cards(
    current_user: UserSchema = Depends(get_current_user),
    db: AsyncSession = Depends(get_session),
):
    """
    Retorna de uma vez todos os cards relacionados ao usuário logado:
    assigned, due_today, overdue e pending_approvals.
    """
    rules = DashboardRules(db)
    return await rules.get_my_cards(current_user.id)


@router.get("/my-day", response_model=MyDayResponse)
async def my_day(
    current_user: UserSchema = Depends(get_current_user),
    db: AsyncSession = Depends(get_session),
):
    """
    Retorna cards atribuídos ao usuário que vencem hoje ou estão atrasados.
    """
    rules = DashboardRules(db)
    return await rules.get_my_day(current_user.id)


@router.get("/pending-approvals", response_model=PendingApprovalsResponse)
async def pending_approvals(
    current_user: UserSchema = Depends(get_current_user),
    db: AsyncSession = Depends(get_session),
):
    """
    Retorna cards onde o usuário é aprovador e ainda não foram concluídos.
    """
    rules = DashboardRules(db)
    return await rules.get_pending_approvals(current_user.id)


@router.get("/project/{project_id}/stats", response_model=ProjectStatsResponse)
async def project_stats(
    project_id: int,
    current_user: UserSchema = Depends(get_current_user),
    db: AsyncSession = Depends(get_session),
):
    """
    Retorna estatísticas agregadas de um projeto:
    cards por coluna, por prioridade, por tag e tempo médio de conclusão.
    """
    rules = DashboardRules(db)
    return await rules.get_project_stats(project_id)


@router.get("/project/{project_id}/burndown", response_model=BurndownResponse)
async def project_burndown(
    project_id: int,
    start: date = Query(..., description="Data de início do período (YYYY-MM-DD)"),
    end: date = Query(..., description="Data de fim do período (YYYY-MM-DD)"),
    current_user: UserSchema = Depends(get_current_user),
    db: AsyncSession = Depends(get_session),
):
    """
    Retorna os dados do burndown chart para um período específico.
    Reconstrói o estado diário a partir de card.created_at e card.completed_at.
    """
    rules = DashboardRules(db)
    return await rules.get_burndown(project_id, start, end)
