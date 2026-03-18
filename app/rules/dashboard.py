from datetime import date, datetime, time, timedelta

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.db.models.approver_model import ApproverModel
from app.db.models.card_history_model import CardHistoryModel
from app.db.models.card_model import CardModel
from app.db.models.list_model import ListModel
from app.db.models.project_model import ProjectModel
from app.db.models.tag_card_model import TagCardModel
from app.db.models.tag_model import TagModel
from app.schemas.dashboard_schema import (
    BurndownPoint,
    BurndownResponse,
    DashboardCardSchema,
    ListDistribution,
    MyCardsResponse,
    MyDayResponse,
    PendingApprovalsResponse,
    PriorityDistribution,
    ProjectStatsResponse,
    TagDistribution,
)


class DashboardRules:
    def __init__(self, db_session: AsyncSession):
        self.db_session = db_session

    async def get_my_day(self, user_id: int) -> MyDayResponse:
        """
        Retorna cards atribuídos ao usuário que vencem hoje ou já estão atrasados
        (data passada e ainda não concluídos).
        """
        today_start = datetime.combine(date.today(), time.min)
        today_end = datetime.combine(date.today(), time.max)

        query = (
            select(CardModel)
            .join(CardModel.list)
            .join(ListModel.project)
            .where(
                CardModel.user_id == user_id,
                CardModel.completed_at.is_(None),
                CardModel.date.isnot(None),
            )
            .options(
                selectinload(CardModel.list).selectinload(ListModel.project),
                selectinload(CardModel.user),
            )
        )
        result = await self.db_session.execute(query)
        cards = result.scalars().unique().all()

        due_today = [
            self._to_dashboard_card(c)
            for c in cards
            if today_start <= c.date <= today_end
        ]
        overdue = [
            self._to_dashboard_card(c)
            for c in cards
            if c.date < today_start
        ]

        return MyDayResponse(due_today=due_today, overdue=overdue)

    async def get_pending_approvals(self, user_id: int) -> PendingApprovalsResponse:
        """
        Retorna cards onde o usuário é aprovador e o card ainda não foi concluído.
        """
        query = (
            select(CardModel)
            .join(CardModel.approvers)
            .join(CardModel.list)
            .join(ListModel.project)
            .where(
                ApproverModel.user_id == user_id,
                CardModel.completed_at.is_(None),
            )
            .options(
                selectinload(CardModel.list).selectinload(ListModel.project),
                selectinload(CardModel.user),
            )
        )
        result = await self.db_session.execute(query)
        cards = result.scalars().unique().all()

        return PendingApprovalsResponse(
            pending=[self._to_dashboard_card(c) for c in cards]
        )

    async def get_my_cards(self, user_id: int) -> MyCardsResponse:
        """
        Retorna de uma vez todos os cards relacionados ao usuário:
        - assigned: cards atribuídos ao usuário (não concluídos)
        - due_today / overdue: subconjunto dos assigned com data
        - pending_approvals: cards onde o usuário é aprovador (não concluídos)
        """
        today_start = datetime.combine(date.today(), time.min)
        today_end = datetime.combine(date.today(), time.max)

        # Cards atribuídos ao usuário que não foram concluídos
        assigned_query = (
            select(CardModel)
            .join(CardModel.list)
            .join(ListModel.project)
            .where(
                CardModel.user_id == user_id,
                CardModel.completed_at.is_(None),
            )
            .options(
                selectinload(CardModel.list).selectinload(ListModel.project),
                selectinload(CardModel.user),
            )
        )
        assigned_result = await self.db_session.execute(assigned_query)
        assigned_cards = assigned_result.scalars().unique().all()

        # Cards onde o usuário é aprovador e ainda não concluídos
        approvals_query = (
            select(CardModel)
            .join(CardModel.approvers)
            .join(CardModel.list)
            .join(ListModel.project)
            .where(
                ApproverModel.user_id == user_id,
                CardModel.completed_at.is_(None),
            )
            .options(
                selectinload(CardModel.list).selectinload(ListModel.project),
                selectinload(CardModel.user),
            )
        )
        approvals_result = await self.db_session.execute(approvals_query)
        approval_cards = approvals_result.scalars().unique().all()

        due_today = [
            c for c in assigned_cards
            if c.date and today_start <= c.date <= today_end
        ]
        overdue = [
            c for c in assigned_cards
            if c.date and c.date < today_start
        ]

        return MyCardsResponse(
            assigned=[self._to_dashboard_card(c) for c in assigned_cards],
            due_today=[self._to_dashboard_card(c) for c in due_today],
            overdue=[self._to_dashboard_card(c) for c in overdue],
            pending_approvals=[self._to_dashboard_card(c) for c in approval_cards],
        )

    async def get_project_stats(self, project_id: int) -> ProjectStatsResponse:
        """
        Retorna estatísticas agregadas de um projeto:
        - contagem de cards por coluna kanban
        - contagem de cards por prioridade
        - contagem de cards por tag
        - tempo médio de conclusão em dias (completed_at - created_at)
        """
        # 1. Cards por lista (preserva a ordem das colunas)
        by_list_stmt = (
            select(
                ListModel.name,
                ListModel.is_final,
                func.count(CardModel.id).label("cnt"),
            )
            .join(CardModel, CardModel.list_id == ListModel.id)
            .where(ListModel.project_id == project_id)
            .group_by(ListModel.id, ListModel.name, ListModel.is_final, ListModel.order)
            .order_by(ListModel.order)
        )
        by_list_rows = (await self.db_session.execute(by_list_stmt)).all()

        # 2. Cards por prioridade
        by_priority_stmt = (
            select(CardModel.priority, func.count(CardModel.id).label("cnt"))
            .join(ListModel, ListModel.id == CardModel.list_id)
            .where(ListModel.project_id == project_id)
            .group_by(CardModel.priority)
            .order_by(CardModel.priority)
        )
        by_priority_rows = (await self.db_session.execute(by_priority_stmt)).all()

        # 3. Cards por tag
        by_tag_stmt = (
            select(TagModel.name, func.count(TagCardModel.cardId).label("cnt"))
            .join(TagCardModel, TagCardModel.tagId == TagModel.id)
            .join(CardModel, CardModel.id == TagCardModel.cardId)
            .join(ListModel, ListModel.id == CardModel.list_id)
            .where(ListModel.project_id == project_id)
            .group_by(TagModel.id, TagModel.name)
            .order_by(func.count(TagCardModel.cardId).desc())
        )
        by_tag_rows = (await self.db_session.execute(by_tag_stmt)).all()

        # 4. Lead Time: avg(completed_at - created_at) em dias
        lead_stmt = (
            select(
                func.avg(
                    func.extract(
                        "epoch", CardModel.completed_at - CardModel.created_at
                    )
                    / 86400
                )
            )
            .join(ListModel, ListModel.id == CardModel.list_id)
            .where(
                ListModel.project_id == project_id,
                CardModel.completed_at.isnot(None),
                CardModel.created_at.isnot(None),
            )
        )
        lead_raw = (await self.db_session.execute(lead_stmt)).scalar()
        lead_time = round(float(lead_raw), 1) if lead_raw is not None else None

        # 5. Cycle Time: avg(completed_at - primeiro "moved") em dias
        first_moved_subq = (
            select(
                CardHistoryModel.card_id,
                func.min(CardHistoryModel.created_at).label("first_moved"),
            )
            .where(CardHistoryModel.action == "moved")
            .group_by(CardHistoryModel.card_id)
            .subquery()
        )
        cycle_stmt = (
            select(
                func.avg(
                    func.extract(
                        "epoch",
                        CardModel.completed_at - first_moved_subq.c.first_moved,
                    )
                    / 86400
                )
            )
            .join(ListModel, ListModel.id == CardModel.list_id)
            .join(first_moved_subq, first_moved_subq.c.card_id == CardModel.id)
            .where(
                ListModel.project_id == project_id,
                CardModel.completed_at.isnot(None),
            )
        )
        cycle_raw = (await self.db_session.execute(cycle_stmt)).scalar()
        cycle_time = round(float(cycle_raw), 1) if cycle_raw is not None else None

        total = sum(r.cnt for r in by_list_rows)

        return ProjectStatsResponse(
            total_cards=total,
            by_list=[
                ListDistribution(list_name=r.name, is_final=r.is_final, count=r.cnt)
                for r in by_list_rows
            ],
            by_priority=[
                PriorityDistribution(priority=r.priority, count=r.cnt)
                for r in by_priority_rows
            ],
            by_tag=[
                TagDistribution(tag_name=r.name, count=r.cnt)
                for r in by_tag_rows
            ],
            lead_time_days=lead_time,
            cycle_time_days=cycle_time,
        )

    async def get_burndown(
        self, project_id: int, start: date, end: date
    ) -> BurndownResponse:
        """
        Reconstrói o burndown chart de um período a partir de created_at e completed_at.

        Para cada dia D no intervalo [start, end]:
          remaining(D) = soma de story_points (ou 1) de cards que:
            - foram criados até o fim do dia D  (created_at <= D 23:59:59)
            - ainda não estavam concluídos no fim do dia D
              (completed_at IS NULL OR completed_at > D 23:59:59)
        """
        # Busca todos os cards do projeto com os campos necessários
        stmt = (
            select(CardModel.created_at, CardModel.completed_at, CardModel.story_points)
            .join(ListModel, ListModel.id == CardModel.list_id)
            .where(ListModel.project_id == project_id)
        )
        rows = (await self.db_session.execute(stmt)).all()

        # Total de story points (ou contagem) no período
        total = sum(r.story_points if r.story_points else 1 for r in rows)

        days_count = (end - start).days + 1
        points: list[BurndownPoint] = []

        for i in range(days_count):
            day = start + timedelta(days=i)
            day_end = datetime.combine(day, time.max)
            day_start_dt = datetime.combine(start, time.min)

            remaining = 0
            for r in rows:
                created = r.created_at
                completed = r.completed_at
                weight = r.story_points if r.story_points else 1

                # Card existia neste dia?
                if created is None or created > day_end:
                    continue
                # Card ainda estava aberto no fim deste dia?
                if completed is None or completed > day_end:
                    remaining += weight

            # Linha ideal: decresce linearmente do total (dia 0) até 0 (último dia)
            ideal = total * (1 - i / max(days_count - 1, 1))

            points.append(
                BurndownPoint(
                    date=day.strftime("%Y-%m-%d"),
                    remaining=remaining,
                    ideal=round(ideal, 1),
                )
            )

        return BurndownResponse(
            start=start.strftime("%Y-%m-%d"),
            end=end.strftime("%Y-%m-%d"),
            total=total,
            points=points,
        )

    def _to_dashboard_card(self, card: CardModel) -> DashboardCardSchema:
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
