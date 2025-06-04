from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, func
from sqlalchemy.orm import relationship

from app.core.configs import settings


class CommentModel(settings.DBBaseModel):
    __tablename__ = "comments"

    id = Column("id", Integer, primary_key=True, autoincrement=True)
    description = Column("description", String(1000), nullable=True)
    created_at = Column("createdAt", DateTime, server_default=func.now())
    updated_at = Column("updatedAt", DateTime, onupdate=func.now())

    user_id = Column("userId", Integer, ForeignKey("users.id"), nullable=False)
    card_id = Column("cardId", Integer, ForeignKey("cards.id"), nullable=False)

    # relationships
    user = relationship("UserModel", lazy="joined")
    card = relationship("CardModel", back_populates="comments", lazy="joined")
