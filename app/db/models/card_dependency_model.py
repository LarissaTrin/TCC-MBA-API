from sqlalchemy import Column, Integer, ForeignKey, DateTime, UniqueConstraint, func
from sqlalchemy.orm import relationship

from app.core.configs import settings


class CardDependencyModel(settings.DBBaseModel):
    """
    Relacionamento simples entre dois cards (dependência/associação).

    card_id → card que possui a dependência
    related_card_id → card relacionado
    """

    __tablename__ = "card_dependencies"
    __table_args__ = (
        UniqueConstraint("cardId", "relatedCardId", name="uq_card_dependency"),
    )

    id = Column("id", Integer, primary_key=True, autoincrement=True)
    card_id = Column(
        "cardId",
        Integer,
        ForeignKey("cards.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    related_card_id = Column(
        "relatedCardId",
        Integer,
        ForeignKey("cards.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    created_at = Column("createdAt", DateTime, server_default=func.now())

    related_card = relationship(
        "CardModel",
        foreign_keys=[related_card_id],
        lazy="joined",
    )
