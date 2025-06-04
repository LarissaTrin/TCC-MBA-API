from sqlalchemy import Column, ForeignKey, UniqueConstraint, Integer
from sqlalchemy.orm import relationship

from app.core.configs import settings


class ProjectUserModel(settings.DBBaseModel):
    __tablename__ = "projectUsers"
    id = Column("id", Integer, primary_key=True, autoincrement=True)

    project_id = Column("projectId", Integer, ForeignKey("projects.id"))
    user_id = Column("userId", Integer, ForeignKey("users.id"))
    role_id = Column("roleId", Integer, ForeignKey("roles.id"))

    # relationships
    project = relationship(
        "ProjectModel", back_populates="project_users", lazy="joined"
    )
    user = relationship("UserModel")
    role = relationship("RoleModel")

    __table_args__ = (UniqueConstraint("projectId", "userId", name="uq_project_user"),)
