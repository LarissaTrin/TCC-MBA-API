from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.exc import NoResultFound

from app.db.models.card_model import CardModel
from app.db.models.comment_model import CommentModel
from app.schemas.comment_schema import CommentCreateSchema


class CommentRules:
    def __init__(self, db_session: AsyncSession):
        self.db_session = db_session

    async def add_comment(
        self, card_id: int, comment_data: CommentCreateSchema, user_id: int
    ) -> CommentModel:
        """
        Adiciona um comentário ao card.

        Args:
            card_id (int): ID do card a ser comentado.
            comment_data (CommentCreateSchema): Dados do comentário.
            user_id (int): ID do usuário autor do comentário.

        Returns:
            CommentModel: Comentário criado.

        Raises:
            NoResultFound: Se o card não for encontrado.
        """
        # Verifica se o card existe
        result = await self.db_session.execute(
            select(CardModel).where(CardModel.id == card_id)
        )
        card = result.scalar_one_or_none()
        if not card:
            raise NoResultFound(f"Card com id={card_id} não encontrado.")

        # Cria e persiste o comentário
        comment = CommentModel(
            description=comment_data.description,
            user_id=user_id,
            card_id=card_id,
        )

        self.db_session.add(comment)
        await self.db_session.commit()
        await self.db_session.refresh(comment)
        return comment

    async def update_comment(
        self, comment_id: int, new_description: str, user_id: int
    ) -> CommentModel:
        """
        Atualiza a descrição de um comentário se o usuário for o autor.

        Args:
            comment_id (int): ID do comentário.
            new_description (str): Novo conteúdo do comentário.
            user_id (int): ID do usuário que está tentando editar.

        Returns:
            CommentModel: Comentário atualizado.

        Raises:
            NoResultFound: Se o comentário não existir.
            PermissionError: Se o usuário não for o autor do comentário.
        """
        result = await self.db_session.execute(
            select(CommentModel).where(CommentModel.id == comment_id)
        )
        comment = result.scalar_one_or_none()
        if not comment:
            raise NoResultFound(f"Comentário com id={comment_id} não encontrado.")

        if comment.user_id != user_id:
            raise PermissionError("Você não tem permissão para editar este comentário.")

        comment.description = new_description
        await self.db_session.commit()
        await self.db_session.refresh(comment)
        return comment

    async def delete_comment(self, comment_id: int, user_id: int) -> None:
        """
        Remove um comentário se o usuário for o autor.

        Args:
            comment_id (int): ID do comentário.
            user_id (int): ID do usuário que está tentando deletar.

        Raises:
            NoResultFound: Se o comentário não existir.
            PermissionError: Se o usuário não for o autor do comentário.
        """
        result = await self.db_session.execute(
            select(CommentModel).where(CommentModel.id == comment_id)
        )
        comment = result.scalar_one_or_none()
        if not comment:
            raise NoResultFound(f"Comentário com id={comment_id} não encontrado.")

        if comment.user_id != user_id:
            raise PermissionError(
                "Você não tem permissão para excluir este comentário."
            )

        await self.db_session.delete(comment)
        await self.db_session.commit()
