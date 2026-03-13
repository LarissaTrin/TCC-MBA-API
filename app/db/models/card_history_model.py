from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, func
from sqlalchemy.orm import relationship

from app.core.configs import settings


class CardHistoryModel(settings.DBBaseModel):
    """
    Audit log for card changes.

    Each row records a single state transition:
      action     – what changed  (e.g. "moved", "assigned", "due_date_changed")
      old_value  – previous value as string (e.g. list name or user name)
      new_value  – new value as string
      user_id    – who made the change
      created_at – when it happened
    """

    __tablename__ = "card_history"

    id = Column("id", Integer, primary_key=True, autoincrement=True)
    card_id = Column(
        "cardId",
        Integer,
        ForeignKey("cards.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    user_id = Column("userId", Integer, ForeignKey("users.id"), nullable=True)
    action = Column("action", String(50), nullable=False)
    old_value = Column("oldValue", String(255), nullable=True)
    new_value = Column("newValue", String(255), nullable=True)
    created_at = Column("createdAt", DateTime, server_default=func.now())

    # relationships
    card = relationship("CardModel", back_populates="history")
    user = relationship("UserModel", lazy="joined")
