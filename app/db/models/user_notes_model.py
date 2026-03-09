from sqlalchemy import Column, Integer, Text, ForeignKey

from app.core.configs import settings


class UserNotesModel(settings.DBBaseModel):
    __tablename__ = "user_notes"

    id = Column("id", Integer, primary_key=True, autoincrement=True)
    user_id = Column("user_id", Integer, ForeignKey("users.id"), nullable=False, unique=True)
    content = Column("content", Text, nullable=True, default="")
