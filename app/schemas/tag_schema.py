from typing import Optional

from app.schemas.base import CustomBaseModel


class TagSchemaBase(CustomBaseModel):
    id: Optional[int] = None
    name: Optional[str] = None


class TagSchema(CustomBaseModel):
    id: int
    name: str
