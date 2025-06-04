from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.orm import relationship

from app.core.configs import settings


class ListModel(settings.DBBaseModel):
    __tablename__ = "lists"
    id = Column("id", Integer, primary_key=True, autoincrement=True)
    name = Column("name", String(100))
    order = Column("order", Integer)

    project_id = Column("projectId", Integer, ForeignKey("projects.id"))

    # relationships
    project = relationship("ProjectModel", back_populates="lists", lazy="joined")
    cards = relationship(
        "CardModel",
        back_populates="list",
        cascade="all, delete-orphan",
        uselist=True,
        lazy="joined",
    )
