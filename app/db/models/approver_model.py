from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.orm import relationship

from app.core.configs import settings


class ApproverModel(settings.DBBaseModel):
    __tablename__ = "approvers"

    id = Column("id", Integer, primary_key=True, autoincrement=True)
    environment = Column("environment", String(100), nullable=True)
    user_id = Column("userId", Integer, ForeignKey("users.id"), nullable=True)
    card_id = Column("cardId", Integer, ForeignKey("cards.id"), nullable=False)

    # relationships
    user = relationship("UserModel", lazy="joined")
    card = relationship("CardModel", back_populates="approvers", lazy="joined")
