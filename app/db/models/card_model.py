from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, func
from sqlalchemy.orm import relationship

from app.core.configs import settings


class CardModel(settings.DBBaseModel):
    __tablename__ = "cards"

    id = Column("id", Integer, primary_key=True, autoincrement=True)
    card_number = Column("cardNumber", Integer, nullable=False)
    title = Column("title", String(255), nullable=False)
    created_at = Column("createdAt", DateTime, server_default=func.now())
    updated_at = Column("updatedAt", DateTime, onupdate=func.now())

    list_id = Column("listId", Integer, ForeignKey("lists.id"), nullable=False)
    user_id = Column("userId", Integer, ForeignKey("users.id"), nullable=True)

    date = Column("date", DateTime, nullable=True)
    priority = Column("priority", Integer, nullable=True)
    description = Column("description", String(1000), nullable=True)
    planned_hours = Column("plannedHours", Integer, nullable=True)
    completed_hours = Column("completedHours", Integer, nullable=True)
    story_points = Column("storyPoints", Integer, nullable=True)

    # relationships
    user = relationship("UserModel", lazy="joined")
    list = relationship("ListModel", back_populates="cards")

    tag_cards = relationship(
        "TagCardModel",
        back_populates="card",
        cascade="all, delete-orphan",
        uselist=True,
        lazy="joined",
    )
    comments = relationship(
        "CommentModel",
        back_populates="card",
        cascade="all, delete-orphan",
        uselist=True,
        lazy="joined",
    )
    approvers = relationship(
        "ApproverModel",
        back_populates="card",
        cascade="all, delete-orphan",
        uselist=True,
        lazy="joined",
    )
    tasks_card = relationship(
        "TaskCardModel",
        back_populates="card",
        cascade="all, delete-orphan",
        uselist=True,
        lazy="joined",
    )
