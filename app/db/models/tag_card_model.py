from sqlalchemy import Column, Integer, ForeignKey
from sqlalchemy.orm import relationship

from app.core.configs import settings


class TagCardModel(settings.DBBaseModel):
    __tablename__ = "tagCards"

    id = Column("id", Integer, primary_key=True, autoincrement=True)
    cardId = Column("cardId", Integer, ForeignKey("cards.id"), primary_key=True)
    tagId = Column("tagId", Integer, ForeignKey("tags.id"), primary_key=True)

    # relationships
    card = relationship("CardModel", back_populates="tag_cards", lazy="joined")
    tag = relationship("TagModel")
