from sqlalchemy import Column, String, Integer

from app.core.configs import settings


class RoleModel(settings.DBBaseModel):
    __tablename__ = "roles"

    id = Column("id", Integer, primary_key=True)
    name = Column("name", String(50), unique=True)
