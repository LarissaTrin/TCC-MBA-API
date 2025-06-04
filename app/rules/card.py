from datetime import datetime
from sqlalchemy import delete, select, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import NoResultFound

from app.db.models.approver_model import ApproverModel
from app.db.models.card_model import CardModel
from app.db.models.list_model import ListModel
from app.db.models.tag_card_model import TagCardModel
from app.db.models.task_card_model import TaskCardModel
from app.schemas.card_schema import CardSchemaBase, CardSchemaUp
from app.schemas.list_schema import ListSchemaProject


class CardRules:
    def __init__(self, db_session: AsyncSession):
        self.db_session = db_session

    async def add_card(self, list_id: int, card_data: CardSchemaBase) -> int:
        """
        Adiciona um novo card à lista especificada, atribuindo automaticamente
        o número do card com base na quantidade total de cards do projeto.

        Args:
            list_id (int): ID da lista onde o card será adicionado.
            card_data (CardSchemaBase): Dados do card (sem precisar do card_number).

        Returns:
            int: ID do novo card criado.
        """
        # Verifica se a lista existe e busca o project_id
        list_query = select(ListModel).where(ListModel.id == list_id)
        result = await self.db_session.execute(list_query)
        list_obj: ListSchemaProject | None = result.scalars().unique().one_or_none()

        if not list_obj:
            raise NoResultFound(f"Lista com id={list_id} não encontrada.")

        project_id = list_obj.project_id

        # Conta todos os cards do projeto (todas as listas ligadas ao projeto)
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
            await self.db_session.commit()
            await self.db_session.refresh(new_card)
            return new_card.id
        except Exception as e:
            await self.db_session.rollback()
            raise e

    async def get_card_by_id(self, card_id: int) -> CardModel:
        """
        Busca um card pelo ID com todos os relacionamentos já definidos no modelo.

        Args:
            card_id (int): ID do card a ser buscado.

        Returns:
            CardModel: Card encontrado com os relacionamentos carregados.

        Raises:
            NoResultFound: Se nenhum card com o ID for encontrado.
        """
        card = await self._get_card_or_404(card_id)

        return card

    async def update_card(self, card_id: int, data: CardSchemaUp) -> CardModel:
        """
        Atualiza um card com campos simples e relacionamentos (tags, approvers, tasks).

        Atualiza registros existentes, cria novos e remove os ausentes.

        Args:
            card_id (int): ID do card a ser atualizado.
            data (CardSchemaUp): Dados recebidos para atualização.

        Returns:
            CardModel: Instância atualizada do card.

        Raises:
            NoResultFound: Se o card não existir.
        """
        card = await self._get_card_or_404(card_id)

        # --- Atualizar campos simples ---
        for field in [
            "title",
            "user_id",
            "description",
            "date",
            "priority",
            "planned_hours",
            "completed_hours",
            "story_points",
            "list_id",
        ]:
            if (value := getattr(data, field)) is not None:
                setattr(card, field, value)

        # --- Tags ---
        if data.tag_cards is not None:
            existing_tags = {tag.id: tag for tag in card.tag_cards if tag.id}
            received_ids = set()

            for tag_data in data.tag_cards:
                if tag_data.id and tag_data.id in existing_tags:
                    tag = existing_tags[tag_data.id]
                    tag.tag_id = tag_data.tag_id
                    received_ids.add(tag_data.id)
                else:
                    new_tag = TagCardModel(
                        **tag_data.dict(exclude={"id"}), card_id=card.id
                    )
                    self.db_session.add(new_tag)

            if existing_tags:
                await self.db_session.execute(
                    delete(TagCardModel).where(
                        TagCardModel.card_id == card.id,
                        TagCardModel.id.notin_(received_ids),
                    )
                )

        # --- Approvers ---
        if data.approvers is not None:
            existing_approvers = {a.id: a for a in card.approvers if a.id}
            received_ids = set()

            for approver_data in data.approvers:
                if approver_data.id and approver_data.id in existing_approvers:
                    approver = existing_approvers[approver_data.id]
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
                    task.description = task_data.description
                    task.completed = task_data.completed
                    received_ids.add(task_data.id)
                else:
                    new_task = TaskCardModel(
                        **task_data.dict(exclude={"id"}), card_id=card.id
                    )
                    self.db_session.add(new_task)

            if existing_tasks:
                await self.db_session.execute(
                    delete(TaskCardModel).where(
                        TaskCardModel.card_id == card.id,
                        TaskCardModel.id.notin_(received_ids),
                    )
                )

        await self.db_session.commit()
        await self.db_session.refresh(card)
        return card

    async def delete_card(self, card_id: int) -> None:
        """
        Remove um card e seus relacionamentos (tags, approvers, tasks).

        Args:
            card_id (int): ID do card a ser removido.

        Raises:
            NoResultFound: Se o card não existir.
        """
        card = await self._get_card_or_404(card_id)

        await self.db_session.delete(card)

        await self.db_session.commit()

    async def _get_card_or_404(self, card_id: int) -> CardModel:
        query = select(CardModel).where(CardModel.id == card_id)
        result = await self.db_session.execute(query)
        card = result.scalars().unique().one_or_none()
        if not card:
            raise NoResultFound(f"Card com id={card_id} não encontrado.")
        return card
