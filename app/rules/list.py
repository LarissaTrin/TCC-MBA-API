from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload
from sqlalchemy.exc import NoResultFound

from app.db.models.list_model import ListModel
from app.db.models.project_user_model import ProjectUserModel
from app.schemas.list_schema import ListSchemaUp


class ListRules:
    def __init__(self, db_session: AsyncSession):
        self.db_session = db_session

    async def _check_permission(self, project_id: int, user_id: int):
        """
        Checa se o usuário tem permissão para editar listas do projeto.
        Apenas role_id 1 ou 2 podem.
        """
        query = select(ProjectUserModel).where(
            ProjectUserModel.project_id == project_id,
            ProjectUserModel.user_id == user_id,
            ProjectUserModel.role_id.in_([1, 2]),
        )
        result = await self.db_session.execute(query)
        # Corrigido:
        user_project = (
            result.unique().scalar_one_or_none()
        )  # <- unique() resolve o problema
        if not user_project:
            raise HTTPException(status_code=403, detail="Usuário não autorizado")

    async def get_lists_for_project(self, project_id: int) -> list[ListModel]:
        query = (
            select(ListModel)
            .options(selectinload(ListModel.cards))  # Carrega cards junto se quiser
            .where(ListModel.project_id == project_id)
        )
        result = await self.db_session.execute(query)
        return result.unique().scalars().all()

    async def add_list(
        self, project_id: int, data: ListSchemaUp, user_id: int
    ) -> ListModel:
        await self._check_permission(project_id, user_id)
        new_list = ListModel(name=data.name, order=data.order, project_id=project_id)
        self.db_session.add(new_list)
        await self.db_session.commit()
        await self.db_session.refresh(new_list)
        return new_list

    async def update_list(
        self, project_id: int, list_id: int, data: ListSchemaUp, user_id: int
    ) -> ListModel:
        await self._check_permission(project_id, user_id)
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
        await self._check_permission(project_id, user_id)
        query = select(ListModel).where(
            ListModel.id == list_id, ListModel.project_id == project_id
        )
        result = await self.db_session.execute(query)
        lst = result.unique().scalar_one_or_none()
        if not lst:
            raise NoResultFound()
        await self.db_session.delete(lst)
        await self.db_session.commit()
