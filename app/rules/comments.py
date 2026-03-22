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
        Adds a comment to a card.

        Args:
            card_id (int): ID of the card to comment on.
            comment_data (CommentCreateSchema): Comment data.
            user_id (int): ID of the comment author.

        Returns:
            CommentModel: The created comment.

        Raises:
            NoResultFound: If the card is not found.
        """
        # Check if the card exists
        result = await self.db_session.execute(
            select(CardModel).where(CardModel.id == card_id)
        )
        card = result.unique().scalar_one_or_none()
        if not card:
            raise NoResultFound(f"Card id={card_id} not found.")

        # Create and persist the comment
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
        Updates a comment's description if the user is the author.

        Args:
            comment_id (int): ID of the comment.
            new_description (str): New comment content.
            user_id (int): ID of the user attempting to edit.

        Returns:
            CommentModel: The updated comment.

        Raises:
            NoResultFound: If the comment does not exist.
            PermissionError: If the user is not the comment author.
        """
        result = await self.db_session.execute(
            select(CommentModel).where(CommentModel.id == comment_id)
        )
        comment = result.unique().scalar_one_or_none()
        if not comment:
            raise NoResultFound(f"Comment id={comment_id} not found.")

        if comment.user_id != user_id:
            raise PermissionError("You do not have permission to edit this comment.")

        comment.description = new_description
        await self.db_session.commit()
        await self.db_session.refresh(comment)
        return comment

    async def delete_comment(self, comment_id: int, user_id: int) -> None:
        """
        Deletes a comment if the user is the author.

        Args:
            comment_id (int): ID of the comment.
            user_id (int): ID of the user attempting to delete.

        Raises:
            NoResultFound: If the comment does not exist.
            PermissionError: If the user is not the comment author.
        """
        result = await self.db_session.execute(
            select(CommentModel).where(CommentModel.id == comment_id)
        )
        comment = result.unique().scalar_one_or_none()
        if not comment:
            raise NoResultFound(f"Comment id={comment_id} not found.")

        if comment.user_id != user_id:
            raise PermissionError(
                "You do not have permission to delete this comment."
            )

        await self.db_session.delete(comment)
        await self.db_session.commit()
