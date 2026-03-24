from sqlalchemy import Column, Integer, String
from app.core.configs import settings


class CategoryModel(settings.DBBaseModel):
    """Global lookup table for card categories (e.g. Bug, Feature, Issue)."""

    __tablename__ = "categories"

    id = Column("id", Integer, primary_key=True, autoincrement=True)
    name = Column("name", String(100), nullable=False, unique=True)
