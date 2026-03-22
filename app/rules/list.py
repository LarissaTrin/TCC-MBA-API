from fastapi import HTTPException
from sqlalchemy import func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload, joinedload
from sqlalchemy.exc import NoResultFound

from app.db.models.card_model import CardModel
from app.db.models.list_model import ListModel
from app.db.models.project_user_model import ProjectUserModel
from app.db.models.role_model import RoleModel
from app.db.models.tag_card_model import TagCardModel
from app.schemas.list_schema import ListSchemaUp

# Roles allowed to create/update lists
_CAN_MANAGE_LISTS = {"SuperAdmin", "Admin", "Leader"}
# Roles allowed to delete lists
_CAN_DELETE_LISTS = {"SuperAdmin", "Admin"}


class ListRules:
    def __init__(self, db_session: AsyncSession):
        self.db_session = db_session

    async def _get_role(self, project_id: int, user_id: int) -> str | None:
        query = (
            select(RoleModel.name)
            .join(ProjectUserModel, RoleModel.id == ProjectUserModel.role_id)
            .where(
                ProjectUserModel.project_id == project_id,
                ProjectUserModel.user_id == user_id,
            )
        )
        result = await self.db_session.execute(query)
        return result.scalar_one_or_none()

    async def _check_manage_permission(self, project_id: int, user_id: int):
        """SuperAdmin, Admin, and Leader can create/update lists."""
        role = await self._get_role(project_id, user_id)
        if role not in _CAN_MANAGE_LISTS:
            raise HTTPException(
                status_code=403,
                detail="Only SuperAdmin, Admin, and Leader can manage lists.",
            )

    async def _check_delete_permission(self, project_id: int, user_id: int):
        """Only SuperAdmin and Admin can delete lists."""
        role = await self._get_role(project_id, user_id)
        if role not in _CAN_DELETE_LISTS:
            raise HTTPException(
                status_code=403,
                detail="Only SuperAdmin and Admin can delete lists.",
            )

    async def get_lists_slim(self, project_id: int) -> list[ListModel]:
        """Return lists without cards — used for the initial board load."""
        query = (
            select(ListModel)
            .where(ListModel.project_id == project_id)
            .order_by(ListModel.order)
        )
        result = await self.db_session.execute(query)
        return result.unique().scalars().all()

    async def get_cards_for_list_paginated(
        self, list_id: int, page: int = 1, limit: int = 20
    ) -> dict:
        """Return cards for a list with offset-based pagination."""
        offset = (page - 1) * limit

        count_q = select(func.count()).where(CardModel.list_id == list_id)
        total = (await self.db_session.execute(count_q)).scalar()

        cards_q = (
            select(CardModel)
            .options(
                joinedload(CardModel.user),
                selectinload(CardModel.tag_cards).joinedload(TagCardModel.tag),
                selectinload(CardModel.tasks_card),
            )
            .where(CardModel.list_id == list_id)
            .order_by(CardModel.card_number)
            .offset(offset)
            .limit(limit)
        )
        result = await self.db_session.execute(cards_q)
        cards = result.unique().scalars().all()

        return {
            "cards": cards,
            "total": total,
            "page": page,
            "has_more": (offset + len(cards)) < total,
        }

    async def get_lists_for_project(self, project_id: int) -> list[ListModel]:
        query = (
            select(ListModel)
            .options(
                selectinload(ListModel.cards).options(
                    joinedload(CardModel.user),
                )
            )
            .where(ListModel.project_id == project_id)
        )
        result = await self.db_session.execute(query)
        return result.unique().scalars().all()

    async def add_list(
        self, project_id: int, data: ListSchemaUp, user_id: int
    ) -> ListModel:
        await self._check_manage_permission(project_id, user_id)
        new_list = ListModel(name=data.name, order=data.order, project_id=project_id)
        self.db_session.add(new_list)
        await self.db_session.commit()
        await self.db_session.refresh(new_list)
        return new_list

    async def update_list(
        self, project_id: int, list_id: int, data: ListSchemaUp, user_id: int
    ) -> ListModel:
        await self._check_manage_permission(project_id, user_id)
        query = select(ListModel).where(
            ListModel.id == list_id, ListModel.project_id == project_id
        )
        result = await self.db_session.execute(query)
        lst = result.unique().scalar_one_or_none()
        if not lst:
            raise NoResultFound()
        if data.name is not None:
            lst.name = data.name
        if data.order is not None:
            lst.order = data.order
        await self.db_session.commit()
        await self.db_session.refresh(lst)
        return lst

    async def delete_list(self, project_id: int, list_id: int, user_id: int):
        await self._check_delete_permission(project_id, user_id)

        query = (
            select(ListModel)
            .options(selectinload(ListModel.cards))
            .where(ListModel.id == list_id, ListModel.project_id == project_id)
        )
        result = await self.db_session.execute(query)
        lst = result.unique().scalar_one_or_none()
        if not lst:
            raise NoResultFound()

        if lst.cards:
            target_query = (
                select(ListModel)
                .where(
                    ListModel.project_id == project_id,
                    ListModel.id != list_id,
                    ListModel.order < lst.order,
                )
                .order_by(ListModel.order.desc())
                .limit(1)
            )
            target_result = await self.db_session.execute(target_query)
            target_list = target_result.scalar_one_or_none()

            if target_list is None:
                raise HTTPException(
                    status_code=409,
                    detail="Cannot delete this list because there is no list with a lower order to receive its cards.",
                )

            for card in lst.cards:
                card.list_id = target_list.id

            await self.db_session.flush()

        await self.db_session.delete(lst)
        await self.db_session.commit()
