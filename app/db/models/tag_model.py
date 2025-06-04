from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.orm import relationship

from app.core.configs import settings


class TagModel(settings.DBBaseModel):
    __tablename__ = "tags"

    id = Column("id", Integer, primary_key=True, autoincrement=True)
    name = Column("name", String(100), nullable=True)
    projectId = Column("projectId", Integer, ForeignKey("projects.id"), nullable=False)

    # Relationship with Project
    project = relationship("ProjectModel", back_populates="tags", lazy="joined")
