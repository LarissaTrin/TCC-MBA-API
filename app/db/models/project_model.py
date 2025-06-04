from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, func
from sqlalchemy.orm import relationship

from app.core.configs import settings


class ProjectModel(settings.DBBaseModel):
    __tablename__ = "projects"

    id = Column("id", Integer, primary_key=True, autoincrement=True)
    title = Column("title", String(100))
    description = Column("description", String(1000))
    created_at = Column("createdAt", DateTime, server_default=func.now())
    updated_at = Column("updatedAt", DateTime, onupdate=func.now())
    creator_id = Column("creatorId", Integer, ForeignKey("users.id"))

    # relationships
    creator = relationship("UserModel", lazy="joined")
    lists = relationship(
        "ListModel",
        back_populates="project",
        cascade="all, delete-orphan",
        uselist=True,
        lazy="joined",
    )
    project_users = relationship(
        "ProjectUserModel",
        back_populates="project",
        cascade="all, delete-orphan",
        uselist=True,
        lazy="joined",
    )
    tags = relationship(
        "TagModel",
        back_populates="project",
        cascade="all, delete-orphan",
        uselist=True,
        lazy="joined",
    )
