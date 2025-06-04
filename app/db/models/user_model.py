from sqlalchemy import Column, Integer, String, Boolean

from app.core.configs import settings


class UserModel(settings.DBBaseModel):
    __tablename__ = "users"

    id = Column("id", Integer, primary_key=True, autoincrement=True)
    firstName = Column("firstName", String(256), nullable=False)
    lastName = Column("lastName", String(256), nullable=True)
    email = Column("email", String(256), index=True, nullable=False, unique=True)
    username = Column("username", String(256), index=True, nullable=False, unique=True)
    password = Column("password", String(256), nullable=False)
    isAdmin = Column("isAdmin", Boolean, default=False)
