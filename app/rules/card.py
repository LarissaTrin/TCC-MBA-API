from datetime import datetime
from sqlalchemy import cast, delete, or_, select, func, and_, String
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import NoResultFound

from fastapi import HTTPException

from app.db.models.approver_model import ApproverModel
from app.db.models.card_dependency_model import CardDependencyModel
from app.db.models.card_history_model import CardHistoryModel
from app.db.models.card_model import CardModel
from app.db.models.list_model import ListModel
from app.db.models.project_user_model import ProjectUserModel
from app.db.models.role_model import RoleModel
from app.db.models.tag_card_model import TagCardModel
from app.db.models.tag_model import TagModel
from app.db.models.task_card_model import TaskCardModel
from app.schemas.card_schema import (
    CardDependenciesResponse,
    CardDependencyItem,
    CardReorderItem,
    CardSchemaBase,
    CardSchemaUp,
    CardSearchResult,
)
from app.schemas.list_schema import ListSchemaProject


class CardRules:
    def __init__(self, db_session: AsyncSession):
        self.db_session = db_session

    async def add_card(self, list_id: int, card_data: CardSchemaBase) -> int:
        """
        Adds a new card to the specified list, automatically assigning the card
        number based on the total number of cards in the project.

        Args:
            list_id (int): ID of the list where the card will be added.
            card_data (CardSchemaBase): Card data (card_number is assigned automatically).

        Returns:
            int: ID of the newly created card.
        """
        # Check if the list exists and retrieve project_id
        list_query = select(ListModel).where(ListModel.id == list_id)
        result = await self.db_session.execute(list_query)
        list_obj: ListSchemaProject | None = result.scalars().unique().one_or_none()

        if not list_obj:
            raise NoResultFound(f"List id={list_id} not found.")

        project_id = list_obj.project_id

        # Count all cards in the project (across all lists)
        count_query = (
            select(func.count(CardModel.id))
            .join(ListModel, ListModel.id == CardModel.list_id)
            .where(ListModel.project_id == project_id)
        )
        result = await self.db_session.execute(count_query)
        total_cards = result.scalar_one() or 0

        new_card_number = total_cards + 1

        try:
            new_card = CardModel(
                title=card_data.title,
                card_number=new_card_number,
                list_id=list_id,
                created_at=datetime.utcnow(),
            )
            self.db_session.add(new_card)
            await self.db_session.flush()
            self.db_session.add(
                CardHistoryModel(
                    card_id=new_card.id,
                    action="created",
                    new_value=card_data.title,
                )
            )
            await self.db_session.commit()
            await self.db_session.refresh(new_card)
            return new_card.id
        except Exception as e:
            await self.db_session.rollback()
            raise e

    async def get_card_by_id(self, card_id: int) -> CardModel:
        """
        Fetches a card by ID with all defined relationships loaded.

        Args:
            card_id (int): ID of the card to retrieve.

        Returns:
            CardModel: The found card with relationships loaded.

        Raises:
            NoResultFound: If no card with the given ID exists.
        """
        card = await self._get_card_or_404(card_id)

        return card

    async def update_card(self, card_id: int, data: CardSchemaUp) -> CardModel:
        """
        Updates a card's simple fields and relationships (tags, approvers, tasks).

        Updates existing records, creates new ones, and removes absent entries.

        Args:
            card_id (int): ID of the card to update.
            data (CardSchemaUp): Data received for the update.

        Returns:
            CardModel: Updated card instance.

        Raises:
            NoResultFound: If the card does not exist.
        """
        card = await self._get_card_or_404(card_id)

        # --- Detect list change for audit log and completed_at ---
        if data.list_id is not None and data.list_id != card.list_id:
            old_list_result = await self.db_session.execute(
                select(ListModel).where(ListModel.id == card.list_id)
            )
            old_list = old_list_result.scalars().unique().one_or_none()

            new_list_result = await self.db_session.execute(
                select(ListModel).where(ListModel.id == data.list_id)
            )
            new_list = new_list_result.scalars().unique().one_or_none()

            if new_list:
                # Set completed_at when entering the final list; clear it when leaving
                card.completed_at = datetime.utcnow() if new_list.is_final else None

                # Record in history
                self.db_session.add(
                    CardHistoryModel(
                        card_id=card.id,
                        action="moved",
                        old_value=old_list.name if old_list else str(card.list_id),
                        new_value=new_list.name,
                    )
                )

        # --- Audit Log: edited (title changed) ---
        if data.title is not None and data.title != card.title:
            self.db_session.add(
                CardHistoryModel(
                    card_id=card.id,
                    action="edited",
                    old_value=card.title,
                    new_value=data.title,
                )
            )

        # --- Audit Log: assigned, priority_changed, due_date_changed ---
        if data.user_id is not None and data.user_id != card.user_id:
            self.db_session.add(
                CardHistoryModel(
                    card_id=card.id,
                    action="assigned",
                    old_value=str(card.user_id) if card.user_id else "Unassigned",
                    new_value=str(data.user_id),
                )
            )

        if data.priority is not None and data.priority != card.priority:
            self.db_session.add(
                CardHistoryModel(
                    card_id=card.id,
                    action="priority_changed",
                    old_value=str(card.priority) if card.priority is not None else "No priority",
                    new_value=str(data.priority),
                )
            )

        if data.date is not None and data.date != card.date:
            self.db_session.add(
                CardHistoryModel(
                    card_id=card.id,
                    action="due_date_changed",
                    old_value=card.date.strftime("%Y-%m-%d") if card.date else "No date",
                    new_value=data.date.strftime("%Y-%m-%d"),
                )
            )

        # --- Update simple fields ---
        for field in [
            "title",
            "user_id",
            "description",
            "date",
            "start_date",
            "end_date",
            "priority",
            "planned_hours",
            "completed_hours",
            "story_points",
            "list_id",
            "blocked",
            "sort_order",
            "category_id",
        ]:
            if (value := getattr(data, field)) is not None:
                setattr(card, field, value)

        # --- Tags ---
        if data.tag_cards is not None:
            # Get project_id so we can create new tags scoped to this project
            list_result = await self.db_session.execute(
                select(ListModel).where(ListModel.id == card.list_id)
            )
            card_list = list_result.scalars().unique().one_or_none()
            project_id = card_list.project_id if card_list else None

            # Delete all existing tag_cards for this card and re-create
            await self.db_session.execute(
                delete(TagCardModel).where(TagCardModel.cardId == card.id)
            )

            seen_tag_ids: set[int] = set()
            for tag_data in data.tag_cards:
                tag_id: int | None = None

                if tag_data.name and project_id:
                    # Name takes priority: find existing tag or create a new one.
                    # Never trust tag_id from frontend (may be a fake Date.now() timestamp).
                    tag_result = await self.db_session.execute(
                        select(TagModel).where(
                            TagModel.name == tag_data.name,
                            TagModel.projectId == project_id,
                        )
                    )
                    existing_tag = tag_result.scalars().unique().one_or_none()

                    if existing_tag:
                        tag_id = existing_tag.id
                    else:
                        new_tag_model = TagModel(
                            name=tag_data.name, projectId=project_id
                        )
                        self.db_session.add(new_tag_model)
                        await self.db_session.flush()
                        tag_id = new_tag_model.id
                elif not tag_data.name:
                    # No name — trust tag_id only if it is a valid int32
                    raw = tag_data.tag_id
                    if raw and 0 < raw <= 2_147_483_647:
                        tag_id = raw
                # else: name present but no project_id — skip (cannot scope tag)

                if tag_id is not None and tag_id not in seen_tag_ids:
                    seen_tag_ids.add(tag_id)
                    self.db_session.add(
                        TagCardModel(tagId=tag_id, cardId=card.id)
                    )

        # --- Approvers ---
        if data.approvers is not None:
            existing_approvers = {a.id: a for a in card.approvers if a.id}
            received_ids = set()

            for approver_data in data.approvers:
                if approver_data.id and approver_data.id in existing_approvers:
                    approver = existing_approvers[approver_data.id]
                    if approver_data.environment is not None:
                        approver.environment = approver_data.environment
                    if approver_data.user_id is not None:
                        approver.user_id = approver_data.user_id
                    received_ids.add(approver_data.id)
                else:
                    new_approver = ApproverModel(
                        **approver_data.dict(exclude={"id"}), card_id=card.id
                    )
                    self.db_session.add(new_approver)

            if existing_approvers:
                await self.db_session.execute(
                    delete(ApproverModel).where(
                        ApproverModel.card_id == card.id,
                        ApproverModel.id.notin_(received_ids),
                    )
                )

        # --- Tasks ---
        if data.tasks_card is not None:
            existing_tasks = {t.id: t for t in card.tasks_card if t.id}
            received_ids = set()

            for task_data in data.tasks_card:
                if task_data.id and task_data.id in existing_tasks:
                    task = existing_tasks[task_data.id]
                    if task_data.title is not None:
                        task.title = task_data.title
                    if task_data.completed is not None:
                        task.completed = task_data.completed
                    if task_data.user_id is not None:
                        task.userId = task_data.user_id
                    if task_data.date is not None:
                        task.date = task_data.date
                    received_ids.add(task_data.id)
                else:
                    new_task = TaskCardModel(
                        title=task_data.title,
                        date=task_data.date,
                        completed=task_data.completed or False,
                        userId=task_data.user_id,
                        cardId=card.id,
                    )
                    self.db_session.add(new_task)
                    self.db_session.add(
                        CardHistoryModel(
                            card_id=card.id,
                            action="task_added",
                            new_value=task_data.title,
                        )
                    )

            if existing_tasks:
                await self.db_session.execute(
                    delete(TaskCardModel).where(
                        TaskCardModel.cardId == card.id,
                        TaskCardModel.id.notin_(received_ids),
                    )
                )

        await self.db_session.commit()
        await self.db_session.refresh(card)
        return card

    async def bulk_reorder(self, items: list[CardReorderItem]) -> None:
        """Updates sort_order for multiple cards in a single transaction."""
        if not items:
            return
        card_ids = [item.card_id for item in items]
        result = await self.db_session.execute(
            select(CardModel).where(CardModel.id.in_(card_ids))
        )
        cards_by_id = {c.id: c for c in result.unique().scalars().all()}
        for item in items:
            card = cards_by_id.get(item.card_id)
            if card:
                card.sort_order = item.sort_order
        await self.db_session.commit()

    async def get_card_history(self, card_id: int) -> list[CardHistoryModel]:
        """
        Returns the event history of a card in reverse chronological order.

        Args:
            card_id (int): ID of the card.

        Returns:
            list[CardHistoryModel]: Recorded events (moved, assigned, priority_changed, due_date_changed).
        """
        query = (
            select(CardHistoryModel)
            .where(CardHistoryModel.card_id == card_id)
            .order_by(CardHistoryModel.created_at.desc())
        )
        result = await self.db_session.execute(query)
        return result.scalars().all()

    async def delete_card(self, card_id: int, user_id: int) -> None:
        """
        Deletes a card and its relationships (tags, approvers, tasks).
        Only SuperAdmin or Admin of the project can delete cards.

        Args:
            card_id (int): ID of the card to delete.
            user_id (int): ID of the user requesting the deletion.

        Raises:
            NoResultFound: If the card does not exist.
            HTTPException: If the user is not SuperAdmin or Admin.
        """
        await self._check_delete_permission(card_id, user_id)
        card = await self._get_card_or_404(card_id)

        await self.db_session.delete(card)

        await self.db_session.commit()

    async def search_cards(self, q: str, project_id: int | None) -> list[CardSearchResult]:
        """
        Searches cards by title or number, returning up to 10 results.
        If project_id is provided, filters by project.
        """
        query = select(CardModel).join(ListModel, ListModel.id == CardModel.list_id)

        if project_id is not None:
            query = query.where(ListModel.project_id == project_id)

        # Search by exact number or partial title
        query = query.where(
            or_(
                cast(CardModel.card_number, String).ilike(f"%{q}%"),
                CardModel.title.ilike(f"%{q}%"),
            )
        ).limit(10)

        result = await self.db_session.execute(query)
        cards = result.scalars().unique().all()

        return [
            CardSearchResult(id=c.id, card_number=c.card_number, title=c.title)
            for c in cards
        ]

    async def get_dependencies(self, card_id: int) -> CardDependenciesResponse:
        """Retorna os cards relacionados (dependências) deste card."""
        result = await self.db_session.execute(
            select(CardDependencyModel).where(CardDependencyModel.card_id == card_id)
        )
        deps = result.scalars().unique().all()

        return CardDependenciesResponse(
            dependencies=[
                CardDependencyItem(
                    id=dep.related_card.id,
                    card_number=dep.related_card.card_number,
                    title=dep.related_card.title,
                )
                for dep in deps
            ]
        )

    async def add_dependency(self, card_id: int, related_card_id: int) -> None:
        """Adiciona um card como dependência. Registra no histórico."""
        if card_id == related_card_id:
            raise HTTPException(
                status_code=400, detail="A card cannot depend on itself."
            )

        existing = (
            await self.db_session.execute(
                select(CardDependencyModel).where(
                    and_(
                        CardDependencyModel.card_id == card_id,
                        CardDependencyModel.related_card_id == related_card_id,
                    )
                )
            )
        ).scalars().first()
        if existing:
            raise HTTPException(status_code=400, detail="Dependency already exists.")

        related = await self._get_card_or_404(related_card_id)

        self.db_session.add(
            CardDependencyModel(card_id=card_id, related_card_id=related_card_id)
        )
        self.db_session.add(
            CardHistoryModel(
                card_id=card_id,
                action="dependency_added",
                new_value=f"#{related.card_number} {related.title}",
            )
        )
        await self.db_session.commit()

    async def remove_dependency(self, card_id: int, related_card_id: int) -> None:
        """Remove uma dependência e registra no histórico."""
        related_result = await self.db_session.execute(
            select(CardModel).where(CardModel.id == related_card_id)
        )
        related = related_result.scalars().unique().one_or_none()

        await self.db_session.execute(
            delete(CardDependencyModel).where(
                and_(
                    CardDependencyModel.card_id == card_id,
                    CardDependencyModel.related_card_id == related_card_id,
                )
            )
        )

        if related:
            self.db_session.add(
                CardHistoryModel(
                    card_id=card_id,
                    action="dependency_removed",
                    old_value=f"#{related.card_number} {related.title}",
                )
            )

        await self.db_session.commit()

    async def _check_delete_permission(self, card_id: int, user_id: int) -> None:
        """
        Checks whether the user is SuperAdmin or Admin of the project the card belongs to.
        """
        query = (
            select(RoleModel.name)
            .join(ProjectUserModel, RoleModel.id == ProjectUserModel.role_id)
            .join(ListModel, ListModel.project_id == ProjectUserModel.project_id)
            .join(CardModel, CardModel.list_id == ListModel.id)
            .where(
                CardModel.id == card_id,
                ProjectUserModel.user_id == user_id,
            )
        )
        result = await self.db_session.execute(query)
        role_name = result.scalar_one_or_none()
        if role_name not in {"SuperAdmin", "Admin"}:
            raise HTTPException(
                status_code=403, detail="Apenas SuperAdmin e Admin podem deletar cards."
            )

    async def _get_card_or_404(self, card_id: int) -> CardModel:
        query = select(CardModel).where(CardModel.id == card_id)
        result = await self.db_session.execute(query)
        card = result.scalars().unique().one_or_none()
        if not card:
            raise NoResultFound(f"Card id={card_id} not found.")
        return card
