from sqlalchemy import Column, Integer, String, ForeignKey, Boolean
from sqlalchemy.orm import relationship

from app.core.configs import settings


class TaskCardModel(settings.DBBaseModel):
    __tablename__ = "tasksCard"

    id = Column("id", Integer, primary_key=True, autoincrement=True)
    title = Column("title", String(255), nullable=True)
    date = Column("date", String(50), nullable=True)
    completed = Column("completed", Boolean, nullable=False, default=False)

    userId = Column("userId", Integer, ForeignKey("users.id"), nullable=True)
    cardId = Column("cardId", Integer, ForeignKey("cards.id"), nullable=False)

    # relationships
    user = relationship("UserModel", lazy="joined")
    card = relationship("CardModel", back_populates="tasks_card", lazy="joined")
